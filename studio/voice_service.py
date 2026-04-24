import os
import requests

def generate_voiceover(text, output_path):
    """Generates TTS using ElevenLabs and saves to output_path"""
    api_key = os.environ.get("ELEVENLABS_API_KEY", "sk_d3bd0076eaaec57aa2951f13b6b0fbc53c52802d20d58e6d")
    voice_id = "21m00Tcm4TlvDq8ikWAM" # Rachel (default pleasant voice)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
    }
    
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    return output_path
