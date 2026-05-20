# Staged AI - Repository Usage Guide

Tools to generate, reimagine, and upload interior design content for TikTok.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Configuration**: Create a `.env` file:
   ```env
   GEMINI_API_KEY=your_gemini_key
   POSTIZ_API_KEY=your_postiz_key
   ```
   *(Note: `generate_styles.py` also requires `serviceAccountKey.json` for Firebase)*

---

## Content Pipelines

There are three content formats, each with a different starting image and reimagine strategy.

### Pipeline 1 — Style Reimagine (default)

A photo of a lived-in room, reimagined in 5 distinct interior design styles. The hook is "what if this room looked completely different?"

```
original.py (no flag)  →  main.py <image>
```

```bash
# Step 1: generate source image (or bring your own)
python original.py
python original.py -n 3        # generate 3 to pick from

# Step 2: run pipeline
python main.py original_room_<timestamp>.png
python main.py original_room_<timestamp>.png -y   # skip approval prompts
```

---

### Pipeline 2 — Story (--custom)

Same as Pipeline 1, but slide captions are AI-generated narrative text — the format is someone showing a skeptical family member (mom, dad, roommate) the AI redesigns. One style doesn't land, one does.

```
original.py (no flag)  →  main.py <image> --custom
```

```bash
# Step 1: generate source image (or bring your own)
python original.py

# Step 2: run pipeline with story captions
python main.py original_room_<timestamp>.png --custom
```

---

### Pipeline 3 — Fill Ideas (-f)

A photo of an awkward, undefined nook or empty corner shown next to 5 creative ways to fill it. The hook is "what on earth do I do with this space?"

```
original.py --fill  →  main.py <image> -f
```

```bash
# Step 1: generate a problem-space image (or bring your own)
python original.py --fill
python original.py --fill --space confusing_alcove   # specific space type
python original.py --fill -n 3                       # 3 options to pick from
python original.py --list                            # see all space types

# Step 2: run fill pipeline
python main.py original_<space>_<timestamp>.png -f
```

---

## Auto-Generation (skip Step 1)

`main.py` can generate the source image automatically if no image path is provided:

```bash
python main.py                          # generate room → style pipeline
python main.py --custom                 # generate room → story pipeline
python main.py -f                       # generate problem space → fill pipeline
python main.py -f --space dormer_nook   # specific space → fill pipeline
python main.py -y                       # any of the above, skip all prompts
```

---

## Individual Scripts

### `original.py` — Source Image Generator

```bash
python original.py              # 1 photorealistic room (for style/story pipelines)
python original.py -n 3         # 3 rooms to pick from
python original.py --fill       # 1 random problem-space nook (for fill pipeline)
python original.py --fill --space bay_window_nook
python original.py --fill -n 3
python original.py --list       # list all problem-space types
```

### `reimagine.py` — Generation Only (no upload)

Runs only the Gemini image generation step. Useful for previewing output without creating slides or uploading.

```bash
python reimagine.py path/to/image.jpg        # style mode: 2 reimagined styles
python reimagine.py path/to/image.jpg -f     # fill mode: 3 fill ideas
```

### `upload.py` — Upload Pre-made Slides

```bash
python upload.py slide1.jpg slide2.jpg slide3.jpg
python upload.py --from-dir ./carousel_output/slides/
```

### `generate_styles.py` — Admin / Firebase Update

```bash
python generate_styles.py new_styles.txt
python generate_styles.py new_styles.txt --publish
python generate_styles.py --publish-only
```
