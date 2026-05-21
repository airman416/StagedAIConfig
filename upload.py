#!/usr/bin/env python3
"""
TikTok Carousel Upload

Uploads carousel slides to TikTok as a photo carousel draft via Zernio API.
Drafts land in TikTok Inbox → System Notifications (public visibility when published).

Usage:
  python upload.py <slide1.jpg> <slide2.jpg> ...
  python upload.py --from-dir ./carousel_xxx/slides/
  python upload.py --fill slide1.jpg ...   # use fill-pipeline title/description pool
"""

import json
import os
import random
import sys
import datetime
import uuid
from pathlib import Path
from typing import Union

from dotenv import load_dotenv
import requests

load_dotenv()

ZERNIO_API_KEY = os.getenv("ZERNIO_API_KEY")
if not ZERNIO_API_KEY:
    raise ValueError("ZERNIO_API_KEY not found in .env")

ZERNIO_BASE = "https://zernio.com/api/v1"
DEFAULT_TIKTOK_ACCOUNT_ID = "6a0dc3a8520992756d88c5ba"  # @kim.designs8
PREFERRED_PRIVACY = "PUBLIC_TO_EVERYONE"
SCHEDULE_DELAY_MINUTES = 2

# Fill pipeline: short photo title + full carousel caption (tiktokSettings.description)
FILL_CAPTIONS = [
    {
        "title": "what do I even do with this corner",
        "description": "#homedecor #interiordesign #smallspaces #roommakeover"
    },
    {
        "title": "help this random nook is stressing me out",
        "description": "#interiordesign #homeinspo #awkwardspaces #decorideas"
    },
    {
        "title": "5 ways to fix this dead space",
        "description": "#homedecor #beforeandafter #spacedesign #cozyhome"
    },
    {
        "title": "this empty corner needs a personality",
        "description": "#interiordesign #nookideas #homemakeover #designinspo"
    },
    {
        "title": "nobody talks about awkward nooks",
        "description": "#smallspaces #homedecor #roomideas #interiorstyle"
    },
    {
        "title": "I cannot leave this corner empty anymore",
        "description": "#homedecor #interiordesign #emptycorner #decor"
    },
    {
        "title": "pick a vibe for this wasted space",
        "description": "#interiordesign #homeinspo #alcove #roomrefresh"
    },
    {
        "title": "the nook that broke my brain",
        "description": "#homedecor #designhelp #smallspaceliving #interiorideas"
    },
]

# Style pipeline (non-fill uploads via upload.py CLI)
STYLE_CAPTIONS = [
    {
        "title": "help me pick a room style",
        "description": "#interiordesign #homedecor #roommakeover #designinspo"
    },
    {
        "title": "which style would you live in",
        "description": "#interiordesign #beforeandafter #homeinspo #decor"
    },
    {
        "title": "one room five totally different vibes",
        "description": "#homedecor #interiordesign #roomideas #styleinspo"
    },
    {
        "title": "I need help choosing a design direction",
        "description": "#interiordesign #homemakeover #designhelp #cozyhome"
    },
    {
        "title": "style 1 2 3 4 or 5",
        "description": "#homedecor #interiordesign #roomtransformation #aesthetic"
    },
]


