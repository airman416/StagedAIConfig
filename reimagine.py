#!/usr/bin/env python3
"""
Reimagine Interior Design Styles

This script:
1. Takes an image path as an argument
2. Uses Gemini to identify 7 suitable interior design styles OR fill ideas
3. Generates reimagined versions of the original image
4. Saves output to a date-stamped folder
"""

import os
import argparse
import datetime
import shutil
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in .env file.")

def init_gemini():
    """Initialize Gemini client."""
    return genai.Client(api_key=GEMINI_API_KEY)

def analyze_image(client, image_path):
    """
    Analyze the image to identify 7 suitable interior design styles.
    """
    try:
        # Open image
        image = Image.open(image_path)
    except Exception as e:
        print(f"❌ Error opening image: {e}")
        return []

    prompt = """
    Analyze this interior design image. Identify 7 distinct interior design styles that would work remarkably well for this specific space, layout, and lighting.
    
    Return ONLY a raw list of the 7 style names, one per line. 
    Example format:
    Modern Minimalist
    Industrial Chic
    Scandinavian
    ...
    
    Do not include numbering, bullet points, or extra text.
    """
    
    print("🔍 Analyzing image for styles...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                temperature=0.7,
            )
        )
        
        # Parse styles
        text = response.text.strip()
        styles = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Clean up styles (remove numbering if model ignored instructions)
        clean_styles = []
        for s in styles:
            # Remove "1. " or "- " prefixes
            s = s.lstrip('0123456789.- ').strip()
            if s:
                clean_styles.append(s)
                
        return clean_styles[:7]
        
    except Exception as e:
        print(f"❌ Error analyzing image: {e}")
        return []

def brainstorm_fill_ideas(client, image_path):
    """
    Brainstorm creative and humorous ideas to fill the empty space.
    """
    try:
        image = Image.open(image_path)
    except Exception as e:
        print(f"❌ Error opening image: {e}")
        return []

    prompt = """
    Analyze this interior design image, which likely contains empty space.
    Brainstorm 7 creative, distinct, and potentially humorous or unexpected ways to fill this space with furniture, objects, lighting, and decor.
    
    The ideas should range from practical/stylish to whimsical/humorous.
    
    Return ONLY a raw list of the 7 ideas/themes, one per line.
    Example format:
    Cozy Reading Nook with a Giant Beanbag
    Victorian Tea Room Setup
    Indoor Jungle with Hammock
    Sci-Fi Gamer Station
    ...
    
    Do not include numbering, bullet points, or extra text.
    """
    
    print("🧠 Brainstorming creative fill ideas...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                temperature=0.8, # Higher temperature for creativity
            )
        )
        
        text = response.text.strip()
        ideas = [line.strip() for line in text.split('\n') if line.strip()]
        
        clean_ideas = []
        for s in ideas:
            s = s.lstrip('0123456789.- ').strip()
            if s:
                clean_ideas.append(s)
                
        return clean_ideas[:7]
        
    except Exception as e:
        print(f"❌ Error brainstorming: {e}")
        return []

def reimagine_image(client, image_path, style_name, output_dir):
    """
    Generate a reimagined version of the image in the specified style.
    """
    try:
        image = Image.open(image_path)
    except Exception as e:
        print(f"❌ Error opening image for generation: {e}")
        return

    # Create a prompt that encourages maintaining the layout but changing the style
    prompt = f"""
    Reimagine this exact room with a DRAMATIC and BOLD transformation into the {style_name} interior design style.
    
    CRITICAL STRUCTURAL CONSTRAINTS (MUST FOLLOW):
    - PRESERVE EXACTLY: The room layout, perspective, ceiling height, and ALL structural elements (walls, windows, doors, beams).
    - DO NOT move walls, remove windows, change door placements, or alter the architecture.
    
    DESIGN INSTRUCTIONS (BE DRAMATIC):
    - COMPLETELY TRANSFORM the interior atmosphere, furniture, and decor to fully embody {style_name}.
    - Use bold lighting, rich textures, and distinct materials characteristic of {style_name}.
    - Make the design choices striking, high-contrast, and impactful while respecting the existing shell of the room.
    - Photorealistic, high-quality interior design photography.
    """

    print(f"🎨 Generating {style_name} version...")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="9:16",
                ),
            )
        )
        
        # Extract and save image
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                img_data = part.inline_data.data
                
                # Create safe filename
                safe_name = "".join(c for c in style_name if c.isalnum() or c in (' ', '_', '-')).strip()
                safe_name = safe_name.replace(' ', '_').lower()
                filename = f"{safe_name}.png"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, "wb") as f:
                    f.write(img_data)
                print(f"  ✅ Saved: {filepath}")
                return filepath
                
        print(f"  ⚠️  No image generated for {style_name}")
        
    except Exception as e:
        print(f"  ❌ Generation failed for {style_name}: {e}")

