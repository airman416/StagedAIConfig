
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def test_batch_styles():
    # Use a dummy image or one from the repo if available.
    # I'll try to use one from the repo if I can find one, or just a text prompt if image is not strictly required for the test (but flash-image needs image input usually for reimagine).
    # I'll check if there is an image in the current dir.
    image_path = "2026-01-17_20-52-31/original.png"
    if not os.path.exists(image_path):
        print(f"Image {image_path} not found.")
        return

    image = Image.open(image_path)
    
    styles = ["Cyberpunk", "Cottagecore"]
    prompt = f"""
    Reimagine this room in distinct styles.
    Generate {len(styles)} images.
    
    Image 1: {styles[0]} style.
    Image 2: {styles[1]} style.
    """
    
    print("Testing batch generation with distinct styles prompt (single candidate, multiple images)...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            )
        )
        
        print(f"Generated {len(response.candidates)} candidates.")
        for i, cand in enumerate(response.candidates):
            print(f"Candidate {i}: Has {len(cand.content.parts)} parts.")
            for part in cand.content.parts:
                print(f"  Part: {part.text if part.text else 'Image/Blob'}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_batch_styles()

