#!/usr/bin/env python3
"""
TikTok Carousel Upload

Uploads carousel slides to TikTok as DRAFT via Postiz API.
Expects pre-edited slide images (from edit.py).

Usage:
  python upload.py <slide1.jpg> <slide2.jpg> ...
  python upload.py --from-dir ./carousel_xxx/slides/
"""

import json
import os
import sys
import datetime
from pathlib import Path
from typing import Union

from dotenv import load_dotenv
import requests
from nanoid import generate

load_dotenv()

POSTIZ_API_KEY = os.getenv("POSTIZ_API_KEY")
if not POSTIZ_API_KEY:
    raise ValueError("POSTIZ_API_KEY not found in .env")

POSTIZ_BASE = "https://api.postiz.com/public/v1"
TIKTOK_INTEGRATION_ID = "cmljzps6w01xzol0y7l9889vh"

# Postiz-style IDs for group (no API returns this; nanoid used as fallback)
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def upload_to_postiz(file_path: str) -> Union[dict, None]:
    """Upload a file to Postiz and return full response with id, path, etc."""
    with open(file_path, "rb") as f:
        r = requests.post(
            f"{POSTIZ_BASE}/upload",
            headers={"Authorization": POSTIZ_API_KEY},
            files={"file": (os.path.basename(file_path), f, "image/jpeg")},
            timeout=60,
        )
    if r.status_code not in (200, 201):
        print(f"❌ Upload failed for {file_path}: {r.status_code} {r.text}")
        return None
    return r.json()


import random

CAPTIONS = [
    "help me decide 😭 style 1, 2, 3, or 4??",
    "which one is your favorite? (i can't choose!)",
    "1, 2, 3, or 4? 👇 be honest!!",
    "struggling to choose... thoughts?? 🤔",
    "picking a style is hard 😅 help me out!",
    "interior design magic ✨ which do you like best?",
    "let me know what you think in the comments!!",
    "transforming this space... need ideas ASAP 🏠",
    "which one's the best?? (4 is my fav 😍)",
    "omg i love them all... which is your top pick?",
    "help!! i need to pick a style today 🕒",
    "rate these transformations 1-10 👇",
    "stuck between 2 and 3... what do you think?",
    "renovation plans! 🛠️ which vibe wins?",
    "dream home vibes ✨ pick your favorite!",
    "honestly obsessed with 3, but what about you?",
    "calling all designers!! which style works best?",
    "i'm so torn 😩 help me pick a design!",
    "can't decide on the vibe... 1 or 4??",
]


def post_carousel_to_tiktok(
    image_refs: list[dict], integration_id: str, caption: str = "", debug: bool = False
) -> bool:
    """Post carousel to TikTok as SELF_ONLY, scheduled 2 min from now."""
    schedule_time = (
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=2)
    )
    # Format date without timezone suffix to match Postiz expected format
    date_str = schedule_time.strftime("%Y-%m-%dT%H:%M:%S")

    content = caption or random.choice(CAPTIONS)

    # Matches working Postiz format exactly; image ids come from upload response
    payload = {
        "type": "schedule",
        "tags": [],
        "shortLink": False,
        "date": date_str,
        "posts": [
            {
                "integration": {"id": integration_id},
                "group": generate(ALPHABET, 10),
                "settings": {
                    "privacy_level": "SELF_ONLY",
                    "content_posting_method": "UPLOAD",
                    "autoAddMusic": "yes",
                    "comment": True,
                    "duet": False,
                    "stitch": False,
                    "video_made_with_ai": False,
                    "disclose": False,
                    "brand_organic_toggle": False,
                    "brand_content_toggle": False,
                    "title": "",
                },
                "value": [
                    {
                        "id": image_refs[0]["id"],
                        "content": f"<p>{content}</p>",
                        "delay": 0,
                        "image": image_refs,
                    }
                ],
            }
        ],
    }
    # ensure_ascii=False so emoji 😭 is sent as literal character, not \ud83d\ude2d
    body = json.dumps(payload, ensure_ascii=False, default=str)

    if debug:
        print("\n--- Request payload (matches Postiz format) ---\n")
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        print("\n--- End payload ---\n")

    r = requests.post(
        f"{POSTIZ_BASE}/posts",
        headers={
            "Authorization": POSTIZ_API_KEY,
            "Content-Type": "application/json",
        },
        data=body.encode("utf-8"),
        timeout=60,
    )
    if r.status_code not in (200, 201):
        print(f"❌ Failed to post to TikTok: {r.status_code} {r.text}")
        return False
    print(f"✅ Carousel scheduled for {schedule_time.strftime('%H:%M:%S UTC')} (2 min from now)")
    print("   It will post to TikTok as SELF_ONLY. Change visibility when ready to publish.")
    return True


def upload_carousel(slide_paths: list[str], debug: bool = False) -> bool:
    """Upload slide images to TikTok as draft carousel. Returns True on success."""
    if not slide_paths:
        print("❌ No slides to upload.")
        return False

    print("\n📤 Uploading to Postiz...")
    image_refs = []
    for p in slide_paths:
        if not os.path.exists(p):
            print(f"❌ Slide not found: {p}")
            return False
        ref = upload_to_postiz(p)
        if not ref:
            return False
        image_refs.append({
            "id": ref["id"],
            "path": ref["path"],
            "alt": None,
            "thumbnail": None,
            "thumbnailTimestamp": None,
        })

    return post_carousel_to_tiktok(image_refs, TIKTOK_INTEGRATION_ID, debug=debug)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Upload carousel slides to TikTok as draft via Postiz"
    )
    parser.add_argument(
        "slides",
        nargs="*",
        help="Paths to slide images (slide_1.jpg, slide_2.jpg, ...)",
    )
    parser.add_argument(
        "--from-dir",
        help="Use all .jpg files from this directory (sorted)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print the exact JSON payload sent to Postiz",
    )
    args = parser.parse_args()

    if args.from_dir:
        dir_path = Path(args.from_dir)
        if not dir_path.is_dir():
            print(f"❌ Not a directory: {args.from_dir}")
            sys.exit(1)
        slide_paths = sorted(dir_path.glob("slide_*.jpg"), key=lambda p: p.name)
        slide_paths = [str(p) for p in slide_paths]
    else:
        slide_paths = args.slides

    success = upload_carousel(slide_paths, debug=args.debug)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
