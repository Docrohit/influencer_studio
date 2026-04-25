from celery import shared_task
import os
import requests
from django.utils import timezone
from .models import Account, Influencer, MediaAsset
from .llm_parser import parse_influencer_intent
from .gemini_service import create_scene_with_character, apply_reference_style
from .kling_service import generate_image2video, generate_motion_control


def _missing_key_message(provider_label):
    return (
        f"⚠️ Missing {provider_label} key on your account. "
        "Log in at influencerai.nftforger.com and add your API keys on the login form, then try again."
    )


def _subscription_required_message():
    return (
        "⚠️ Your subscription is not active. Renew in billing: "
        "https://influencerai.nftforger.com/billing/"
    )


def _sync_expired_status(account):
    if account.status == 'approved' and (
        account.subscription_paid_until is None or account.subscription_paid_until <= timezone.now()
    ):
        account.status = 'expired'
        account.save(update_fields=['status'])


def _resolve_provider_key(account, account_field, env_fallback_name):
    _sync_expired_status(account)

    if account.status != 'approved' or not account.is_subscription_active():
        return None, _subscription_required_message()

    if account.key_mode == 'platform_keys':
        value = os.environ.get(env_fallback_name)
        if not value and env_fallback_name == 'GEMINI_API_KEY':
            value = os.environ.get('NANO_BANANA_API_KEY')
        if not value and env_fallback_name == 'KLING_API_TOKEN':
            kling_access = os.environ.get('KLING_ACCESS_KEY')
            kling_secret = os.environ.get('KLING_SECRET_KEY')
            if kling_access and kling_secret:
                value = f"{kling_access}:{kling_secret}"
        if not value:
            return None, f"⚠️ Platform provider key missing on server for {env_fallback_name}."
        return value, None

    value = getattr(account, account_field)
    if not value:
        label_map = {
            'openai_api_key': 'OpenAI API',
            'gemini_api_key': 'Gemini API',
            'kling_api_token': 'Kling API',
            'elevenlabs_api_key': 'ElevenLabs API',
        }
        readable = label_map.get(account_field, account_field)
        return None, _missing_key_message(readable)
    return value, None

