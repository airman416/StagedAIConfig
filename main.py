#!/usr/bin/env python3
"""
Carousel Pipeline Orchestrator

Three content pipelines, all ending in a TikTok carousel draft:

  STYLE PIPELINE (default)
    A photorealistic room reimagined in 5 interior design styles.
    Source: any room photo, or auto-generated via original.py (no flag).
    python main.py <image>

  STORY PIPELINE (--custom)
    Same as style, but slide captions are AI-generated narrative text
    (someone showing a skeptical family member the AI redesigns).
    python main.py <image> --custom

  FILL PIPELINE (-f)
    An awkward empty nook shown with 5 creative fill ideas.
    Source: problem-space photo, or auto-generated via original.py --fill.
    python main.py <image> -f

Auto-generation (omit image_path):
  python main.py                    # auto-generate room → style pipeline
  python main.py --custom           # auto-generate room → story pipeline
  python main.py -f                 # auto-generate problem space → fill pipeline
  python main.py -f --space alcove  # specific problem space → fill pipeline
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


def run_pipeline(image_path: str, fill_mode: bool = False, skip_approval: bool = False, captions: list[str] = None, use_custom_story: bool = False, source_image_path: str = None, tiktok_account: str | None = None) -> bool:
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
             items_list = list(item_paths.keys())
             story_image = source_image_path or orig_path or image_path
             captions = generate_screen_text(client, items_list, fill_mode=fill_mode, image_path=story_image)
             logger.info(f"📝 Generated Custom Screen Text:\n   - " + "\n   - ".join(captions))

        # --- Step 2: Edit (overlays) ---
        logger.info("✏️  [Stage 2/3] Edit (text + circle overlays) - Starting...")
        try:
            slide_paths = edit_carousel(orig_path, item_paths, output_dir, captions=captions, fill_mode=fill_mode)
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
            result = upload_carousel(slide_paths, fill_mode=fill_mode, account_id=tiktok_account)
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
Pipelines:
  (default)  Style  — room reimagined in 5 interior design styles
  --custom   Story  — same as style, but with AI narrative captions
  -f         Fill   — empty nook shown with 5 creative fill ideas

Auto-generation (omit image_path):
  python main.py              # generate room → style pipeline
  python main.py --custom     # generate room → story pipeline
  python main.py -f           # generate problem space → fill pipeline
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
        help="Problem space type to generate (fill mode only; ignored if image_path is provided)",
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
    parser.add_argument(
        "--story",
        action="store_true",
        help="Generate a story for fill mode (use with --fill). Ignored without --fill.",
    )
    parser.add_argument(
        "--tiktok-account",
        default=None,
        help="Zernio TikTok account ID for upload (default: @kim.designs8)",
    )
    args = parser.parse_args()

    # Logic: If no image path, generate one first
    pipeline_image_path = args.image_path

    if not pipeline_image_path:
        logger.info("🏗️  No image provided. [Stage 0] Generating source image...")
        try:
            client = init_gemini()

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            if args.fill:
                # Fill pipeline: generate a problem-space nook image
                space_type = args.space if args.space else random.choice(list(SPACE_TYPES.keys()))
                logger.info(f"   Fill mode — generating problem space: {space_type}")
                generated_filename = f"generated_source_{space_type}_{timestamp}.png"
                pipeline_image_path = str(Path.cwd() / generated_filename)
                generated_path = generate_original(client, pipeline_image_path, fill_mode=True, space_type=space_type)
            else:
                # Style/story pipeline: generate a photorealistic lived-in room
                logger.info("   Generating photorealistic room source image")
                generated_filename = f"generated_source_room_{timestamp}.png"
                pipeline_image_path = str(Path.cwd() / generated_filename)
                generated_path = generate_original(client, pipeline_image_path, fill_mode=False)

            if not generated_path:
                logger.error("❌ Failed to generate source image.")
                sys.exit(1)

            logger.info(f"✅ Generated source image: {generated_path}")

            # If user didn't auto-confirm, ask if they like the source
            if not args.yes:
                print(f"   (Open {generated_filename} to check it)")
                resp = input("Proceed with this source image? (y/n): ").lower().strip()
                if resp not in ("y", "yes"):
                    logger.warning("🚫 ABORTING: User rejected source image.")
                    sys.exit(0)
        except Exception as e:
            logger.critical(f"❌ Failed during source image generation: {e}")
            traceback.print_exc()
            sys.exit(1)

    # --story requires --fill; treat it as the fill equivalent of --custom
    use_fill_story = args.fill and getattr(args, "story", False)

    # If --fill without --story and no captions provided, use the default hook text
    if args.fill and not args.captions and not use_fill_story:
        args.captions = ["HELP!! what should i do\nwith this space??"]

    # Run the standard pipeline
    success = run_pipeline(
        pipeline_image_path,
        fill_mode=args.fill,
        skip_approval=args.yes,
        captions=args.captions,
        use_custom_story=args.custom or use_fill_story,
        source_image_path=pipeline_image_path,
        tiktok_account=args.tiktok_account,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
