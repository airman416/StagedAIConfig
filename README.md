# Staged AI - Repository Usage Guide

This repository contains tools to generate, reimagine, and upload interior design content for TikTok.

## 🛠️ Setup

1. **Environment**: Ensure you have Python 3.10+ installed.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configuration**: Create a `.env` file with the following keys:
   ```env
   GEMINI_API_KEY=your_gemini_key
   POSTIZ_API_KEY=your_postiz_key
   ```
   *(Note: `generate_styles.py` also requires `serviceAccountKey.json` for Firebase)*

---

## 🚀 Scripts Overview

### 1. `main.py` (The All-in-One Pipeline)
**Use this for the daily workflow.** It runs the full process: Reimagine -> Edit (Overlays) -> Upload to TikTok.

**Usage:**
```bash
# Standard Mode: Reimage a room in 5 different interior styles
python main.py path/to/image.jpg

# Automatic Mode: Generate a random "problem space" image first, then run pipeline
python main.py

# Automatic Mode (Specific Space): Generate an "alcove" image first
python main.py --space alcove

# Fill Mode: Brainstorm 5 ways to fill an empty space
python main.py path/to/empty_space.jpg -f

# Skip prompts (Auto-confirm)
python main.py path/to/image.jpg -y
```

### 2. `original.py` (Source Image Generator)
Generates photorealistic "problem space" images (empty corners, attics, etc.) to use as input for `main.py`.

**Usage:**
```bash
# Generate 1 random empty space image
python original.py

# Generate a specific type (e.g., attic_nook, alcove)
python original.py --space attic_nook

# Generate 3 images
python original.py -n 3

# List all available space types
python original.py --list
```

### 3. `reimagine.py` (Generation Only)
Runs only the generation step (Gemini). Useful for testing prompts or concepts without creating final slides/uploading.

**Modes:**
*   **Standard Mode (No flag):** Completely transforms the room's interior design style (e.g., changes the vibe to "Modern Minimalist" or "Industrial Chic") while keeping the structural shell (walls, windows) intact.
*   **Fill Mode (`-f`):** Keeps the existing room style but fills empty spaces with specific furniture or decor concepts (e.g., "Add a cozy reading nook" or "Install a home bar").

**Usage:**
```bash
# Standard Mode: Reimagine in 2 styles
python reimagine.py path/to/image.jpg

# Fill Mode: Brainstorm 3 fill ideas
python reimagine.py path/to/image.jpg -f
```

### 4. `upload.py` (Upload Only)
Uploads pre-made images to TikTok as a draft carousel via Postiz.

**Usage:**
```bash
# Upload specific files
python upload.py slide1.jpg slide2.jpg slide3.jpg

# Upload all .jpg files from a directory (sorted by name)
python upload.py --from-dir ./carousel_output/slides/
```

### 5. `generate_styles.py` (Admin / DB Update)
Used to research and add new interior design styles to the Firebase Remote Config database.

**Usage:**
```bash
# Generate new styles from a text file (one style per line)
python generate_styles.py new_styles.txt

# Generate AND publish to Firebase
python generate_styles.py new_styles.txt --publish

# Publish existing config only (no generation)
python generate_styles.py --publish-only
```
