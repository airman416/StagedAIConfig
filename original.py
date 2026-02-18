#!/usr/bin/env python3
"""
Original "Problem Space" Image Generator

Generates photorealistic images of lived-in homes with a specific "problem area"
-- an unused or empty spot that begs to be filled. These images serve as input
to the carousel pipeline (main.py -> reimagine -> edit -> upload).

Usage:
  python original.py                                      # Random space, 1 image
  python original.py --space confusing_alcove             # Specific space type
  python original.py --count 3                            # Generate 3 images to pick from
  python original.py --space bay_window_nook -n 3         # 3 specific images
  python original.py --list                               # List all space types
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
    "odd_angled_nook": {
        "label": "Nook with strange non-90-degree angles",
        "description": (
            "A small nook or corner where the walls meet at odd, sharp, or obtuse angles "
            "due to the roofline or exterior geometry. "
            "It is tucked away — nobody walks through it. "
            "Standard furniture wouldn't fit squarely here. "
            "It looks completely empty, baffling, and architecturally confused."
        ),
    },
    "under_stairs_void": {
        "label": "Deep void under open stairs",
        "description": (
            "The space underneath a floating or open staircase. "
            "It's a large, odd-shaped footprint on the floor tucked to the side — not in a walkway. "
            "The ceiling slants aggressively, making it hard to stand in. "
            "It is currently just empty floor collecting dust."
        ),
    },
    "confusing_alcove": {
        "label": "Alcove with no clear purpose",
        "description": (
            "A recessed alcove in a living room or bedroom wall that isn't deep enough "
            "for a closet but too deep for a shelf. "
            "It has no shelving, just three blank walls forming a boxed-in nook. "
            "Nobody walks through it — it's a dead end. "
            "It looks like it was meant for something specific that never happened."
        ),
    },
    "loft_dead_space": {
        "label": "Unusable slice of a loft",
        "description": (
            "A narrow strip or wedge of floor in a loft area, trapped between the "
            "stair railing and a knee wall. "
            "It's a dead-end pocket of space — not a path anyone walks through. "
            "It's technically floor space, but it's hard to access and visually isolated. "
            "It looks lonely and forgotten."
        ),
    },
    "column_gap": {
        "label": "Gap between structural column and wall",
        "description": (
            "A strange empty pocket of space created between a structural column/pillar and a wall. "
            "It's a boxed-in void that nobody walks through — it just sits there. "
            "The floor is continuous but the space feels separated and useless."
        ),
    },
    "dormer_nook": {
        "label": "Deep dormer window recess",
        "description": (
            "A very deep recess leading to a dormer window in a bedroom or attic room. "
            "The side walls create a boxed-in nook around the window. "
            "Nobody walks through it — it's a dead end at the window. "
            "The floor area in front of the window is empty and feels disconnected from the room."
        ),
    },
    "sloped_ceiling_corner": {
        "label": "Corner with aggressive roof slope",
        "description": (
            "A corner of a room on an upper floor where the roofline cuts into the room "
            "drastically, leaving only a few feet of vertical wall before slanting in. "
            "It's a tucked-away corner — not a path, not a doorway, just dead space. "
            "The floor under the slope is empty and awkward to use."
        ),
    },
    "bay_window_nook": {
        "label": "Empty bay window nook",
        "description": (
            "A bay window bump-out in a living room or bedroom that juts out from the wall, "
            "creating a wide, shallow pocket of floor space. "
            "It's a dead-end alcove — nobody walks through it. "
            "The three-sided window area has nothing in it, just bare floor. "
            "It feels like wasted potential."
        ),
    },
    "fireplace_alcove": {
        "label": "Empty alcove beside a fireplace",
        "description": (
            "A recessed nook built into the wall right next to a fireplace or chimney breast. "
            "It's a boxed-in pocket — nobody walks through it, it just sits empty. "
            "It's too narrow for a closet but too deep to ignore. "
            "The walls are bare and it feels purposeless."
        ),
    },
    "corner_pocket": {
        "label": "Deep L-shaped corner pocket",
        "description": (
            "A deep corner where two walls of a room create an L-shaped pocket of dead space. "
            "It's tucked away from the main area — nobody walks through it. "
            "It's big enough to do something with but small enough to feel confusing. "
            "It is completely bare and undecorated."
        ),
    },
}

# Architectural twists randomly added for variety
ARCHITECTURAL_TWISTS = [
    "The ceiling height changes abruptly above this spot.",
    "A random support beam cuts through the edge of the visual field.",
    "The flooring changes direction or type near this area.",
    "There is an awkwardly placed outlet right in the center of the wall.",
    "A partial half-wall separates this void from the main room.",
    "The lighting is slightly dim in this specific corner.",
    "A window is placed asymmetrically in the space.",
    "The baseboard trim ends abruptly at the edge of this space.",
    "The wall paint is slightly different here, as if this area was an afterthought.",
]


def build_prompt(space_type: str, dated_look: bool = False) -> str:
    """Build the image generation prompt for a given space type."""
    info = SPACE_TYPES[space_type]
    twist = random.choice(ARCHITECTURAL_TWISTS)

    if dated_look:
        return f"""Generate a photorealistic image taken inside an AVERAGE, SLIGHTLY UNKEMPT residential home.
        
