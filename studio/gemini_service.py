import os
from google import genai
from google.genai import types
from PIL import Image

def get_gemini_client():
    return genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def create_scene_with_character(base_image_paths, prompt, aspect_ratio="9:16"):
    """
    Uses Gemini Nano Banana 2 (3.1 Flash Image Preview) to place the influencer in a new scene.
    Passes up to 4 base images to maintain strict character consistency.
    """
    client = get_gemini_client()
    
    # Load all base images of the character (e.g., Maaya)
    contents = [prompt]
    for path in base_image_paths[:4]: # Max 4 characters/reference images supported
        contents.append(Image.open(path))

    response = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=['IMAGE'],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size="2K"
            ),
        )
    )
    
    # Return the generated images (PIL Image objects)
    generated_images = []
    for part in response.parts:
        if part.inline_data is not None:
            generated_images.append(part.as_image())
            
    return generated_images

def apply_reference_style(base_image_path, reference_image_path, prompt, aspect_ratio="9:16"):
    """
    Takes the influencer base image, and a reference image (e.g. clothing, pose, room),
    and forces the influencer into that setup.
    """
    client = get_gemini_client()
    contents = [
        prompt, 
        Image.open(base_image_path), 
        Image.open(reference_image_path)
    ]
    
    response = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=['IMAGE'],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size="2K"
            ),
        )
    )
    
    for part in response.parts:
        if part.inline_data is not None:
            return part.as_image()
    return None
