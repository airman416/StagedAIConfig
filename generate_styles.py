#!/usr/bin/env python3
"""
Interior Design Style Generator

This script:
1. Reads style names from a text file (one per line)
2. Uses Gemini to research each style and determine applicable categories
3. Generates images using Gemini's image generation
4. Uploads images to Firebase Storage
5. Updates firebase-config.json with new style entries
6. Uploads config to Firebase Remote Config and publishes
"""

import json
import os
import sys
import re
import tempfile
import argparse
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, storage
import google.auth.transport.requests
from google.oauth2 import service_account
from google import genai
from google.genai import types
from PIL import Image
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in .env file.")
SERVICE_ACCOUNT_PATH = "serviceAccountKey.json"
FIREBASE_BUCKET = "stage-ai-e610c.firebasestorage.app"
CONFIG_PATH = "firebase-config.json"
IMAGES_DIR = "IMAGES"

# Available categories for interior design styles
ALL_CATEGORIES = ["interior", "kitchen", "bedroom", "bathroom", "garden", "declutter"]

# Available icons (from existing styles)
AVAILABLE_ICONS = ["sofa", "star", "sparkle", "chair", "leaf", "building", "house", "sparkles"]

# Available color palettes (from existing styles)
AVAILABLE_PALETTES = ["neutral", "monochrome", "earth", "warm", "ocean", "forest", "pastel"]


def init_firebase():
    """Initialize Firebase Admin SDK."""
    if not firebase_admin._apps:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred, {
            "storageBucket": FIREBASE_BUCKET
        })
    return storage.bucket()


def init_gemini():
    """Initialize Gemini client."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    return client


def research_style(client, style_name: str) -> dict:
    """
    Use Gemini to research an interior design style and determine its properties.
    
    Returns a dict with:
    - id: snake_case identifier
    - name: Display name
    - description: Short description
    - categories: List of applicable categories
    - icon: Icon name
    - prompt_modifier: Prompt for image generation
    - default_color_palette: Color palette name
    """
    
    prompt = f"""You are an expert interior designer. Research the interior design style "{style_name}" and provide detailed information.

Respond ONLY with a valid JSON object (no markdown, no explanation) with these exact fields:

{{
    "id": "snake_case_id_for_the_style",
    "name": "Display Name of Style",
    "description": "A short, elegant description (under 50 characters) that captures the essence",
    "categories": ["list", "of", "applicable", "categories"],
    "icon": "icon_name",
    "prompt_modifier": "detailed visual description for AI image generation: materials, colors, textures, atmosphere, furniture styles",
    "default_color_palette": "palette_name"
}}

IMPORTANT RULES:
1. "categories" must ONLY contain items from this list: {ALL_CATEGORIES}
   - "interior" = living room / general interior
   - "kitchen" = kitchen spaces
   - "bedroom" = bedroom spaces  
   - "bathroom" = bathroom spaces
   - "garden" = outdoor/garden spaces (only if style applies outdoors)
   - "declutter" = organization-focused (rarely applicable)
   
   Choose categories that genuinely fit the style. Most interior styles work for: interior, kitchen, bedroom, bathroom.
   Garden is only for styles that work outdoors. Declutter is very rare.

2. "icon" must be one of: {AVAILABLE_ICONS}
   Choose the most fitting icon for the style's aesthetic.

3. "default_color_palette" must be one of: {AVAILABLE_PALETTES}
   - neutral: beige, white, soft grays
   - monochrome: black, white, grays
   - earth: browns, tans, terracotta
   - warm: oranges, reds, yellows
   - ocean: blues, teals, seafoam
   - forest: greens, deep emeralds
   - pastel: soft pinks, lavenders, mint

4. "prompt_modifier" should be rich and descriptive, suitable for generating beautiful interior images.
   Include: materials, colors, textures, lighting, furniture styles, decorative elements, atmosphere.
   Example: "warm wood tones, iconic furniture shapes, bold geometric patterns, retro colors"

5. "id" should be lowercase with underscores, derived from the style name.

6. "description" should be evocative and under 50 characters.

