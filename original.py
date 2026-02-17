#!/usr/bin/env python3
"""
Original "Problem Space" Image Generator

Generates photorealistic images of lived-in homes with a specific "problem area"
-- an unused or empty spot that begs to be filled. These images serve as input
to the carousel pipeline (main.py -> reimagine -> edit -> upload).

Usage:
  python original.py                          # Random space, 1 image
  python original.py --space alcove           # Specific space type
  python original.py --count 3               # Generate 3 images to pick from
  python original.py --space attic_nook -n 3  # 3 attic nook images
  python original.py --list                   # List all space types
"""

import os
import random
import argparse
import datetime
import concurrent.futures
from pathlib import Path
from typing import Union

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in .env file.")


def init_gemini():
    """Initialize Gemini client."""
    return genai.Client(api_key=GEMINI_API_KEY)


# ---------------------------------------------------------------------------
# Space types: each entry describes the problem area AND the lived-in context
# ---------------------------------------------------------------------------

SPACE_TYPES = {
    "alcove": {
        "label": "Recessed alcove off a hallway",
        "description": (
            "A recessed alcove or nook visible from a hallway. The alcove itself "
            "is completely bare -- empty carpet or floor with nothing in it. "
            "The hallway around it looks normal: carpet, walls with doors to "
            "other rooms, baseboards, maybe a light fixture hanging above the "
            "empty alcove. A half-wall or archway frames the entrance to the nook."
        ),
    },
    "attic_nook": {
        "label": "Narrow attic nook under sloped eaves",
        "description": (
            "A narrow area under a sloped or vaulted ceiling in an attic room. "
            "The ceiling angles down, creating an intimate, challenging corridor-like "
            "space that leads to a small window at the far end. This specific area "
            "is completely unused. Nearby, at the edge of the frame, there may be "
            "a small shelf or console hinting that the rest of the room is lived-in."
        ),
    },
    "staircase_landing": {
        "label": "Open landing at the top of stairs",
        "description": (
            "The open area at the top of a staircase. The stairs and railing are "
            "visible and look normal -- the adjacent hallway has doors to bedrooms "
            "or a bathroom. But the landing itself is a generous carpeted area with "
            "absolutely nothing in it. A window or chandelier may be nearby, "
            "highlighting the unused potential of this transition space."
        ),
    },
    "built_in_shelving": {
        "label": "Wall with bare built-in niches or entertainment cutout",
        "description": (
            "A wall with built-in niches, an arched cutout, or an entertainment "
            "center recess. Every shelf and niche is completely bare. A dangling "
            "cable or a single outlet hints that a TV or equipment used to be here. "
            "The rest of the room has hardwood or carpet and looks lived-in -- "
            "maybe a cardboard box or loose cable on the floor nearby."
        ),
    },
    "bay_window_area": {
        "label": "Bay window section with no seating",
        "description": (
            "A bay window area in a living room or bedroom that has no bench, "
            "no seating, no cushions -- just bare floor in front of the windows. "
            "The windows let in natural light. The rest of the room, visible at "
            "the edges, has signs of normal life: a door frame, baseboards, "
            "maybe the edge of existing furniture barely in frame."
        ),
    },
    "under_stairs": {
        "label": "Triangular void beneath a staircase",
        "description": (
            "The triangular space underneath a staircase. The stairs above are "
            "clearly used -- you can see the underside of the steps or the wall "
            "following the stair angle. But the space beneath is completely empty "
            "and unused. The surrounding area (hallway, adjacent room) looks normal."
        ),
    },
    "bonus_room_corner": {
        "label": "Empty corner of an upstairs room",
        "description": (
            "One conspicuously bare corner of an upstairs bonus room or spare room. "
            "The corner has interesting features -- maybe a window, sloped ceiling, "
            "or an outlet suggesting something should go there. The rest of the room "
            "at the edges of the frame hints at normal use."
        ),
    },
    "sunroom": {
        "label": "Enclosed porch or sunroom, empty",
        "description": (
            "An enclosed porch or sunroom with large windows or glass panels. "
            "The room is flooded with natural light but completely empty -- bare "
            "floor, no furniture, no plants. Through the doorway behind, the "
            "adjoining room looks normal and furnished, creating contrast with "
            "this bright but unused space."
        ),
    },
    "walk_in_closet": {
        "label": "Large unused walk-in closet",
        "description": (
            "A spacious walk-in closet that's completely empty -- bare rods, "
            "empty shelves, nothing on the floor. The closet may have built-in "
            "wire shelving or wooden shelving that's all bare. Through the closet "
            "doorway, the bedroom it connects to looks normal and lived-in."
        ),
    },
    "breakfast_nook": {
        "label": "Small windowed area off a kitchen, bare",
        "description": (
            "A small windowed bump-out or nook area off a kitchen. The nook is "
            "completely bare -- no table, no chairs, just empty floor and windows "
            "letting in light. The kitchen at the edge of the frame has countertops, "
            "cabinets, maybe an appliance visible, looking normal and used."
        ),
    },
    "basement_section": {
        "label": "Finished but empty basement section",
        "description": (
            "One section of a finished basement that's completely empty. The walls "
            "are drywalled and painted, the floor is carpeted or has laminate, "
            "there may be recessed lighting overhead -- but nothing occupies the "
            "space. Adjacent areas of the basement may show a door, a utility panel, "
            "or other signs of a used home."
        ),
    },
    "entryway": {
        "label": "Foyer or mudroom, unused space",
        "description": (
            "A foyer, entryway, or mudroom near the front door. The area has "
            "interesting features -- a coat closet door, a bench area with nothing "
            "on it, hooks on the wall with nothing hanging, tile or hardwood floor. "
            "The front door or adjacent hallway is visible, and the rest of the "
            "home looks normal beyond the entryway."
        ),
    },
    "loft_area": {
        "label": "Open loft overlooking a lower floor",
        "description": (
            "An open loft area with a railing that overlooks the lower floor. "
            "The loft is completely empty -- just carpet or hardwood with a railing "
            "and maybe a window. You can see the railing and the open drop to "
            "the lower level. The lower floor, partially visible, looks lived-in."
        ),
    },
    "fireplace_wall": {
        "label": "Wall with a fireplace but nothing else",
        "description": (
            "A wall with a fireplace (gas or traditional) as its centerpiece. "
            "The mantel is bare, no art above it, no furniture flanking it -- the "
            "entire wall is empty except for the fireplace itself. The room around "
            "it is otherwise normal, with flooring, baseboards, and maybe the edge "
            "of a doorway or window visible."
        ),
    },
    "corner_of_room": {
        "label": "Conspicuously bare corner of a lived-in room",
        "description": (
            "One specific empty corner of an otherwise lived-in living room, "
            "family room, or bedroom. The corner has bare wall and floor -- maybe "
            "an outlet or a light switch on the wall hinting at intended use. "
            "The rest of the room at the edges shows signs of normal life: a door "
            "frame, the edge of a piece of furniture barely visible."
        ),
    },
}

