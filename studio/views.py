import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Account
from .tasks import process_telegram_intent

@csrf_exempt
def telegram_webhook(request, custom_chat_id=None):
    """
    Main entry point for all Telegram bot interactions.
    Handles approvals, image uploads, and routing to the LLM intent parser.
    Supports a dynamic URL for multi-tenant BYO-Bot webhook registrations.
    """
    if request.method == 'POST':
        try:
            update = json.loads(request.body.decode('utf-8'))
            message = update.get('message', {})
            chat = message.get('chat', {})
            chat_id = str(chat.get('id'))
            username = chat.get('username', '')
            text = message.get('text', '')
            
            if not chat_id:
                return JsonResponse({'status': 'ok'})

            # 1. Get or Create Account
            account, created = Account.objects.get_or_create(
                telegram_chat_id=chat_id,
                defaults={'telegram_username': username, 'status': 'pending'}
            )
            
            # The token to reply with is their own custom bot token if they have one
            reply_token = account.bot_token if account.bot_token else None

            # 2. Check Approval Status
            if account.status == 'pending':
                send_telegram_message(chat_id, "⏳ Your account is pending approval from the admin.", custom_bot_token=reply_token)
                trigger_admin_approval_request(account)
                return JsonResponse({'status': 'ok'})
            elif account.status == 'rejected':
                send_telegram_message(chat_id, "❌ Your access request was denied.", custom_bot_token=reply_token)
                return JsonResponse({'status': 'ok'})

            # 3. Handle Media (Photos/Videos) vs Text
            photo_data = message.get('photo')
            video_data = message.get('video')
            caption = message.get('caption', '')
            
            user_input = text if text else caption
            
            # Extract file IDs if media is present
            file_id = None
            media_type = None
            if photo_data:
                file_id = photo_data[-1]['file_id'] # Get highest res photo
                media_type = 'photo'
            elif video_data:
                file_id = video_data['file_id']
                media_type = 'video'

            # 4. Offload to Celery (Telegram expects 200 OK within seconds, image gen takes 10s-30s)
            process_telegram_intent.delay(
                chat_id=chat_id,
                account_id=str(account.id),
                user_input=user_input,
                file_id=file_id,
                media_type=media_type
            )

            return JsonResponse({'status': 'ok'})
        except Exception as e:
            print(f"Webhook Error: {e}")
            return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'status': 'invalid method'}, status=405)

@csrf_exempt
def kling_callback(request):
    """
    Webhook endpoint to catch Kling API video generation completion.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            task_id = data.get('data', {}).get('task_id')
            status = data.get('data', {}).get('task_status')
            
            from .models import MediaAsset
            asset = MediaAsset.objects.filter(provider_task_id=task_id).first()
            if not asset:
                return JsonResponse({'status': 'ok'}) # Task not found
                
            if status == 'succeed':
                video_url = data['data']['task_result']['videos'][0]['url']
                asset.output_url = video_url
                asset.status = 'success'
                asset.save()
                
                if asset.narration_text:
                    # Offload the ffmpeg merge to a new task
                    from .tasks import apply_voiceover_and_send
                    apply_voiceover_and_send.delay(asset.id, video_url)
                else:
                    # Notify User immediately
                    send_telegram_message(asset.influencer.account.telegram_chat_id, f"🎬 Your video generation is complete! Watch it here or view it in your dashboard: {video_url}")
            elif status == 'failed':
                asset.status = 'failed'
                asset.save()
                send_telegram_message(asset.influencer.account.telegram_chat_id, "❌ Your video generation failed.")

            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'status': 'invalid method'}, status=405)

@csrf_exempt
def admin_approve_account(request):
    """
    Endpoint for n8n to call when the Admin clicks "Approve" or "Reject" on Telegram.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            chat_id = data.get('chat_id')
            action = data.get('action') # 'approve' or 'reject'
            
            from .models import Account
            account = Account.objects.get(telegram_chat_id=chat_id)
            
            if action == 'approve':
                account.status = 'approved'
                account.save()
                
                # If they provided a custom bot token, we need to register the webhook for that specific bot
                if account.bot_token:
                    webhook_url = f"https://influencerai.nftforger.com/api/telegram/webhook/{account.telegram_chat_id}/"
                    requests.get(f"https://api.telegram.org/bot{account.bot_token}/setWebhook?url={webhook_url}")
                    
                send_telegram_message(chat_id, "🎉 Your account has been approved! You can now use your Influencer Studio bot.", custom_bot_token=account.bot_token)
            elif action == 'reject':
                account.status = 'rejected'
                account.save()
                send_telegram_message(chat_id, "❌ Your account access request has been declined.", custom_bot_token=account.bot_token)
                
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'status': 'invalid method'}, status=405)

# --- Helper Functions (To be moved to a services.py later) ---

import os
import requests

def send_telegram_message(chat_id, text, custom_bot_token=None):
    token = custom_bot_token if custom_bot_token else os.environ.get("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def trigger_admin_approval_request(account):
    """
    Sends a ping to the central Approvals Bot to accept/reject this new user.
    """
    # Assuming standard integration where we notify your admin chat
    admin_chat_id = os.environ.get("APPROVAL_CHAT_ID")
    token = os.environ.get("APPROVAL_BOT_TOKEN")
    if admin_chat_id and token:
        msg = f"🔔 *New Influencer Studio Request*\nUser: @{account.telegram_username}\nChat ID: `{account.telegram_chat_id}`\nAction required: /approve_{account.telegram_chat_id}"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": admin_chat_id, "text": msg, "parse_mode": "Markdown"})
