#!/usr/bin/env python3
"""
TikTok Carousel Upload

Uploads carousel slides to TikTok as a scheduled (SELF_ONLY) post via Postfast API.
Falls back to Postiz when an explicit integration_id is provided (legacy/custom-story path).

Usage:
  python upload.py <slide1.jpg> <slide2.jpg> ...
  python upload.py --from-dir ./carousel_xxx/slides/
"""

import json
import os
import random
import sys
import datetime
from pathlib import Path
from typing import Union

from dotenv import load_dotenv
import requests
from nanoid import generate

load_dotenv()

POSTFAST_API_KEY = os.getenv("POSTFAST_API_KEY")
if not POSTFAST_API_KEY:
    raise ValueError("POSTFAST_API_KEY not found in .env")

POSTFAST_BASE = "https://api.postfa.st"
POSTFAST_CHANNEL = "kim.designs8"

# Postiz (legacy — used only when integration_id is explicitly passed)
POSTIZ_API_KEY = os.getenv("POSTIZ_API_KEY")
POSTIZ_BASE = "https://api.postiz.com/public/v1"
TIKTOK_INTEGRATION_ID = "cmljzps6w01xzol0y7l9889vh"

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

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

# ── Postfast ──────────────────────────────────────────────────────────────────

_social_media_id_cache: dict[str, str] = {}


def get_social_media_id(channel_name: str) -> Union[str, None]:
    """Return the Postfast socialMediaId for the given channel username."""
    if channel_name in _social_media_id_cache:
        return _social_media_id_cache[channel_name]
    r = requests.get(
        f"{POSTFAST_BASE}/social-media/my-social-accounts",
        headers={"pf-api-key": POSTFAST_API_KEY},
        timeout=30,
    )
    if r.status_code != 200:
        print(f"❌ Failed to fetch social accounts: {r.status_code} {r.text}")
        return None
    accounts = r.json()
    if not isinstance(accounts, list):
        accounts = accounts.get("data", [])
    for acct in accounts:
        handle = (
            acct.get("platformUsername")
            or acct.get("username")
            or acct.get("handle")
            or acct.get("name")
            or ""
        )
        if handle == channel_name:
            _social_media_id_cache[channel_name] = acct["id"]
            return acct["id"]
    names = [acct.get("platformUsername") or acct.get("username") or acct.get("handle") or acct.get("name") for acct in accounts]
    print(f"❌ No Postfast account found with username '{channel_name}'")
    print(f"   Available: {names}")
    return None


def upload_to_postfast(file_path: str) -> Union[str, None]:
    """Get a pre-signed S3 URL, upload the file, return the S3 key."""
    r = requests.post(
        f"{POSTFAST_BASE}/file/get-signed-upload-urls",
        headers={"pf-api-key": POSTFAST_API_KEY, "Content-Type": "application/json"},
        json={"contentType": "image/jpeg", "count": 1},
        timeout=30,
    )
    if r.status_code not in (200, 201):
        print(f"❌ Failed to get signed URL for {file_path}: {r.status_code} {r.text}")
        return None
    data = r.json()
    item = data[0] if isinstance(data, list) else data
    signed_url = item["signedUrl"]
    key = item["key"]

    with open(file_path, "rb") as f:
        put_r = requests.put(
            signed_url,
            data=f,
            headers={"Content-Type": "image/jpeg"},
            timeout=120,
        )
    if put_r.status_code not in (200, 204):
        print(f"❌ S3 upload failed for {file_path}: {put_r.status_code} {put_r.text}")
        return None
    return key