def _auth_headers(extra: dict | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {ZERNIO_API_KEY}"}
    if extra:
        headers.update(extra)
    return headers


def get_tiktok_creator_info(account_id: str) -> Union[dict, None]:
    """Fetch allowed privacy levels and posting limits for a TikTok account."""
    r = requests.get(
        f"{ZERNIO_BASE}/accounts/{account_id}/tiktok/creator-info",
        params={"mediaType": "photo"},
        headers=_auth_headers(),
        timeout=30,
    )
    if r.status_code != 200:
        print(f"❌ Failed to fetch TikTok creator info: {r.status_code} {r.text}")
        return None
    return r.json()


def resolve_privacy_level(creator_info: dict) -> Union[str, None]:
    """Pick PUBLIC_TO_EVERYONE if allowed, otherwise the first available level."""
    levels = creator_info.get("privacyLevels") or creator_info.get("privacy_levels") or []
    if not levels:
        print("❌ No privacy levels returned from creator info.")
        return None
    if isinstance(levels[0], dict):
        level_values = [lv.get("value") or lv.get("name") for lv in levels]
    else:
        level_values = list(levels)
    level_values = [v for v in level_values if v]
    if PREFERRED_PRIVACY in level_values:
        return PREFERRED_PRIVACY
    print(
        f"⚠️  {PREFERRED_PRIVACY} not available for this account. "
        f"Using {level_values[0]} instead. Available: {level_values}"
    )
    return level_values[0]


def upload_media_direct(file_path: str) -> Union[str, None]:
    """Upload a local image via /v1/media/upload-direct; return the public URL."""
    with open(file_path, "rb") as f:
        r = requests.post(
            f"{ZERNIO_BASE}/media/upload-direct",
            headers=_auth_headers(),
            files={"file": (os.path.basename(file_path), f, "image/jpeg")},
            timeout=120,
        )
    if r.status_code not in (200, 201):
        print(f"❌ Media upload failed for {file_path}: {r.status_code} {r.text}")
        return None
    data = r.json()
    url = data.get("url") or data.get("publicUrl")
    if not url:
        print(f"❌ Media upload response missing URL for {file_path}: {data}")
        return None
    return url


def post_carousel_via_zernio(
    media_urls: list[str],
    title: str,
    description: str,
    privacy_level: str,
    account_id: str,
    debug: bool = False,
) -> bool:
    """Schedule a TikTok photo carousel as an inbox draft (public when published)."""
    schedule_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=SCHEDULE_DELAY_MINUTES
    )
    scheduled_for = schedule_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    payload = {
        "content": title[:90],
        "mediaItems": [{"type": "image", "url": url} for url in media_urls],
        "platforms": [{"platform": "tiktok", "accountId": account_id}],
        "tiktokSettings": {
            "privacy_level": privacy_level,
            "allow_comment": True,
            "media_type": "photo",
            "photo_cover_index": 0,
            "description": description,
            "auto_add_music": True,
            "content_preview_confirmed": True,
            "express_consent_given": True,
            "draft": True,
        },
        "scheduledFor": scheduled_for,
    }

    if debug:
        print("\n--- Zernio payload ---")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print("--- End payload ---\n")

    r = requests.post(
        f"{ZERNIO_BASE}/posts",
        headers=_auth_headers({
            "Content-Type": "application/json",
            "x-request-id": str(uuid.uuid4()),
        }),
        json=payload,
        timeout=120,
    )
    if r.status_code not in (200, 201):
        print(f"❌ Failed to post carousel via Zernio: {r.status_code} {r.text}")
        return False

    post = r.json().get("post") or r.json()
    post_id = post.get("_id") or post.get("id") or "unknown"
    print(f"✅ Carousel scheduled as TikTok inbox draft (post {post_id})")
    print(f"   Scheduled for {schedule_time.strftime('%H:%M:%S UTC')} ({SCHEDULE_DELAY_MINUTES} min from now)")
    print(f"   Privacy: {privacy_level} · Find it in TikTok Inbox → System Notifications")
    return True


def pick_caption(fill_mode: bool) -> tuple[str, str]:
    pool = FILL_CAPTIONS if fill_mode else STYLE_CAPTIONS
    choice = random.choice(pool)
    return choice["title"], choice["description"]


def upload_carousel(
    slide_paths: list[str],
    debug: bool = False,
    title: str = "",
    description: str = "",
    fill_mode: bool = False,
    account_id: str | None = None,
) -> bool:
    """Upload slides as a TikTok photo carousel draft via Zernio."""
    account_id = account_id or DEFAULT_TIKTOK_ACCOUNT_ID
    if not slide_paths:
        print("❌ No slides to upload.")
        return False

    for p in slide_paths:
        if not os.path.exists(p):
            print(f"❌ Slide not found: {p}")
            return False

    if not title or not description:
        auto_title, auto_desc = pick_caption(fill_mode)
        title = title or auto_title
        description = description or auto_desc

    print(f"\n📤 Uploading to Zernio (account {account_id})...")
    creator_info = get_tiktok_creator_info(account_id)
    if not creator_info:
        return False

    privacy_level = resolve_privacy_level(creator_info)
    if not privacy_level:
        return False

    media_urls = []
    for p in slide_paths:
        url = upload_media_direct(p)
        if not url:
            return False
        media_urls.append(url)
        print(f"   ✓ Uploaded {os.path.basename(p)}")

    return post_carousel_via_zernio(
        media_urls, title, description, privacy_level, account_id, debug=debug
    )


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Upload carousel slides to TikTok via Zernio (inbox draft)"
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
        "--fill",
        action="store_true",
        help="Use fill-pipeline title/description options",
    )
    parser.add_argument("--title", help="Photo title (max 90 chars)")
    parser.add_argument("--description", help="Full carousel caption")
    parser.add_argument(
        "--tiktok-account",
        default=DEFAULT_TIKTOK_ACCOUNT_ID,
        help="Zernio TikTok account ID (default: @kim.designs8)",
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

    success = upload_carousel(
        slide_paths,
        debug=args.debug,
        title=args.title or "",
        description=args.description or "",
        fill_mode=args.fill,
        account_id=args.tiktok_account,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
