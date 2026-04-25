import base64
import requests

KLING_API_BASE = "https://api-singapore.klingai.com/v1/videos"

def get_kling_headers(api_token=None):
    if not api_token:
        raise ValueError("Missing Kling API token for this account.")
    return {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def generate_image2video(image_path_or_url, prompt, duration="5", mode="pro", api_token=None):
    """
    Kling Image to Video generation (Intent 4a)
    """
    url = f"{KLING_API_BASE}/image2video"
    
    payload = {
        "model_name": "kling-v3",
        "prompt": prompt,
        "duration": str(duration),
        "mode": mode,
        "sound": "off"
    }

    if image_path_or_url.startswith("http"):
        payload["image"] = image_path_or_url
    else:
        payload["image"] = encode_image_to_base64(image_path_or_url)

    response = requests.post(url, headers=get_kling_headers(api_token=api_token), json=payload)
    response.raise_for_status()
    return response.json()

def generate_motion_control(image_path_or_url, video_url, prompt="", api_token=None):
    """
    Kling Motion Control generation (Intent 4b)
    """
    url = f"{KLING_API_BASE}/motion-control"
    
    payload = {
        "model_name": "kling-v3",
        "video_url": video_url,
        "character_orientation": "video",
        "mode": "pro",
        "prompt": prompt
    }

    if image_path_or_url.startswith("http"):
        payload["image_url"] = image_path_or_url
    else:
        payload["image_url"] = encode_image_to_base64(image_path_or_url)

    response = requests.post(url, headers=get_kling_headers(api_token=api_token), json=payload)
    response.raise_for_status()
    return response.json()

def check_task_status(task_id, task_type="image2video", api_token=None):
    """
    Polls the task status for either image2video or motion-control
    """
    url = f"{KLING_API_BASE}/{task_type}/{task_id}"
    response = requests.get(url, headers=get_kling_headers(api_token=api_token))
    response.raise_for_status()
    return response.json()