# Architectural twists randomly added for variety
ARCHITECTURAL_TWISTS = [
    "An arched doorway or opening frames the area.",
    "Crown molding and wainscoting add character to the walls.",
    "A small decorative window or transom is above the area.",
    "The ceiling has an interesting coffered or tray detail.",
    "Exposed wooden beams cross the ceiling above the space.",
    "A built-in ledge or shelf runs along one wall but is empty.",
    "Recessed lighting in the ceiling highlights the empty area below.",
    "A column or half-wall partially separates this area from the rest.",
]


def build_prompt(space_type: str) -> str:
    """Build the image generation prompt for a given space type."""
    info = SPACE_TYPES[space_type]
    twist = random.choice(ARCHITECTURAL_TWISTS)

    return f"""Generate a photorealistic image taken inside a LIVED-IN residential home.
The camera is pointed at a specific problem area -- an unused or empty spot
within an otherwise normal, occupied home.

PERSPECTIVE & FEEL:
- Shot from a PERSONAL, CANDID angle as if a homeowner took it with their
  phone, standing a few feet away, pointing the camera at the problem area.
  Slightly off-center framing is fine.
- NOT a professional real estate wide-angle shot. NOT a render. NOT a 3D model.
- The image should feel authentic, like it was posted on social media asking
  "what should I do with this space?"

THE PROBLEM AREA (center of the image):
- {info['description']}
- {twist}
- This specific area is EMPTY and UNUSED -- it's the focal point of the photo
  and the "problem" the homeowner wants help with.
- The emptiness should feel like WASTED POTENTIAL -- the area has good bones,
  interesting architectural features, but nothing occupies it.
- The viewer should immediately think: "oh you could put X there."

THE SURROUNDINGS (edges / background):
- The rest of the visible home should look NORMAL and LIVED-IN.
- Hints of adjacent rooms, hallways, doorways, staircases, or other
  used parts of the house should be visible at the edges or background.
- Minor mundane items are OK in the surroundings (a light switch, an air vent,
  a door handle, baseboards, a cable, a small shelf) to sell the realism.
- The surroundings FRAME the problem area and draw the eye to it.

ARCHITECTURAL DETAILS:
- The problem area should have interesting features that make it compelling:
  sloped ceilings, built-in niches, half-walls, railings, arched openings,
  recessed lighting, crown molding, a light fixture, a window, etc.
- Standard American suburban home finishes (textured drywall, white trim,
  white baseboards, neutral wall colors, carpet or hardwood).

LIGHTING:
- Natural light from windows, supplemented by existing fixtures.
  Normal residential daytime lighting.

CRITICAL:
- The PROBLEM AREA itself must be empty -- no furniture or decor there.
- The SURROUNDINGS should feel lived-in and normal.
- NO people, NO pets.
- NO text, NO watermarks, NO logos.
- Portrait orientation (9:16)."""


