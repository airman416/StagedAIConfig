#!/usr/bin/env python3
"""
Image Editing for Carousel Slides

Applies text and circle overlays to reimagine output:
- Slide 1: Original + circle.png centered + "HELP!! what should i do with this space??" (TikTokSans-Regular.ttf)
- Slides 2-6: Reimagined image + style/idea name (lowercase, <3 words) + tagline on slide 2

Can be run standalone or imported by main.py.
"""

import os
import re
from pathlib import Path

from typing import Union
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).parent.resolve()
TIKTOK_FONT = SCRIPT_DIR / "TikTokSans-Regular.ttf"
CIRCLE_OVERLAY = SCRIPT_DIR / "circle.png"
TARGET_SIZE = (1080, 1920)  # 9:16 for TikTok

# Emoji font paths (try in order); Apple Color Emoji uses size 32, 40, 48, 64
EMOJI_FONT_PATHS = [
    "/System/Library/Fonts/Apple Color Emoji.ttc",  # macOS
    "/System/Library/Fonts/Apple Color Emoji.ttf",
    "C:/Windows/Fonts/seguiemj.ttf",  # Windows Segoe UI Emoji
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",  # Linux
]
EMOJI = "\N{WHITE HEART}"
EMOJI_FONT_SIZE = 40


def _get_emoji_font(size: int = EMOJI_FONT_SIZE):
    """Load emoji-capable font at specified size. Returns None if unavailable."""
    for path in EMOJI_FONT_PATHS:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return None


EMOJI_PATTERN = re.compile(r'([\U00010000-\U0010ffff\u2600-\u27bf\u2b50\u2b55\u231a\u231b\u23e9-\u23f3\u23f8-\u23fa\U0001f000-\U0001ffff])', flags=re.UNICODE)


def _font_line_height(font: ImageFont.FreeTypeFont) -> int:
    """Return a consistent line height for a font using its metrics (ascent + descent).
    This is the same for every line regardless of which glyphs are present."""
    ascent, descent = font.getmetrics()
    return ascent + descent


def draw_text_centered_mixed(
    draw: ImageDraw.Draw,
    text: str,
    font: ImageFont.FreeTypeFont,
    emoji_font: Union[ImageFont.FreeTypeFont, None],
    top_y: int,
    target_width: int,
    fill="white",
    stroke_width=0,
    stroke_fill=None,
):
    """
    Draws one line of text centered horizontally.
    top_y is the y coordinate passed directly to draw.text (the font's anchor point).
    Accounts for left-bearing offset so the visual center matches the screen center.
    """
    if not emoji_font:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        # Subtract left bearing so the visible pixels are truly centered
        tx = (target_width - tw) // 2 - bbox[0]
        draw.text((tx, top_y), text, fill=fill, font=font, stroke_width=stroke_width, stroke_fill=stroke_fill)
        return

    # Split into emoji / non-emoji segments
    parts = EMOJI_PATTERN.split(text)

    total_w = 0
    render_tasks = []

    for part in parts:
        if not part:
            continue
        is_emoji = bool(EMOJI_PATTERN.fullmatch(part))
        f = emoji_font if is_emoji else font
        bbox = draw.textbbox((0, 0), part, font=f)
        w = bbox[2] - bbox[0]
        total_w += w
        render_tasks.append((part, f, is_emoji, bbox[0]))

    # Start x so that the total visible span is centered
    current_x = (target_width - total_w) // 2
    for part, f, is_emoji, left_bearing in render_tasks:
        draw_x = current_x - left_bearing
        if is_emoji:
            draw.text((draw_x, top_y), part, font=f, embedded_color=True)
        else:
            draw.text((draw_x, top_y), part, fill=fill, font=f, stroke_width=stroke_width, stroke_fill=stroke_fill)
        bbox = draw.textbbox((0, 0), part, font=f)
        current_x += bbox[2] - bbox[0]


def shorten_name(name: str, max_words: int = 3) -> str:
    """Shorten style/idea name to max_words, lowercase."""
    words = name.strip().split()[:max_words]
    return " ".join(words).lower()


def ensure_transparency(img: Image.Image) -> Image.Image:
    """If image has no alpha, create one (black = transparent for overlay)."""
    if img.mode == "RGBA":
        return img
    img = img.convert("RGBA")
    data = img.getdata()
    new_data = []
    for item in data:
        r, g, b = item[:3]
        if r < 30 and g < 30 and b < 30:
            new_data.append((r, g, b, 0))
        else:
            new_data.append((r, g, b, 255))
    img.putdata(new_data)
    return img


