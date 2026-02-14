#!/usr/bin/env python3
"""
Carousel Pipeline Orchestrator

Runs the full carousel workflow:
1. reimagine  - Generate original + 5 reimagined images (interior styles OR fill ideas)
2. edit       - Apply text/circle overlays (slide 1: HELP!! + circle; slides 2-6: style name + tagline)
3. upload     - Upload to TikTok as draft

Two reimagine modes:
- Interior design (default): Identifies 5 styles, reimagines the room in each
- Fill (-f): Brainstorms 5 ideas to fill empty space, generates filled versions

Usage:
  python main.py <image_path>                    # Interior design styles
  python main.py <image_path> -f                  # Fill empty space ideas
  python main.py <image_path> -y                  # Skip approval prompts
  python main.py <image_path> -f -y              # Fill mode, no prompts
"""

import os
import sys
import datetime
from pathlib import Path

from reimagine import init_gemini, run_reimagine_for_carousel
from edit import edit_carousel
from upload import upload_carousel


import random
from original import generate_original, SPACE_TYPES


def run_pipeline(image_path: str, fill_mode: bool = False, skip_approval: bool = False) -> bool:
    """Orchestrate reimagine -> edit -> (confirm) -> upload."""
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return False

    date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = Path.cwd() / f"carousel_{date_str}"
    output_dir.mkdir(exist_ok=True)
    print(f"📂 Output: {output_dir.resolve()}")

    # If the image is just a filename in the current dir, copy it to output for safekeeping?
    # Not strictly necessary but nice.
    # shutil.copy(image_path, output_dir / "source_image.png")

    # --- Step 1: Reimagine ---
    mode = "fill" if fill_mode else "interior design styles"
    print(f"\n🎨 Step 1: Reimagine ({mode})")
    client = init_gemini()
    orig_path, item_paths = run_reimagine_for_carousel(
        client, image_path, str(output_dir), fill=fill_mode
    )
    if not orig_path or not item_paths:
        return False

    if not skip_approval:
        resp = input("\nProceed with editing & carousel? (y/n): ").lower().strip()
        if resp not in ("y", "yes"):
            print("Cancelled.")
            return False

    # --- Step 2: Edit (overlays) ---
    print("\n✏️  Step 2: Edit (text + circle overlays)")
    slide_paths = edit_carousel(orig_path, item_paths, output_dir)
    slides_dir = output_dir / "slides"

    for i, p in enumerate(slide_paths, 1):
        print(f"  ✅ Slide {i}: {p}")

    # --- Step 3: Confirm, then upload ---
    print(f"\n📁 Carousel slides saved to: {slides_dir.resolve()}")
    print("   Review the images, then confirm to upload to TikTok.")
    if not skip_approval:
        resp = input("\nReady to upload to TikTok as draft? (y/n): ").lower().strip()
        if resp not in ("y", "yes"):
            print("Upload cancelled. Your slides are saved locally.")
            return True

    # --- Step 4: Upload ---
    print("\n📤 Step 3: Upload")
    return upload_carousel(slide_paths)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate carousel and upload to TikTok draft",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Reimagine modes:
  (default) Interior design - Identifies 5 styles, reimagines room in each
  -f       Fill            - Brainstorms 5 ideas to fill empty space (4 good + 1 silly)

Automatic Generation:
  If no image_path is provided, the script will generate a specific "problem space"
  image (using original.py) before running the pipeline.
        """,
    )
    parser.add_argument(
        "image_path",
        nargs="?",
        help="Path to source interior image. If omitted, generates a new one.",
    )
    parser.add_argument(
        "-f",
        "--fill",
        action="store_true",
        help="Fill mode: brainstorm ideas to fill empty space (instead of interior design styles)",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip approval prompts (generation + upload)",
    )
    parser.add_argument(
        "--space",
        choices=list(SPACE_TYPES.keys()),
        help="Specific space type to generate (only used if image_path is omitted)",
    )
    args = parser.parse_args()

    # Logic: If no image path, generate one first
    pipeline_image_path = args.image_path

    if not pipeline_image_path:
        print("\n🏗️  No image provided. Step 0: Generating source image...")
        client = init_gemini()
        
        # Decide space type
        space_type = args.space if args.space else random.choice(list(SPACE_TYPES.keys()))
        
        # Create a temp output path for the source
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        generated_filename = f"generated_source_{space_type}_{timestamp}.png"
        pipeline_image_path = str(Path.cwd() / generated_filename)
        
        generated_path = generate_original(client, space_type, pipeline_image_path)
        
        if not generated_path:
            print("❌ Failed to generate source image.")
            sys.exit(1)
            
        print(f"✅ Generated source image: {generated_path}")
        
        # If user didn't auto-confirm, ask if they like the source
        if not args.yes:
            # We can't easily show it in CLI, but we can pause
            print(f"   (Open {generated_filename} to check it)")
            resp = input("Proceed with this source image? (y/n): ").lower().strip()
            if resp not in ("y", "yes"):
                print("ABORTING: User rejected source image.")
                sys.exit(0)

    # Run the standard pipeline
    success = run_pipeline(
        pipeline_image_path, fill_mode=args.fill, skip_approval=args.yes
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
