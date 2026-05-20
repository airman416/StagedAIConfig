
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Import our custom modules
from edit import edit_carousel
from upload import upload_carousel
from screen_text import generate_screen_text
from reimagine import init_gemini

# Load environment variables for Gemini (to re-gen captions) and Zernio
load_dotenv()

def resume_custom_workflow(carousel_dir: str):
    """
    Resumes the custom workflow for a specific carousel directory where:
    - Original image exists (original.png).
    - Reimagined images exist (0_..., 1_..., etc.).
    - But editing/captioning/upload failed.
    """
    
    output_dir = Path(carousel_dir)
    if not output_dir.exists():
        print(f"❌ Directory not found: {output_dir}")
        return

    print(f"🔄 Resuming workflow for: {output_dir.name}")

    # 1. Identify Images
    original_path = str(output_dir / "original.png")
    if not os.path.exists(original_path):
        print("❌ 'original.png' not found in directory.")
        return

    # Find the reimagined images (0_..., 1_..., etc.)
    # We need to map them back to style names for captions.
    # Filenames are like "0_modern_minimalist.png", "1_scandinavian.png"
    # We can parse the style name from the filename.
    
    item_paths = {}
    reimagined_files = sorted(list(output_dir.glob("[0-9]_*.png")))
    
    if not reimagined_files:
        print("❌ No reimagined images (0_*.png, etc.) found.")
        return

    print(f"📸 Found {len(reimagined_files)} reimagined images.")

    for p in reimagined_files:
        # e.g., "0_modern_minimalist.png" -> "modern minimalist"
        name_part = p.stem.split("_", 1)[1] # "modern_minimalist"
        style_name = name_part.replace("_", " ").title() # "Modern Minimalist"
        item_paths[style_name] = str(p)

    # 2. Generate Captions (Story)
    print("📝 Generating story captions...")
    try:
        client = init_gemini()
        # Pass realistic_mode=True context (which mapped to custom story context)
        # In captions.py, fill_mode=False triggers the "Renovation" story context.
        captions = generate_screen_text(client, list(item_paths.keys()), fill_mode=False, image_path=original_path)
        for i, c in enumerate(captions):
            print(f"   [{i+1}] {c}")
    except Exception as e:
        print(f"❌ Failed to generate captions: {e}")
        return

    # 3. Running Edit
    print("✏️  Editing slides...")
    try:
        slide_paths = edit_carousel(original_path, item_paths, output_dir, captions=captions)
        print(f"✅ Generated {len(slide_paths)} slides.")
    except Exception as e:
        print(f"❌ Editing failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Ask to upload?
    resp = input("\nReady to upload to TikTok draft? (y/n): ").lower().strip()
    if resp not in ("y", "yes"):
        print("🚫 Upload cancelled.")
        return

    # 4. Upload
    print("📤 Uploading...")
    success = upload_carousel(slide_paths)
    if success:
        print("✅ Workflow complete!")
    else:
        print("❌ Upload failed.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python resume_custom.py <carousel_directory>")
        sys.exit(1)
    
    resume_custom_workflow(sys.argv[1])