def create_slide_1(original_path: str, output_path: str, text: Union[str, None] = None) -> str:
    """
    Slide 1: Original + circle overlay centered + text (default: "HELP!!...") centered.
    """
    base = Image.open(original_path).convert("RGBA").resize(TARGET_SIZE, Image.Resampling.LANCZOS)

    # Overlay circle centered (0.9 = 90% of frame for bigger circle)
    if CIRCLE_OVERLAY.exists():
        circle = Image.open(CIRCLE_OVERLAY)
        circle = ensure_transparency(circle)
        scale = min(TARGET_SIZE[0] * 0.9 / circle.width, TARGET_SIZE[1] * 0.9 / circle.height)
        new_w = int(circle.width * scale)
        new_h = int(circle.height * scale)
        circle = circle.resize((new_w, new_h), Image.Resampling.LANCZOS)
        cx = (TARGET_SIZE[0] - new_w) // 2
        cy = (TARGET_SIZE[1] - new_h) // 2
        base.paste(circle, (cx, cy), circle)

    # Add text centered (two lines)
    try:
        font = ImageFont.truetype(str(TIKTOK_FONT), 72)
    except OSError:
        font = ImageFont.load_default()

    draw = ImageDraw.Draw(base)
    
    if text:
        # Accept both literal \n (from captions set in code) and escaped \\n (from LLM output)
        normalized = text.replace("\\n", "\n")
        lines = [l for l in normalized.split("\n") if l.strip()]
    else:
        lines = ["HELP!! what should i do", "with this space??"]

    LINE_GAP = 16
    line_h = _font_line_height(font)
    n = len(lines)
    total_h = n * line_h + (n - 1) * LINE_GAP
    start_y = (TARGET_SIZE[1] - total_h) // 2

    emoji_font = _get_emoji_font(72)

    for line in lines:
        draw_text_centered_mixed(
            draw, line, font, emoji_font, start_y, TARGET_SIZE[0],
            stroke_width=5, stroke_fill="black"
        )
        start_y += line_h + LINE_GAP

    base = base.convert("RGB")
    base.save(output_path, "JPEG", quality=95)
    return output_path


