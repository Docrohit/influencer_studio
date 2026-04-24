import os
import sys
import time
import requests
from dotenv import load_dotenv

# Add the studio path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from studio.gemini_service import create_scene_with_character
from studio.kling_service import generate_motion_control, check_task_status

# Load environment variables
load_dotenv()

# --- Configurations ---
# Please save the uploaded image of Maaya to this path, or update the path below:
MAAYA_BASE_IMAGE = "/Users/rohitsharma/Desktop/maaya_base.jpg"
MAAYA_REF_VIDEO = "/Users/rohitsharma/Desktop/kling_20260424_Motion_Control_Make_the_i_2948_0.mp4"

def make_maaya_scene():
    print(f"🎨 Generating new scene for Maaya using Gemini 3.1 Flash Image Preview...")
    if not os.path.exists(MAAYA_BASE_IMAGE):
        print(f"❌ Error: Could not find Maaya's base image at {MAAYA_BASE_IMAGE}")
        print("Please save the image you uploaded to that path, or update the script.")
        return

    prompt = (
        "A cinematic, high-fashion editorial shot of this exact woman. "
        "She is sitting at a sleek, modern cafe in Paris, sipping an espresso. "
        "She is wearing a stylish red trench coat. Soft golden hour lighting, 85mm lens, photorealistic."
    )
    
    try:
        images = create_scene_with_character([MAAYA_BASE_IMAGE], prompt, aspect_ratio="9:16")
        for i, img in enumerate(images):
            output_path = f"maaya_paris_scene_{i}.png"
            img.save(output_path)
            print(f"✅ Scene generated and saved to {output_path}")
    except Exception as e:
        print(f"❌ Gemini Generation Failed: {e}")

def make_maaya_motion_video():
    print(f"🎬 Generating Motion Control Video for Maaya using Kling V3...")
    if not os.path.exists(MAAYA_BASE_IMAGE):
        print(f"❌ Error: Could not find Maaya's base image at {MAAYA_BASE_IMAGE}")
        return
    if not os.path.exists(MAAYA_REF_VIDEO):
        print(f"❌ Error: Could not find reference video at {MAAYA_REF_VIDEO}")
        # Note: Kling requires a URL for the video, so if it's local, we would normally need to upload it first 
        # or use a publicly accessible URL. For this script, we assume the user has a way to pass the video URL 
        # or we implement an upload mechanism.
        # Since Kling API accepts video_url, we will mock this or ask you to provide a hosted URL.
        print("⚠️ Note: Kling API requires a publicly accessible video_url. If this is a local file, it needs to be uploaded first.")
        
    # Assuming we have a hosted URL for the video for now:
    # In production, we'd upload local files to a bucket (S3/Cloudinary) first and pass that URL.
    hosted_video_url = "https://p2-kling.klingai.com/kcdn/cdn-kcdn112452/kling-qa-test/dance.mp4" # Placeholder
    
    try:
        response = generate_motion_control(
            image_path_or_url=MAAYA_BASE_IMAGE,
            video_url=hosted_video_url, # We must pass a URL here per the docs
            prompt="The woman is doing the exact motions from the video."
        )
        task_id = response['data']['task_id']
        print(f"⏳ Task submitted successfully. Task ID: {task_id}")
        
        # Poll for completion
        while True:
            time.sleep(10)
            status_res = check_task_status(task_id, task_type="motion-control")
            status = status_res['data']['task_status']
            print(f"Task status: {status}...")
            
            if status == "succeed":
                video_url = status_res['data']['task_result']['videos'][0]['url']
                print(f"✅ Video Generation Complete! Download URL: {video_url}")
                break
            elif status == "failed":
                print(f"❌ Task failed: {status_res['data'].get('task_status_msg')}")
                break
                
    except Exception as e:
        print(f"❌ Kling Generation Failed: {e}")

if __name__ == "__main__":
    print("🌟 Starting Maaya AI Production 🌟")
    print("1. Testing Image Scene Generation")
    # make_maaya_scene() 
    print("\n2. Testing Motion Control Video Generation")
    # make_maaya_motion_video()
    print("\nScript is ready! Uncomment the functions and provide API keys in .env to run.")