STYLE & VIBE:
- This is a REGULAR person's house, not a wealthy home.
- It looks LIVED-IN and slightly cluttered/messy (but not filthy).
- The interior design is UGLY and MISMATCHED.
- Think: Cheap furniture, hand-me-downs, maybe a random exercise bike in the corner, piles of mail/papers, or a slightly unmade sofa.
- Finishes: Beige rental carpet, popcorn ceiling, basic builder-grade white walls that are slightly scuffed.

PERSPECTIVE & FEEL:
- Shot from a PERSONAL, CANDID angle (smartphone photo).
- Bad lighting (maybe just one overhead bulb on).
- It feels real, raw, and relatable.

SUBJECT (The Room):
- A standard Living Room or Bedroom that just looks sad and needs help.
- Furniture is functional but ugly (e.g. a black leather couch next to a pine table).
- It feels STAGNANT and boring.

CRITICAL:
- NO people, NO pets.
- NO text.
- Portrait orientation (9:16)."""
    
    return f"""Generate a photorealistic image taken inside a LIVED-IN residential home.
The camera is pointed at a specific AWKWARD, UNDEFINED space -- an area where the
intended use is completely unclear ("liminal space").

PERSPECTIVE & FEEL:
- Shot from a PERSONAL, CANDID angle as if a homeowner took it with their
  phone, standing a few feet away, baffled by the space.
- Slightly off-center framing is fine.
- The image should feel authentic, like it was posted on social media asking
  "what on earth do I put here?"

THE PROBLEM AREA (center of the image):
- {info['description']}
- {twist}
- This specific area is EMPTY and UNUSED.
- The emptiness should feel AWKWARD and BAFFLING.
- It is NOT a standard square room. It has odd geometry or placement.
- CRITICAL: This must be a NOOK or DEAD-END pocket of space. Nobody walks through it.
  It is NOT a hallway, NOT a corridor, NOT a passageway. It is a tucked-away void
  where furniture, shelving, or decor could realistically be placed.
- The viewer should immediately think: "I have no idea what would go there."

THE SURROUNDINGS (edges / background):
- The rest of the visible home should look NORMAL and LIVED-IN.
- Hints of adjacent walls, baseboards, furniture, or staircases may be visible at the edges.
- CRITICAL: NO doors, NO doorframes, NO archways, and NO open passages should appear
  anywhere in the image — not in the nook, not in the background. Doors imply a walkway.
  This space is sealed on all sides except the opening facing the camera.

ARCHITECTURAL DETAILS:
- Make the geometry feel slightly "off" or challenging (angles, slopes, tight squeezes).
- Residential finishes (drywall, carpet/wood, trim) to ground it in reality.

CRITICAL:
- The PROBLEM AREA itself must be empty -- no furniture or decor there.
- The SURROUNDINGS should feel lived-in.
- NO people, NO pets.
- NO text.
- Portrait orientation (9:16)."""


def generate_original(client, space_type: str, output_path: str, dated_look: bool = False) -> Union[str, None]:
    """Generate a single original image for the given space type."""
    prompt = build_prompt(space_type, dated_look=dated_look)
    label = SPACE_TYPES[space_type]["label"]
    if dated_look:
        label += " (Dated Look)"

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
  python original.py                                      # Random space type, 1 image
  python original.py --space confusing_alcove             # Generate specific image
  python original.py --count 3                            # Generate 3 random images
  python original.py --space bay_window_nook -n 3         # 3 specific images
  python original.py --list                               # Show all space types
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
