# Story Carousel GitHub Actions Workflow

**Date:** 2026-05-21  
**Status:** Approved

## Goal

Add a second scheduled GitHub Actions workflow that runs the existing story pipeline (`--custom`) and uploads carousels to @stacy.designs, without changing the existing fill workflow for @kim.designs8.

## Requirements

- Use existing story mode prompts and pipeline (`python main.py --custom -y`)
- Upload to TikTok account `6a0f1fde520992756d93d5dc` (@stacy.designs)
- Same schedule as fill workflow: 11:00 AM and 4:00 PM Eastern
- Leave fill workflow and Kim account default behavior unchanged
- Parameterize TikTok account ID via CLI flag (approach 1)

## Architecture

| | Fill (existing) | Story (new) |
|---|---|---|
| Workflow | `fill-carousel.yml` | `story-carousel.yml` |
| Command | `python main.py -f -y` | `python main.py --custom -y --tiktok-account 6a0f1fde520992756d93d5dc` |
| Account | Kim (default) | Stacy |
| Pushover | fill + story workflows | fill + story workflows |
| Concurrency | `fill-carousel` | `story-carousel` |

## Code Changes

### `upload.py`

- Rename `TIKTOK_ACCOUNT_ID` → `DEFAULT_TIKTOK_ACCOUNT_ID` (@kim.designs8)
- Add optional `account_id` parameter to `upload_carousel()` and `post_carousel_via_zernio()`
- Add `--tiktok-account` CLI flag

### `main.py`

- Add `--tiktok-account` flag
- Thread through `run_pipeline()` → `upload_carousel(account_id=...)`

### `.github/workflows/story-carousel.yml`

- New workflow mirroring fill-carousel structure
- Runs story pipeline with Stacy account ID

## Secrets

No new secrets. Reuses `GEMINI_API_KEY`, `ZERNIO_API_KEY`, `PUSHOVER_API_KEY`, `PUSHOVER_USER_KEY`.

## Testing

- Local dry run: `python main.py --custom -y --tiktok-account 6a0f1fde520992756d93d5dc`
- Manual workflow dispatch in GitHub Actions after merge to `main`
