# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Python CLI toolkit that generates TikTok carousel posts for interior design content. Three content pipelines, all ending in a TikTok carousel draft uploaded via Zernio API.

## Content Pipelines

**Pipeline 1 — Style** (default): A lived-in room reimagined in 5 interior design styles.
```
original.py (no flag)  →  main.py <image>
```

**Pipeline 2 — Story** (`--custom`): Same as Style, but AI-generated narrative captions frame it as showing a skeptical family member the redesigns.
```
original.py (no flag)  →  main.py <image> --custom
```

**Pipeline 3 — Fill** (`-f`): An awkward empty nook shown with 5 creative fill ideas.
```
original.py --fill  →  main.py <image> -f
```

## Setup

```bash
pip install -r requirements.txt
```

Required `.env`:
```
GEMINI_API_KEY=...
ZERNIO_API_KEY=...
```

`generate_styles.py` additionally needs `serviceAccountKey.json` for Firebase.

## Running Scripts

```bash
# Style pipeline
python original.py                        # Generate photorealistic room source image
python main.py path/to/image.jpg          # Run style pipeline

# Story pipeline  
python original.py                        # Same source image as style
python main.py path/to/image.jpg --custom # Run with AI narrative captions

# Fill pipeline
python original.py --fill                 # Generate problem-space nook image
python original.py --fill --space bay_window_nook
python original.py --fill -n 3            # 3 images to pick from
python original.py --list                 # List all available space types
python main.py path/to/nook.jpg -f        # Run fill pipeline

# Auto-generate source image (skip original.py step)
python main.py                            # Auto-generate room → style
python main.py --custom                   # Auto-generate room → story
python main.py -f                         # Auto-generate nook → fill
python main.py -f --space confusing_alcove

# Utilities
python main.py path/to/image.jpg -y       # Skip approval prompts
python reimagine.py path/to/image.jpg     # Generation only (no upload)
python upload.py slide1.jpg slide2.jpg    # Upload pre-made images
python upload.py --from-dir ./slides/
python upload.py --fill --from-dir ./slides/  # Fill title/description pool
python generate_styles.py new_styles.txt  # Add styles to Firebase
```

## Architecture

**`main.py`** — Orchestrator. Calls `reimagine → edit → upload` in sequence with user confirmation gates between stages. Handles `--custom`/`--story` flags for AI-generated captions via `screen_text.py`. When no image is provided, auto-generates a source via `original.py` — photorealistic room for style/story, problem space for fill.

**`original.py`** — Source image generator with two modes:
- Default (no flag): generates a candid photo of a lived-in, average home interior (input for style/story pipelines).
- `--fill` (`-f`): generates a photorealistic awkward nook or empty corner from `SPACE_TYPES` (input for fill pipeline). `SPACE_TYPES` dict defines all available problem-space categories.
- `generate_original(client, output_path, fill_mode=False, space_type=None)` — callable from main.py.

**`reimagine.py`** — Gemini image generation. `init_gemini()` returns a client reused across modules. `run_reimagine_for_carousel()` returns `(orig_path, item_paths_dict)` where dict maps style name → image path. Runs generations in parallel via `concurrent.futures`.

**`edit.py`** — Pillow-based overlay. Composites `circle.png` on slide 1 and renders text with `TikTokSans-Regular.ttf`. Output is 1080×1920 (9:16 TikTok). Assets (`circle.png`, font file) must stay in the repo root alongside `edit.py`.

**`upload.py`** — Posts to Zernio API (`https://zernio.com/api/v1`). Uploads each slide via `POST /v1/media/upload-direct`, then creates a scheduled TikTok photo carousel with `tiktokSettings.draft: true`. Account ID is hardcoded (`TIKTOK_ACCOUNT_ID`). Prefetches creator info via `GET /v1/accounts/{id}/tiktok/creator-info?mediaType=photo` to validate privacy levels.

**`screen_text.py`** — Generates narrative slide captions using Gemini. Uses `STORY_EXAMPLES` templates and `CHARACTERS` list to produce a 6-slide story arc.

**`generate_styles.py`** — Admin tool for Firebase Remote Config. Uses `firebase-admin` SDK with `serviceAccountKey.json` to read/write interior design style definitions.

## Zernio API

TikTok integration docs: `docs/ZERNIO_DOCS.md` and https://docs.zernio.com/llms-full.txt

Key endpoints used by `upload.py`:
- `POST /v1/media/upload-direct` — Bearer auth, multipart `file` field, returns public `url`
- `GET /v1/accounts/{accountId}/tiktok/creator-info?mediaType=photo` — allowed privacy levels
- `POST /v1/posts` — photo carousel with `tiktokSettings.draft: true`, `scheduledFor` (+2 min)

TikTok photo carousel fields:
- Top-level `content` — photo title (90 chars max; hashtags stripped by TikTok)
- `tiktokSettings.description` — full caption (up to 4,000 chars)
- `tiktokSettings.privacy_level` — `PUBLIC_TO_EVERYONE` when allowed
- `tiktokSettings.draft: true` — sends to TikTok Creator Inbox (not Zernio dashboard-only draft)
- `tiktokSettings.auto_add_music: true` — recommended music on photo carousels

## Key Conventions

- All scripts load `.env` at module top via `python-dotenv` and raise `ValueError` immediately if required keys are missing.
- Output directories are named `carousel_YYYY-MM-DD_HH-MM-SS/` in the cwd. Slides land in a `slides/` subdirectory.
- `reimagine.py` exports `init_gemini()` — other modules import from it rather than each initializing separately.
- TikTok drafts appear in TikTok Inbox → System Notifications after Zernio processes the scheduled post.