def create_item_slide(
    reimagined_path: str, item_name: str, output_path: str, include_tagline: bool = True, force_text: Union[str, None] = None
) -> str:
    """
    Slides 2-6: Reimagined image + style/idea name (lowercase, <3 words) + optional tagline.
    If force_text is provided, use it verbatim (supports newlines).
    """
    base = Image.open(reimagined_path).convert("RGB").resize(TARGET_SIZE, Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(base)

    short_name = shorten_name(item_name)
    try:
        font_large = ImageFont.truetype(str(TIKTOK_FONT), 72)
        font_small = ImageFont.truetype(str(TIKTOK_FONT), 36)
    except OSError:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    tagline_text = "i made these images with the staged ai app "
    tagline_full = f"{tagline_text}{EMOJI}"
    tagline_fallback = f"{tagline_text}\u2661"  # ♡ if emoji font unavailable

    if force_text:
        full_text = force_text.replace("\\n", "\n")
    else:
        full_text = f"{short_name}\n{tagline_full}" if include_tagline else short_name

    emoji_font = _get_emoji_font()

    lines = full_text.split("\n")

    LINE_GAP = 24
    TAGLINE_EXTRA_OFFSET = 48  # extra space pushed down before the tagline
    line_h_large = _font_line_height(font_large)
    line_h_small = _font_line_height(font_small)

    line_heights = []
    for line in lines:
        is_tagline = (line == tagline_full or line == tagline_fallback) and not force_text
        line_heights.append(line_h_small if is_tagline else line_h_large)

    # Account for the extra tagline offset in total height so the block stays centered
    tagline_extra = TAGLINE_EXTRA_OFFSET if (not force_text and len(lines) > 1) else 0
    n = len(lines)
    total_h = sum(line_heights) + (n - 1) * LINE_GAP + tagline_extra
    start_y = (TARGET_SIZE[1] - total_h) // 2

    current_emoji_font = _get_emoji_font(72)

    for i, line in enumerate(lines):
        is_tagline = (line == tagline_full or line == tagline_fallback) and not force_text
        if is_tagline:
            start_y += TAGLINE_EXTRA_OFFSET

        if is_tagline and emoji_font and line == tagline_full:
            b_text = draw.textbbox((0, 0), tagline_text, font=font_small)
            b_emoji = draw.textbbox((0, 0), EMOJI, font=emoji_font)
            tw_text = b_text[2] - b_text[0]
            tw_emoji = b_emoji[2] - b_emoji[0]
            total_w = tw_text + tw_emoji
            tx = (TARGET_SIZE[0] - total_w) // 2 - b_text[0]
            draw.text((tx, start_y), tagline_text, fill="white", font=font_small, stroke_width=5, stroke_fill="black")
            draw.text((tx + tw_text, start_y), EMOJI, font=emoji_font, embedded_color=True)

        elif is_tagline:
            b = draw.textbbox((0, 0), tagline_fallback, font=font_small)
            tw = b[2] - b[0]
            tx = (TARGET_SIZE[0] - tw) // 2 - b[0]
            draw.text((tx, start_y), tagline_fallback, fill="white", font=font_small, stroke_width=5, stroke_fill="black")

        else:
            draw_text_centered_mixed(
                draw, line, font_large, current_emoji_font, start_y, TARGET_SIZE[0],
                stroke_width=5, stroke_fill="black"
            )

        start_y += line_heights[i] + LINE_GAP

    base.save(output_path, "JPEG", quality=95)
    return output_path


def edit_carousel(
    original_path: str,
    item_paths: dict[str, str],
    output_dir: Union[str, Path],
    captions: list[str] = None,
    fill_mode: bool = False,
) -> list[str]:
    """
    Create 6 carousel slides from original + reimagined images.
    Applies circle overlay and text as per spec.
    Returns list of slide file paths.
    """
    output_dir = Path(output_dir)
    slides_dir = output_dir / "slides"
    slides_dir.mkdir(parents=True, exist_ok=True)

    slide_paths = []

    # Slide 1: Original + circle + "HELP!! what should i do with this space??"
    slide_1 = slides_dir / "slide_1.jpg"
    
    # Use captions[0] if available
    s1_text = captions[0] if captions and len(captions) > 0 else None
    create_slide_1(original_path, str(slide_1), text=s1_text)
    slide_paths.append(str(slide_1))

    # Slides 2-6: Reimagined + style/idea name + tagline on first
    for i, (item_name, path) in enumerate(item_paths.items()):
        out = slides_dir / f"slide_{i + 2}.jpg"
        
        # Use captions[i+1] if available (captions index 1 corresponds to slide 2, i=0)
        c_idx = i + 1
        force_txt = captions[c_idx] if captions and len(captions) > c_idx else None
        
        # In non-fill mode, append "Staged AI" to the last slide.
        # In fill mode, just show the fill idea name as normal.
        if i == len(item_paths) - 1 and not fill_mode:
            cta = "Staged AI"
            if force_txt:
                if cta.lower() not in force_txt.lower():
                    force_txt = f"{force_txt}\n\n\n{cta}"
            else:
                force_txt = cta

        create_item_slide(path, item_name, str(out), include_tagline=(i == 0), force_text=force_txt)
        slide_paths.append(str(out))

    # Pad to 6 slides if needed
    while len(slide_paths) < 6 and item_paths:
        last_name = list(item_paths.keys())[-1]
        last_path = item_paths[last_name]
        idx = len(slide_paths) + 1
        out = slides_dir / f"slide_{idx}.jpg"
        
        # Check if we have a caption for this padded slide
        c_idx = idx - 1 # slide 1 is index 0
        force_txt = captions[c_idx] if captions and len(captions) > c_idx else None
        
        if idx == 6 and not fill_mode:
            cta = "Staged AI"
            if force_txt:
                if cta.lower() not in force_txt.lower():
                    force_txt = f"{force_txt}\n\n\n{cta}"
            else:
                force_txt = cta

        create_item_slide(last_path, last_name, str(out), include_tagline=False, force_text=force_txt)
        slide_paths.append(str(out))

    return slide_paths[:6]


def main():
    """
    CLI for editing pre-generated reimagine output.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Apply text/circle overlays to reimagine output for carousel"
    )
    parser.add_argument("original_path", help="Path to original.png (9:16 regenerated)")
    parser.add_argument("output_dir", help="Output directory (will create slides/ subfolder)")
    parser.add_argument(
        "item_paths",
        nargs="+",
        help="Pairs of 'name:path' for reimagined images (e.g. 'Modern Minimalist:./modern_minimalist.png')",
    )
    args = parser.parse_args()

    item_paths = {}
    for pair in args.item_paths:
        if ":" in pair:
            name, path = pair.split(":", 1)
            item_paths[name.strip()] = path.strip()
        else:
            print(f"⚠️  Skipping invalid pair: {pair}")

    if not item_paths:
        print("❌ No valid item paths provided.")
        return 1

    slides = edit_carousel(args.original_path, item_paths, args.output_dir)
    print(f"✅ Created {len(slides)} slides in {Path(args.output_dir) / 'slides'}")
    for s in slides:
        print(f"  - {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
