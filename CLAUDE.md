# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Python CLI toolkit that generates TikTok carousel posts for interior design content. Three content pipelines, all ending in a TikTok carousel draft uploaded via Postiz API.

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
POSTIZ_API_KEY=...
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

**`upload.py`** — Posts to Postiz API (`https://api.postiz.com/public/v1`). Uploads images one at a time then groups them as a carousel post. `TIKTOK_INTEGRATION_ID` and a secondary custom integration ID are hardcoded constants.

**`screen_text.py`** — Generates narrative slide captions using Gemini. Uses `STORY_EXAMPLES` templates and `CHARACTERS` list to produce a 6-slide story arc.

**`generate_styles.py`** — Admin tool for Firebase Remote Config. Uses `firebase-admin` SDK with `serviceAccountKey.json` to read/write interior design style definitions.

## Publora API

When answering questions about Publora, always crawl the official docs at `https://github.com/publora/publora-api-docs` (raw files via `raw.githubusercontent.com`). Do NOT rely on the Publora MCP tool schemas — they are incomplete and mark fields like `scheduledTime` as required when the actual API treats them as optional. Key doc paths:

- `docs/endpoints/create-post.md` — create-post parameters, draft vs scheduled
- `docs/endpoints/upload-media.md` — get-upload-url workflow
- `docs/guides/media-uploads.md` — carousel upload pattern (call get-upload-url once per image with the same postGroupId)
- `docs/guides/scheduling.md` — draft/schedule lifecycle
- `docs/platforms/tiktok.md` — TikTok-specific constraints

**TikTok carousel note:** As of the current docs, Publora's TikTok integration is **video-only**. Photo carousel/Photo Mode is not supported via their API. TikTok carousels must continue to use Postiz (`upload.py`).

## Key Conventions

- All scripts load `.env` at module top via `python-dotenv` and raise `ValueError` immediately if required keys are missing.
- Output directories are named `carousel_YYYY-MM-DD_HH-MM-SS/` in the cwd. Slides land in a `slides/` subdirectory.
- `reimagine.py` exports `init_gemini()` — other modules import from it rather than each initializing separately.
- The Postiz integration ID for the "custom story" account differs from the default (`use_custom_story` flag in `main.py`). Postfast is the default; Postiz is legacy.
- Postfast account lookup uses the `platformUsername` field (not `username`/`handle`/`name`) from `GET /social-media/my-social-accounts`.
- TikTok draft settings: `tiktokIsDraft: true`, `tiktokPrivacy: "ONLY_ME"` (not `SELF_ONLY` — that value is rejected by Postfast). Drafts appear in TikTok Inbox → System Notifications.