Research the style "{style_name}" thoroughly and provide accurate, design-appropriate responses."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
        )
    )
    
    # Parse JSON from response
    response_text = response.text.strip()
    
    # Remove markdown code blocks if present
    if response_text.startswith("```"):
        response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
        response_text = re.sub(r'\n?```$', '', response_text)
    
    try:
        style_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"  ⚠️  Failed to parse JSON response: {e}")
        print(f"  Response was: {response_text[:500]}...")
        raise
    
    # Validate categories
    style_data["categories"] = [c for c in style_data.get("categories", []) if c in ALL_CATEGORIES]
    if not style_data["categories"]:
        style_data["categories"] = ["interior", "bedroom"]  # Default fallback
    
    # Validate icon
    if style_data.get("icon") not in AVAILABLE_ICONS:
        style_data["icon"] = "sofa"  # Default fallback
    
    # Validate palette
    if style_data.get("default_color_palette") not in AVAILABLE_PALETTES:
        style_data["default_color_palette"] = "neutral"  # Default fallback
    
    return style_data


def generate_image(client, style_data: dict, category: str) -> bytes | None:
    """
    Generate an image for a style and category using Gemini's image generation.
    
    Returns the image bytes or None if generation failed.
    """
    
    # Build the image generation prompt
    category_descriptions = {
        "interior": "a beautiful living room interior",
        "kitchen": "a stunning modern kitchen",
        "bedroom": "an elegant, cozy bedroom",
        "bathroom": "a luxurious bathroom",
        "garden": "a beautiful outdoor garden space",
        "declutter": "a clean, organized living space"
    }
    
    scene = category_descriptions.get(category, "an interior space")
    
    prompt = f"""Create a professional interior design photograph of {scene} in the {style_data['name']} style.

Style characteristics: {style_data['prompt_modifier']}

Requirements:
- Photorealistic, high-quality interior photography
- Natural lighting with warm atmosphere
- Shot from a pleasing angle that showcases the space
- No people in the image
- Professional real estate or interior design magazine quality"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="4:3",
                ),
            )
        )
        
        # Extract image from response
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                return part.inline_data.data
        
        print(f"  ⚠️  No image in response for {category}")
        return None
        
    except Exception as e:
        print(f"  ❌ Image generation failed for {category}: {e}")
        return None


def upload_to_firebase(bucket, image_bytes: bytes, destination_path: str) -> str | None:
    """
    Upload image bytes to Firebase Storage and return the download URL.
    """
    try:
        blob = bucket.blob(destination_path)
        blob.upload_from_string(image_bytes, content_type="image/png")
        blob.make_public()
        
        # Get the download URL with token
        blob.reload()
        
        # Generate a signed URL or use the public URL format
        # Firebase Storage URL format
        url = f"https://firebasestorage.googleapis.com/v0/b/{FIREBASE_BUCKET}/o/{destination_path.replace('/', '%2F')}?alt=media"
        
        # Get the download token
        if blob.metadata and 'firebaseStorageDownloadTokens' in blob.metadata:
            token = blob.metadata['firebaseStorageDownloadTokens']
            url += f"&token={token}"
        else:
            # Generate new token
            import uuid
            token = str(uuid.uuid4())
            blob.metadata = {'firebaseStorageDownloadTokens': token}
            blob.patch()
            url += f"&token={token}"
        
        return url
        
    except Exception as e:
        print(f"  ❌ Upload failed for {destination_path}: {e}")
        return None


def save_image_locally(image_bytes: bytes, style_id: str, category: str) -> str:
    """Save image locally to IMAGES directory."""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    
    if category == "interior":
        filename = f"{style_id}.png"
    else:
        filename = f"{style_id}_{category}.png"
    
    filepath = os.path.join(IMAGES_DIR, filename)
    
    with open(filepath, "wb") as f:
        f.write(image_bytes)
    
    return filepath


def load_config() -> list:
    """Load the current firebase-config.json."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return []


