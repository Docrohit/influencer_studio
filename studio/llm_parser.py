import openai
import json

def parse_influencer_intent(user_input, has_photo=False, has_video=False, openai_api_key=None):
    """
    Uses OpenAI (GPT-4o or similar) to classify the user's natural language message into one of 7 intents.
    Returns the intent type, and extracted parameters (like target demographic, style, etc.)
    """
    if not openai_api_key:
        raise ValueError("Missing OpenAI API key for this account.")

    client = openai.Client(api_key=openai_api_key)

    system_prompt = """
    You are an intent router for an AI Influencer Studio Telegram Bot.
    The user is interacting with their AI influencer using natural language.

    Analyze their message and determine which of the 7 intents they are requesting:
    1. MAKE_INFLUENCER: Create a new character from scratch using a text description (NO image provided by user).
    2. ADD_INFLUENCER: Save an image they just uploaded as a new character (e.g., "save her as Maaya", image IS provided).
    3. TWEAK_INFLUENCER: Alter the base traits of their current character (e.g., "make her blonde", "make her look older").
    4. GENERATE_SCENE: Place their existing character in a new environment, pose, or situation without a reference image (e.g., "put her in a cafe", "make her sit on a couch").
    5. TURN_TO_VIDEO: Animate an image. If they provide a video, they want Motion Control. If they don't, they want standard Image2Video.
    6. REFERENCE_APPLY: Force the character into an exact style/pose/setting based on an image they just provided (e.g., "make her wear this", "put her in this room").
    7. EDIT_IMAGE: Modify a specific part of a generated image (e.g., "change the cup to a glass").

    Return a strictly formatted JSON object:
    {
        "intent": "MAKE_INFLUENCER" | "ADD_INFLUENCER" | "TWEAK_INFLUENCER" | "GENERATE_SCENE" | "TURN_TO_VIDEO" | "REFERENCE_APPLY" | "EDIT_IMAGE",
        "enhanced_prompt": "A highly detailed, photographic prompt based on the user's request, focusing on realism and high fashion.",
        "influencer_name": "Extracted name if provided (e.g., 'Maaya')",
        "extracted_traits": {"hair": "...", "age": "...", "vibe": "..."}, // Useful for MAKE, ADD, or TWEAK
        "target_demographic": "e.g., Asian, European, Gen-Z", // If applicable
        "narration_text": "Exact text the user wants narrated in the background of the video (if they ask for a voiceover/narration)"
    }
    """

    user_context = f"User Input: '{user_input}'\nProvided Photo: {has_photo}\nProvided Video: {has_video}"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_context}
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)