def post_carousel_via_postfast(
    keys: list[str],
    social_media_id: str,
    caption: str = "",
    debug: bool = False,
) -> bool:
    """Post a TikTok photo carousel via Postfast as a draft, visible only to the creator."""
    schedule_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=2)
    content = caption or random.choice(CAPTIONS)

    payload = {
        "posts": [
            {
                "content": content,
                "mediaItems": [
                    {"key": k, "type": "IMAGE", "sortOrder": i}
                    for i, k in enumerate(keys)
                ],
                "scheduledAt": schedule_time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "socialMediaId": social_media_id,
            }
        ],
        "controls": {
            "tiktokIsDraft": True,
            "tiktokPrivacy": "ONLY_ME",
            "tiktokAllowComments": True,
        },
    }

    if debug:
        print("\n--- Postfast payload ---")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print("--- End payload ---\n")

    r = requests.post(
        f"{POSTFAST_BASE}/social-posts",
        headers={"pf-api-key": POSTFAST_API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    if r.status_code not in (200, 201):
        print(f"❌ Failed to post carousel via Postfast: {r.status_code} {r.text}")
        return False

    print(f"✅ Carousel posted as draft (find it in TikTok Inbox → System Notifications)")
    return True


# ── Postiz (legacy) ───────────────────────────────────────────────────────────

def _upload_to_postiz(file_path: str) -> Union[dict, None]:
    if not POSTIZ_API_KEY:
        print("❌ POSTIZ_API_KEY not set — cannot use legacy Postiz path")
        return None
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


def _post_carousel_via_postiz(
    image_refs: list[dict], integration_id: str, caption: str = "", debug: bool = False
) -> bool:
    schedule_time = (
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=2)
    )
    date_str = schedule_time.strftime("%Y-%m-%dT%H:%M:%S")
    content = caption or random.choice(CAPTIONS)

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
    body = json.dumps(payload, ensure_ascii=False, default=str)

    if debug:
        print("\n--- Postiz payload ---")
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        print("--- End payload ---\n")

    r = requests.post(
        f"{POSTIZ_BASE}/posts",
        headers={"Authorization": POSTIZ_API_KEY, "Content-Type": "application/json"},
        data=body.encode("utf-8"),
        timeout=60,
    )
    if r.status_code not in (200, 201):
        print(f"❌ Failed to post to TikTok via Postiz: {r.status_code} {r.text}")
        return False
    print(f"✅ Carousel scheduled for {schedule_time.strftime('%H:%M:%S UTC')} (2 min from now)")
    print("   It will post to TikTok as SELF_ONLY. Change visibility when ready to publish.")
    return True


# ── Public API ────────────────────────────────────────────────────────────────

def upload_carousel(
    slide_paths: list[str],
    integration_id: str = None,
    debug: bool = False,
    caption: str = "",
) -> bool:
    """Upload slides as a TikTok photo carousel.

    Default: Postfast (kim.designs8 channel).
    Legacy: pass integration_id to route through Postiz instead.
    """
    if not slide_paths:
        print("❌ No slides to upload.")
        return False

    for p in slide_paths:
        if not os.path.exists(p):
            print(f"❌ Slide not found: {p}")
            return False

    # Legacy Postiz path (custom-story account or explicit override)
    if integration_id is not None:
        print("\n📤 Uploading to Postiz (legacy)...")
        image_refs = []
        for p in slide_paths:
            ref = _upload_to_postiz(p)
            if not ref:
                return False
            image_refs.append({
                "id": ref["id"],
                "path": ref["path"],
                "alt": None,
                "thumbnail": None,
                "thumbnailTimestamp": None,
            })
        return _post_carousel_via_postiz(image_refs, integration_id, caption=caption, debug=debug)

    # Default Postfast path
    print("\n📤 Uploading to Postfast...")
    social_media_id = get_social_media_id(POSTFAST_CHANNEL)
    if not social_media_id:
        return False

    keys = []
    for p in slide_paths:
        key = upload_to_postfast(p)
        if not key:
            return False
        keys.append(key)
        print(f"   ✓ Uploaded {os.path.basename(p)}")

    return post_carousel_via_postfast(keys, social_media_id, caption=caption, debug=debug)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Upload carousel slides to TikTok via Postfast (default) or Postiz (legacy)"
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
        help="Print the exact JSON payload sent to the API",
    )
    parser.add_argument(
        "--integration-id",
        help="Use Postiz (legacy) with this integration ID instead of Postfast",
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

    success = upload_carousel(slide_paths, integration_id=args.integration_id, debug=args.debug)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
