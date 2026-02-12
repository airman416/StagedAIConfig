
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

try:
    print("ImageConfig fields:", types.ImageConfig.__annotations__)
except AttributeError:
    print("Could not find annotations, trying dir()")
    print(dir(types.ImageConfig))

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Try to find the parameter for generating multiple images
try:
    # Attempt with 'count' which is a common guess or 'number_of_images'
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
             aspect_ratio="1:1"
        ),
        candidate_count=2 # Try candidate_count at the top level first
    )
    print("Config created successfully with candidate_count")
except Exception as e:
    print(f"Error with candidate_count: {e}")

try:
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
             aspect_ratio="1:1",
             count=2 # Try count inside ImageConfig
        )
    )
    print("Config created successfully with ImageConfig.count")
except Exception as e:
    print(f"Error with ImageConfig.count: {e}")