def generate_fill_image(client, image_path, idea, output_dir):
    """
    Generate an image with the space filled based on the idea.
    """
    try:
        image = Image.open(image_path)
    except Exception as e:
        print(f"❌ Error opening image: {e}")
        return

    prompt = f"""
    Edit this image to fill the empty space based on this concept: {idea}.
    
    INSTRUCTIONS:
    - Keep the original room's perspective, lighting, and general architectural shell (walls, windows, floor type).
    - ADD furniture, objects, decor, and lighting to match the concept "{idea}".
    - DO NOT ADD any new structural elements (like built-in shelves, dividers, new walls, or architectural changes).
    - The room's structure must remain EXACTLY as it is. Only movable furniture and decor should be added.
    - Be creative and detailed.
    - Make it photorealistic and high quality.
    - Seamlessly blend the new objects into the existing environment.
    """

    print(f"🎨 Generating: {idea}...")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="9:16",
                ),
            )
        )
        
        # Save logic
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                img_data = part.inline_data.data
                
                safe_name = "".join(c for c in idea if c.isalnum() or c in (' ', '_', '-')).strip()
                safe_name = safe_name.replace(' ', '_').lower()[:50] # Limit length
                filename = f"{safe_name}.png"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, "wb") as f:
                    f.write(img_data)
                print(f"  ✅ Saved: {filepath}")
                return filepath
                
        print(f"  ⚠️  No image generated for {idea}")
        
    except Exception as e:
        print(f"  ❌ Generation failed for {idea}: {e}")

def regenerate_original(client, image_path, output_dir):
    """
    Regenerate the original image in 9:16 aspect ratio.
    """
    try:
        image = Image.open(image_path)
    except Exception as e:
        print(f"❌ Error opening image for regeneration: {e}")
        return

    prompt = """
    Regenerate this exact room in high quality.
    
    INSTRUCTIONS:
    - PRESERVE EXACTLY: The room layout, furniture, decor, lighting, and style.
    - The goal is to output a high-quality version of this image in 9:16 format.
    - If the original is not 9:16, extend the scene naturally to fill the frame (ceiling/floor) without changing the existing elements.
    - Photorealistic, high-quality interior design photography.
    """

    print(f"🎨 Regenerating original in 9:16...")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="9:16",
                ),
            )
        )
        
        # Extract and save image
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                img_data = part.inline_data.data
                
                filename = "original.png"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, "wb") as f:
                    f.write(img_data)
                print(f"  ✅ Saved 9:16 original: {filepath}")
                return filepath
                
        print(f"  ⚠️  No image generated for original")
        
    except Exception as e:
        print(f"  ❌ Generation failed for original: {e}")

def main():
    parser = argparse.ArgumentParser(description='Reimagine an interior image in different styles.')
    parser.add_argument('image_path', help='Path to the source image file')
    parser.add_argument('-y', '--yes', action='store_true', help='Skip approval and automatically proceed with generation')
    parser.add_argument('-f', '--fill', action='store_true', help='Fill empty space with creative objects instead of restyling')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.image_path):
        print(f"❌ Image not found: {args.image_path}")
        return
        
    client = init_gemini()
    
    # Step 1: Analyze and get styles or ideas
    if args.fill:
        items = brainstorm_fill_ideas(client, args.image_path)
        item_type = "Ideas"
    else:
        items = analyze_image(client, args.image_path)
        item_type = "Styles"
    
    if not items:
        print(f"❌ Could not identify {item_type.lower()}.")
        return
        
    print(f"\n✨ Identified {item_type}:")
    for s in items:
        print(f"  - {s}")
    
    # Approval Step
    if not args.yes:
        while True:
            response = input("\nProceed with generation? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                break
            elif response in ['n', 'no']:
                print("❌ Operation cancelled by user.")
                return
    
    # Step 2: Create output directory
    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = os.path.join(os.getcwd(), date_str)
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n📂 Output directory: {output_dir}")
    
    # Step 2.5: Regenerate original image in 9:16
    regenerate_original(client, args.image_path, output_dir)
    
    # Step 3: Generate images
    print("\n🚀 Starting generation...")
    for item in items:
        if args.fill:
            generate_fill_image(client, args.image_path, item, output_dir)
        else:
            reimagine_image(client, args.image_path, item, output_dir)
        
    print("\n✨ Done!")

if __name__ == "__main__":
    main()
