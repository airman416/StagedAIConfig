#!/usr/bin/env python3
"""
TikTok Carousel Upload

Uploads carousel slides to TikTok as DRAFT via Postiz API.
Expects pre-edited slide images (from edit.py).

Usage:
  python upload.py <slide1.jpg> <slide2.jpg> ...
  python upload.py --from-dir ./carousel_xxx/slides/
"""

import os
import sys
import datetime
from pathlib import Path

from dotenv import load_dotenv
import requests

load_dotenv()

POSTIZ_API_KEY = os.getenv("POSTIZ_API_KEY")
if not POSTIZ_API_KEY:
    raise ValueError("POSTIZ_API_KEY not found in .env")

POSTIZ_BASE = "https://api.postiz.com/public/v1"
TIKTOK_INTEGRATION_ID = "cmljzps6w01xzol0y7l9889vh"


def upload_to_postiz(file_path: str) -> dict | None:
    """Upload a file to Postiz and return {id, path}."""
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


def post_carousel_to_tiktok(
    image_refs: list[dict], integration_id: str, caption: str = ""
) -> bool:
    """Post carousel to TikTok as a private post (SELF_ONLY via DIRECT_POST)."""
    # type: "schedule" -> Postiz sends at the scheduled time
    # DIRECT_POST     -> actually pushes to TikTok
    # SELF_ONLY       -> only you can see it on TikTok
    schedule_time = (
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=2)
    )
    payload = {
        "type": "schedule",
        "date": schedule_time.isoformat().replace("+00:00", "Z"),
        "shortLink": False,
        "tags": [],
        "posts": [
            {
                "integration": {"id": integration_id},
                "value": [
                    {
                        "content": caption
                        or "help me decide 🥺\n\n#interiordesign #fyp #homedecor",
                        "image": image_refs,
                    }
                ],
                "settings": {
                    "__type": "tiktok",
                    "title": "help me decide 🥺",
                    "privacy_level": "SELF_ONLY",
                    "duet": False,
                    "stitch": False,
                    "comment": True,
                    "autoAddMusic": "no",
                    "brand_content_toggle": False,
                    "brand_organic_toggle": False,
                    "video_made_with_ai": True,
                    "content_posting_method": "DIRECT_POST",
                },
            }
        ],
    }
    r = requests.post(
        f"{POSTIZ_BASE}/posts",
        headers={
            "Authorization": POSTIZ_API_KEY,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    if r.status_code not in (200, 201):
        print(f"❌ Failed to post to TikTok: {r.status_code} {r.text}")
        return False
    print(f"✅ Carousel scheduled for {schedule_time.strftime('%H:%M:%S UTC')} (2 min from now)")
    print("   It will post to TikTok as SELF_ONLY. Change visibility when ready to publish.")
    return True


def upload_carousel(slide_paths: list[str]) -> bool:
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
        image_refs.append({"id": ref["id"], "path": ref["path"]})

    return post_carousel_to_tiktok(image_refs, TIKTOK_INTEGRATION_ID)


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

    success = upload_carousel(slide_paths)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