def generate_original(client, space_type: str, output_path: str) -> Union[str, None]:
    """Generate a single original image for the given space type."""
    prompt = build_prompt(space_type)
    label = SPACE_TYPES[space_type]["label"]

    print(f"🎨 Generating: {label}...")

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="9:16",
                ),
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                img_data = part.inline_data.data
                with open(output_path, "wb") as f:
                    f.write(img_data)
                print(f"  ✅ Saved: {output_path}")
                return output_path

        print(f"  ⚠️  No image generated for {label}")
        return None

    except Exception as e:
        print(f"  ❌ Generation failed for {label}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate photorealistic 'problem space' images for the carousel pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python original.py                          # Random space type, 1 image
  python original.py --space alcove           # Generate an alcove image
  python original.py --count 3               # Generate 3 random images
  python original.py --space attic_nook -n 3  # 3 attic nook images
  python original.py --list                   # Show all space types
        """,
    )
    parser.add_argument(
        "--space",
        choices=list(SPACE_TYPES.keys()),
        default=None,
        help="Space type to generate (random if not specified)",
    )
    parser.add_argument(
        "-n", "--count",
        type=int,
        default=1,
        help="Number of images to generate (default: 1)",
    )
    parser.add_argument(
        "-o", "--output-dir",
        default=".",
        help="Directory to save images (default: current directory)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available space types and exit",
    )
    args = parser.parse_args()

    # List mode
    if args.list:
        print("\n📋 Available space types:\n")
        for key, info in SPACE_TYPES.items():
            print(f"  {key:24s} {info['label']}")
        print(f"\n  Total: {len(SPACE_TYPES)} types")
        return

    # Validate count
    if args.count < 1:
        print("❌ --count must be at least 1")
        return

    # Resolve output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize Gemini
    client = init_gemini()

    # Build generation tasks
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    tasks = []
    for i in range(args.count):
        space = args.space if args.space else random.choice(list(SPACE_TYPES.keys()))
        if args.count == 1:
            filename = f"original_{space}_{timestamp}.png"
        else:
            filename = f"original_{space}_{timestamp}_{i + 1}.png"
        output_path = str(output_dir / filename)
        tasks.append((space, output_path))

    # Generate
    if len(tasks) == 1:
        space, output_path = tasks[0]
        print(f"\n🏠 Space type: {SPACE_TYPES[space]['label']}")
        result = generate_original(client, space, output_path)
        if result:
            print(f"\n✅ Done! Use with the pipeline:")
            print(f"   python main.py {result}")
    else:
        print(f"\n🚀 Generating {len(tasks)} images in parallel...\n")
        for space, _ in tasks:
            print(f"  🏠 {SPACE_TYPES[space]['label']}")
        print()

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(tasks), 5)) as executor:
            futures = {}
            for space, output_path in tasks:
                fut = executor.submit(generate_original, client, space, output_path)
                futures[fut] = output_path
            for fut in concurrent.futures.as_completed(futures):
                try:
                    result = fut.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"  ❌ Error: {e}")

        print(f"\n✅ Generated {len(results)}/{len(tasks)} images.")
        if results:
            print("   Use any with the pipeline:")
            for r in sorted(results):
                print(f"   python main.py {r}")


if __name__ == "__main__":
    main()