def get_telegram_file_url(file_id):
    """Fetches the actual download URL for a Telegram file ID."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    file_info_url = f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}"
    res = requests.get(file_info_url).json()
    if res['ok']:
        file_path = res['result']['file_path']
        return f"https://api.telegram.org/file/bot{token}/{file_path}"
    return None

def send_telegram_message(chat_id, text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def send_telegram_video(chat_id, video_path_or_url, caption=""):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/sendVideo"
    if video_path_or_url.startswith("http"):
        requests.post(url, data={"chat_id": chat_id, "video": video_path_or_url, "caption": caption})
    else:
        with open(video_path_or_url, 'rb') as video:
            requests.post(url, data={"chat_id": chat_id, "caption": caption}, files={"video": video})

@shared_task
def apply_voiceover_and_send(asset_id, video_url):
    """
    Called after Kling finishes generating the video if narration_text was requested.
    Merges ElevenLabs audio and sends to Telegram.
    """
    import subprocess
    import urllib.request
    from .voice_service import generate_voiceover
    
    asset = MediaAsset.objects.get(id=asset_id)
    account = asset.influencer.account
    chat_id = asset.influencer.account.telegram_chat_id

    send_telegram_message(chat_id, "🎙️ Video ready! Applying ElevenLabs Voiceover...")
    
    temp_dir = "/tmp"
    raw_vid = os.path.join(temp_dir, f"raw_{asset_id}.mp4")
    audio = os.path.join(temp_dir, f"audio_{asset_id}.mp3")
    final_vid = os.path.join(temp_dir, f"final_{asset_id}.mp4")
    
    try:
        # Download video
        urllib.request.urlretrieve(video_url, raw_vid)
        
        # Generate Audio
        elevenlabs_key, key_error = _resolve_provider_key(account, 'elevenlabs_api_key', 'ELEVENLABS_API_KEY')
        if key_error:
            send_telegram_message(chat_id, key_error)
            send_telegram_message(chat_id, f"Here is the silent video instead: {video_url}")
            return

        generate_voiceover(asset.narration_text, audio, api_key=elevenlabs_key)
        
        # Merge via FFmpeg
        cmd = [
            "ffmpeg", "-y", "-i", raw_vid, "-i", audio,
            "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
            "-shortest", final_vid
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        send_telegram_video(chat_id, final_vid, caption="🎬 Here is your narrated video!")
        
    except Exception as e:
        send_telegram_message(chat_id, f"❌ Failed to apply voiceover: {e}")
        send_telegram_message(chat_id, f"Here is the silent video instead: {video_url}")
        
    finally:
        for file in [raw_vid, audio, final_vid]:
            if os.path.exists(file):
                os.remove(file)

@shared_task
def process_telegram_intent(chat_id, account_id, user_input, file_id=None, media_type=None):
    """
    Async task that parses the intent via LLM, downloads media if needed,
    and calls Gemini or Kling to fulfill the user's request.
    """
    account = Account.objects.get(id=account_id)

    _sync_expired_status(account)
    if account.status != 'approved' or not account.is_subscription_active():
        send_telegram_message(chat_id, _subscription_required_message())
        return
    
    # Notify user we are thinking
    send_telegram_message(chat_id, "🧠 Analyzing your request...")

    has_photo = media_type == 'photo'
    has_video = media_type == 'video'

    # Get media URL if provided
    media_url = None
    if file_id:
        media_url = get_telegram_file_url(file_id)

    openai_key, key_error = _resolve_provider_key(account, 'openai_api_key', 'OPENAI_API_KEY')
    if key_error:
        send_telegram_message(chat_id, key_error)
        return

    try:
        parsed_intent = parse_influencer_intent(
            user_input,
            has_photo,
            has_video,
            openai_api_key=openai_key,
        )
    except Exception as e:
        send_telegram_message(chat_id, f"❌ Failed to parse your request: {e}")
        return
    intent = parsed_intent.get('intent')
    enhanced_prompt = parsed_intent.get('enhanced_prompt', user_input)
    influencer_name = parsed_intent.get('influencer_name') or f"Influencer_{account.telegram_username}"
    narration_text = parsed_intent.get('narration_text')

    # Route Intent
    if intent == 'ADD_INFLUENCER':
        if not has_photo:
            send_telegram_message(chat_id, "⚠️ Please upload an image of the person to save them as your influencer.")
            return
        
        # Save new influencer from uploaded photo
        influencer = Influencer.objects.create(
            account=account,
            name=influencer_name,
            base_image_url_1=media_url,
            traits=parsed_intent.get('extracted_traits', {})
        )
        send_telegram_message(chat_id, f"✅ Influencer '{influencer_name}' saved! You can now generate scenes, videos, or tweak her style.")

    elif intent == 'MAKE_INFLUENCER':
        send_telegram_message(chat_id, f"✨ Creating a brand new influencer from scratch based on your description...")
        
        # Here we would call GPT-Image-2 or Gemini to generate a base image from scratch
        # Try a quick prompt to generate the initial character sheet
        try:
            # Pseudo-code for text-to-image to create base character
            # client = openai.Client()
            # response = client.images.generate(model="gpt-image-2", prompt=enhanced_prompt...)
            # new_image_url = response.data[0].url
            
            # Mocking the creation
            mock_url = "https://example.com/new_character.jpg" 
            
            influencer = Influencer.objects.create(
                account=account,
                name=influencer_name,
                base_image_url_1=mock_url,
                traits=parsed_intent.get('extracted_traits', {})
            )
            send_telegram_message(chat_id, f"✅ New influencer '{influencer_name}' created from your imagination!")
        except Exception as e:
            send_telegram_message(chat_id, f"❌ Failed to create influencer: {e}")

    elif intent == 'GENERATE_SCENE':
        # Get active influencer
        influencer = account.influencers.filter(is_active=True).first()
        if not influencer:
            send_telegram_message(chat_id, "⚠️ You need to create an influencer first by uploading a photo.")
            return
            
        send_telegram_message(chat_id, "🎨 Generating scene using Gemini Nano Banana (preserving character traits)...")
        
        # Call Gemini (Assuming we download the URL locally first in prod, but logic holds)
        # We pass the enhanced prompt which includes demographic targeting etc.
        # NOTE: For this pseudo-code to run, gemini_service needs local paths. We'll assume we saved it.
        try:
            # Fake save path for architecture demonstration
            local_path = "/tmp/base_image.jpg" 
            gemini_key, key_error = _resolve_provider_key(account, 'gemini_api_key', 'GEMINI_API_KEY')
            if key_error:
                send_telegram_message(chat_id, key_error)
                return

            images = create_scene_with_character([local_path], enhanced_prompt, api_key=gemini_key)
            if images:
                output_path = f"/tmp/generated_{account_id}.png"
                images[0].save(output_path)
                send_telegram_photo(chat_id, output_path, caption="Here is your new scene!")
        except Exception as e:
            send_telegram_message(chat_id, f"❌ Failed to generate scene: {e}")

    elif intent == 'REFERENCE_APPLY':
        influencer = account.influencers.filter(is_active=True).first()
        if not has_photo:
            send_telegram_message(chat_id, "⚠️ You must attach a reference photo (clothes, pose, etc.) for this command.")
            return
        gemini_key, key_error = _resolve_provider_key(account, 'gemini_api_key', 'GEMINI_API_KEY')
        if key_error:
            send_telegram_message(chat_id, key_error)
            return
            
        send_telegram_message(chat_id, "👗 Applying reference style to your influencer...")
        # Implementation calls apply_reference_style() in gemini_service

    elif intent == 'TURN_TO_VIDEO':
        influencer = account.influencers.filter(is_active=True).first()
        kling_key, key_error = _resolve_provider_key(account, 'kling_api_token', 'KLING_API_TOKEN')
        if key_error:
            send_telegram_message(chat_id, key_error)
            return

        if narration_text:
            elevenlabs_key, key_error = _resolve_provider_key(account, 'elevenlabs_api_key', 'ELEVENLABS_API_KEY')
            if key_error:
                send_telegram_message(chat_id, key_error)
                return

        if not influencer:
            send_telegram_message(chat_id, "⚠️ You need to create an influencer first by uploading a photo.")
            return
        
        # Save intent as a MediaAsset to track status and narration
        asset = MediaAsset.objects.create(
            influencer=influencer,
            intent_type='video',
            user_prompt=user_input,
            llm_enhanced_prompt=enhanced_prompt,
            media_type='video',
            narration_text=narration_text,
            status='processing'
        )
        
        if narration_text:
            send_telegram_message(chat_id, "🎬 Starting Video Generation (with your requested voiceover narration)...")
        else:
            send_telegram_message(chat_id, "🎬 Starting Video Generation...")
            
        # Implementation would call Kling API here and save the task_id to the asset
        # asset.provider_task_id = response['data']['task_id']
        # asset.save()

    elif intent == 'TWEAK_INFLUENCER':
        send_telegram_message(chat_id, "🧬 Tweaking influencer DNA (updating base traits)...")
        # Updates JSON traits on the Influencer model and regenerates base image

    else:
        send_telegram_message(chat_id, "🤖 I'm not sure how to handle that request yet.")