def save_config(config: list):
    """Save the updated config to firebase-config.json."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def get_access_token():
    """Get OAuth2 access token for Firebase Remote Config API."""
    SCOPES = ['https://www.googleapis.com/auth/firebase.remoteconfig']
    
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_PATH,
        scopes=SCOPES
    )
    
    request = google.auth.transport.requests.Request()
    creds.refresh(request)
    
    return creds.token


def get_remote_config():
    """Get current Remote Config from Firebase."""
    # Load service account to get project ID
    with open(SERVICE_ACCOUNT_PATH, 'r') as f:
        sa = json.load(f)
    project_id = sa['project_id']
    
    access_token = get_access_token()
    
    url = f"https://firebaseremoteconfig.googleapis.com/v1/projects/{project_id}/remoteConfig"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept-Encoding': 'gzip',
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json(), response.headers.get('ETag')
    else:
        print(f"  ❌ Failed to get Remote Config: {response.status_code}")
        print(f"     {response.text}")
        return None, None


def upload_remote_config(config: list, publish: bool = True):
    """
    Upload the styles config to Firebase Remote Config.
    
    Args:
        config: The styles configuration list
        publish: If True, publish immediately. If False, just validate.
    """
    print("\n📤 Uploading to Firebase Remote Config...")
    
    # Load service account to get project ID
    with open(SERVICE_ACCOUNT_PATH, 'r') as f:
        sa = json.load(f)
    project_id = sa['project_id']
    
    # Get access token
    access_token = get_access_token()
    
    # First, get the current config to get the ETag
    print("  📥 Fetching current Remote Config...")
    current_config, etag = get_remote_config()
    
    if etag is None:
        # No existing config, use wildcard
        etag = '*'
        current_config = {"parameters": {}, "conditions": []}
    
    print(f"  ✅ Got ETag: {etag[:20]}...")
    
    # Update the styles parameter in the config
    if 'parameters' not in current_config:
        current_config['parameters'] = {}
    
    # Set the styles as a Remote Config parameter with JSON value type
    current_config['parameters']['styles'] = {
        'defaultValue': {
            'value': json.dumps(config)
        },
        'description': 'Interior design styles configuration',
        'valueType': 'JSON'
    }
    
    # Upload the updated config
    url = f"https://firebaseremoteconfig.googleapis.com/v1/projects/{project_id}/remoteConfig"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json; UTF-8',
        'If-Match': etag,
    }
    
    # Add validate-only parameter if not publishing
    if not publish:
        url += '?validate_only=true'
        print("  🔍 Validating config (not publishing)...")
    else:
        print("  🚀 Publishing config...")
    
    response = requests.put(url, headers=headers, json=current_config)
    
    if response.status_code == 200:
        if publish:
            print("  ✅ Remote Config published successfully!")
            new_etag = response.headers.get('ETag', 'unknown')
            print(f"  📋 New ETag: {new_etag[:20]}...")
        else:
            print("  ✅ Config validation passed!")
        return True
    else:
        print(f"  ❌ Failed to upload Remote Config: {response.status_code}")
        print(f"     {response.text}")
        return False


def style_exists(config: list, style_id: str) -> bool:
    """Check if a style already exists in the config."""
    return any(s.get("id") == style_id for s in config)


def process_style(client, bucket, style_name: str, config: list) -> dict | None:
    """
    Process a single style: research, generate images, upload, and return config entry.
    """
    print(f"\n{'='*60}")
    print(f"Processing style: {style_name}")
    print('='*60)
    
    # Step 1: Research the style
    print("\n📚 Researching style with Gemini...")
    try:
        style_data = research_style(client, style_name)
        print(f"  ✅ Style ID: {style_data['id']}")
        print(f"  ✅ Name: {style_data['name']}")
        print(f"  ✅ Description: {style_data['description']}")
        print(f"  ✅ Categories: {style_data['categories']}")
        print(f"  ✅ Prompt: {style_data['prompt_modifier'][:80]}...")
    except Exception as e:
        print(f"  ❌ Research failed: {e}")
        return None
    
    # Check if style already exists
    if style_exists(config, style_data['id']):
        print(f"\n⚠️  Style '{style_data['id']}' already exists in config. Skipping...")
        return None
    
    # Step 2: Generate and upload images for each category
    print(f"\n🎨 Generating images for {len(style_data['categories'])} categories...")
    category_image_urls = {}
    
    for category in style_data['categories']:
        print(f"\n  📷 Generating {category} image...")
        
        # Generate image
        image_bytes = generate_image(client, style_data, category)
        
        if image_bytes:
            # Save locally
            local_path = save_image_locally(image_bytes, style_data['id'], category)
            print(f"    💾 Saved locally: {local_path}")
            
            # Upload to Firebase
            if category == "interior":
                storage_path = f"styles/{style_data['id']}.png"
            else:
                storage_path = f"styles/{style_data['id']}_{category}.png"
            
            print(f"    ☁️  Uploading to Firebase: {storage_path}")
            url = upload_to_firebase(bucket, image_bytes, storage_path)
            
            if url:
                category_image_urls[category] = url
                print(f"    ✅ Uploaded successfully")
            else:
                print(f"    ❌ Upload failed")
        else:
            print(f"    ❌ Image generation failed")
    
    # Build the final style entry
    style_entry = {
        "id": style_data['id'],
        "name": style_data['name'],
        "description": style_data['description'],
        "categories": style_data['categories'],
        "icon": style_data['icon'],
        "prompt_modifier": style_data['prompt_modifier'],
        "default_color_palette": style_data['default_color_palette'],
        "category_image_urls": category_image_urls
    }
    
    return style_entry


def generate_styles(styles_file: str):
    """Generate new styles from a file."""
    if not os.path.exists(styles_file):
        print(f"❌ File not found: {styles_file}")
        return False
    
    # Read style names from file
    with open(styles_file, "r") as f:
        style_names = [line.strip() for line in f if line.strip()]
    
    if not style_names:
        print("❌ No style names found in file.")
        return False
    
    print(f"🎯 Found {len(style_names)} styles to process:")
    for name in style_names:
        print(f"  - {name}")
    
    # Initialize services
    print("\n🔧 Initializing services...")
    client = init_gemini()
    print("  ✅ Gemini client initialized")
    
    bucket = init_firebase()
    print("  ✅ Firebase initialized")
    
    # Load existing config
    config = load_config()
    print(f"  ✅ Loaded config with {len(config)} existing styles")
    
    # Process each style
    new_styles = []
    for style_name in style_names:
        style_entry = process_style(client, bucket, style_name, config)
        if style_entry:
            new_styles.append(style_entry)
            config.append(style_entry)
    
    # Save updated config
    if new_styles:
        save_config(config)
        print(f"\n{'='*60}")
        print(f"🎉 SUCCESS! Added {len(new_styles)} new styles to {CONFIG_PATH}")
        print('='*60)
        for style in new_styles:
            print(f"  ✅ {style['name']} ({style['id']})")
            print(f"     Categories: {', '.join(style['categories'])}")
            print(f"     Images: {len(style['category_image_urls'])} uploaded")
        return True
    else:
        print(f"\n⚠️  No new styles were added.")
        return False


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description='Generate interior design styles and manage Firebase Remote Config',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate new styles from a file
  python generate_styles.py styles.txt

  # Generate styles and publish to Remote Config
  python generate_styles.py styles.txt --publish

  # Only publish current config to Remote Config (no generation)
  python generate_styles.py --publish-only

  # Validate config without publishing
  python generate_styles.py --validate
        """
    )
    
    parser.add_argument(
        'styles_file',
        nargs='?',
        help='Text file with style names (one per line)'
    )
    
    parser.add_argument(
        '--publish',
        action='store_true',
        help='Publish to Firebase Remote Config after generating styles'
    )
    
    parser.add_argument(
        '--publish-only',
        action='store_true',
        help='Only publish current firebase-config.json to Remote Config (skip generation)'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate the config against Remote Config without publishing'
    )
    
    args = parser.parse_args()
    
    # Handle publish-only mode
    if args.publish_only:
        config = load_config()
        print(f"📋 Loaded {len(config)} styles from {CONFIG_PATH}")
        
        # Initialize Firebase (needed for auth)
        init_firebase()
        
        success = upload_remote_config(config, publish=True)
        sys.exit(0 if success else 1)
    
    # Handle validate mode
    if args.validate:
        config = load_config()
        print(f"📋 Loaded {len(config)} styles from {CONFIG_PATH}")
        
        # Initialize Firebase (needed for auth)
        init_firebase()
        
        success = upload_remote_config(config, publish=False)
        sys.exit(0 if success else 1)
    
    # Normal mode: require styles file
    if not args.styles_file:
        parser.print_help()
        print("\n❌ Error: styles_file is required for generation mode")
        print("   Use --publish-only to publish existing config without generating new styles")
        sys.exit(1)
    
    # Generate styles
    success = generate_styles(args.styles_file)
    
    # Optionally publish to Remote Config
    if args.publish and success:
        config = load_config()
        upload_remote_config(config, publish=True)
    elif args.publish:
        print("\n⚠️  Skipping Remote Config publish due to generation issues")


if __name__ == "__main__":
    main()

