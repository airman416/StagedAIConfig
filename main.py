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
import logging
import traceback
from pathlib import Path
import time

from reimagine import init_gemini, run_reimagine_for_carousel
from edit import edit_carousel
from upload import upload_carousel
from screen_text import generate_screen_text


import random
from original import generate_original, SPACE_TYPES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def run_pipeline(image_path: str, fill_mode: bool = False, skip_approval: bool = False, captions: list[str] = None, use_custom_story: bool = False) -> bool:
    """Orchestrate reimagine -> edit -> (confirm) -> upload."""
    
    try:
        if not os.path.exists(image_path):
            logger.error(f"❌ Image not found: {image_path}")
            return False

        date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = Path.cwd() / f"carousel_{date_str}"
        output_dir.mkdir(exist_ok=True)
        logger.info(f"📂 Output Directory Created: {output_dir.resolve()}")

        # --- Step 1: Reimagine ---
        mode = "fill" if fill_mode else "interior design styles"
        logger.info(f"🎨 [Stage 1/3] Reimagine ({mode}) - Starting...")
        
        try:
            client = init_gemini()
            orig_path, item_paths = run_reimagine_for_carousel(
                client, image_path, str(output_dir), fill=fill_mode, realistic=use_custom_story
            )
            if not orig_path or not item_paths:
                logger.error("❌ [Stage 1/3] Reimagine failed: No images returned.")
                return False
            logger.info("✅ [Stage 1/3] Reimagine complete.")
        except Exception as e:
            logger.error(f"❌ [Stage 1/3] Reimagine failed with exception: {e}")
            logger.debug(traceback.format_exc())
            return False

        if not skip_approval:
            print("\nPreview generated images in output folder.")
            resp = input("Proceed with editing & carousel? (y/n): ").lower().strip()
            if resp not in ("y", "yes"):
                logger.warning("🚫 Pipeline cancelled by user after Reimagine stage.")
                return False

        # --- Step 1.5: Custom Story Generation (if requested) ---
        if use_custom_story and not captions:
             client = init_gemini()
             # Need the item list (keys of item_paths)
             items_list = list(item_paths.keys())
             captions = generate_screen_text(client, items_list, fill_mode=fill_mode)
             logger.info(f"📝 Generated Custom Screen Text:\n   - " + "\n   - ".join(captions))

        # --- Step 2: Edit (overlays) ---
        logger.info("✏️  [Stage 2/3] Edit (text + circle overlays) - Starting...")
        try:
            slide_paths = edit_carousel(orig_path, item_paths, output_dir, captions=captions)
            slides_dir = output_dir / "slides"

            for i, p in enumerate(slide_paths, 1):
                logger.info(f"  ✅ Slide {i} generated: {p}")
            
            logger.info(f"✅ [Stage 2/3] Edit complete. Slides saved to: {slides_dir.resolve()}")
        except Exception as e:
            logger.error(f"❌ [Stage 2/3] Edit failed with exception: {e}")
            logger.debug(traceback.format_exc())
            return False

        # --- Step 3: Confirm, then upload ---
        print(f"\n📁 Carousel slides saved to: {slides_dir.resolve()}")
        print("   Review the images, then confirm to upload to TikTok.")
        
        if not skip_approval:
            resp = input("\nReady to upload to TikTok as draft? (y/n): ").lower().strip()
            if resp not in ("y", "yes"):
                 logger.warning("🚫 Upload cancelled by user. Slides are saved locally.")
                 return True # Not a failure, just a stop

        # --- Step 4: Upload ---
        logger.info("📤 [Stage 3/3] Upload to TikTok - Starting...")
        try:
            integration_id = "cmlr80l5303ppmn0y3kjylrl3" if use_custom_story else None
            result = upload_carousel(slide_paths, integration_id=integration_id)
            if result:
                logger.info("✅ [Stage 3/3] Upload complete!")
            else:
                logger.error("❌ [Stage 3/3] Upload failed.")
            return result
        except Exception as e:
            logger.error(f"❌ [Stage 3/3] Upload failed with exception: {e}")
            logger.debug(traceback.format_exc())
            return False

    except Exception as e:
        logger.critical(f"❌ Unhandled exception in pipeline: {e}")
        traceback.print_exc()
        return False


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
    parser.add_argument(
        "--captions",
        nargs="*",
        help="Custom captions for slides (in order). Use \\n for line breaks.",
    )
    parser.add_argument(
        "--custom",
        action="store_true",
        help="Generate custom story captions using Gemini (ignores --captions if set)",
    )
    args = parser.parse_args()

    # Logic: If no image path, generate one first
    pipeline_image_path = args.image_path

    if not pipeline_image_path:
        logger.info("🏗️  No image provided. [Stage 0] Generating source image...")
        try:
            client = init_gemini()
            
            # Decide space type
            space_type = args.space if args.space else random.choice(list(SPACE_TYPES.keys()))
            logger.info(f"   Selected space type: {space_type}")
            
            # Create a temp output path for the source
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            generated_filename = f"generated_source_{space_type}_{timestamp}.png"
            pipeline_image_path = str(Path.cwd() / generated_filename)
            
            generated_path = generate_original(client, space_type, pipeline_image_path, dated_look=args.custom)
            
            if not generated_path:
                logger.error("❌ Failed to generate source image.")
                sys.exit(1)
                
            logger.info(f"✅ Generated source image: {generated_path}")
            
            # If user didn't auto-confirm, ask if they like the source
            if not args.yes:
                # We can't easily show it in CLI, but we can pause
                print(f"   (Open {generated_filename} to check it)")
                resp = input("Proceed with this source image? (y/n): ").lower().strip()
                if resp not in ("y", "yes"):
                    logger.warning("🚫 ABORTING: User rejected source image.")
                    sys.exit(0)
        except Exception as e:
            logger.critical(f"❌ Failed during source image generation: {e}")
            traceback.print_exc()
            sys.exit(1)

    # If --fill is used but no captions provided, use the "WAIT!!" text
    if args.fill and not args.captions and not args.custom:
        args.captions = ["WAIT!! what should i do\nwith this space??"]

    # Run the standard pipeline
    success = run_pipeline(
        pipeline_image_path, 
        fill_mode=args.fill, 
        skip_approval=args.yes, 
        captions=args.captions, 
        use_custom_story=args.custom
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
