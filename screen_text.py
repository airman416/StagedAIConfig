import google.genai.types as types
from reimagine import init_gemini
from PIL import Image


CHARACTERS = [
    "my mom",
    "my dad",
    "my girlfriend",
    "my boyfriend",
    "my roommate",
    "my sister",
    "my brother",
    "my landlord",
    "my best friend",
    "my wife",
    "my husband",
    "my grandma",
]

STORY_EXAMPLES = [
    # --- Mom / living room: dismisses first, warms up, locks in on third ---
    [
        "I used AI to fix\\nmy mom's living room\\nshe didn't ask for this",
        "She's been complaining\\nabout it for years\\nbut hates change",
        "[STYLE_1]\\n *too cold*\\nshe said",
        "[STYLE_2]\\n *maybe*\\nshe wasn't sure",
        "[STYLE_3]\\n she went quiet\\nthen asked me\\nto scroll back",
        "She's redecorating now",
    ],
    # --- Dad / home office: resistant, indifferent, finally sold ---
    [
        "My dad said his\\nhome office was fine\\nI let AI prove otherwise",
        "It looks exactly the\\nsame as 2009",
        "[STYLE_1]\\n *that's not me*\\nhe said immediately",
        "[STYLE_2]\\n he shrugged\\nnot convinced",
        "[STYLE_3]\\n he stared at it\\nfor a long time\\nthen said nothing",
        "He measured the room\\nthe next morning",
    ],
    # --- Roommate / kitchen: skeptical, unimpressed, then the one that got him ---
    [
        "I used AI to show\\nmy roommate what\\nour kitchen could be",
        "He'd given up\\non it completely",
        "[STYLE_1]\\n *looks like a\\ncafe I'd never go to*",
        "[STYLE_2]\\n he scrolled past\\nwithout a word",
        "[STYLE_3]\\n *wait — how much\\nwould that actually cost*",
        "He's splitting it\\nwith me now",
    ],
    # --- Sister / bathroom: picky, dismissive, then the one that worked ---
    [
        "My sister hates\\nher bathroom\\nI tried fixing it with AI",
        "She rejects every idea\\nanyone suggests",
        "[STYLE_1]\\n *too trendy*\\nshe said",
        "[STYLE_2]\\n *nice but not me*",
        "[STYLE_3]\\n she grabbed my phone\\nand didn't give it back",
        "She already ordered\\nthe tiles",
    ],
    # --- Partner / bedroom: frustrated, dismisses two, finds the one ---
    [
        "My girlfriend has hated\\nour bedroom for years\\nso I used AI to fix it",
        "I've tried suggesting\\nthings for two years",
        "[STYLE_1]\\n *too minimal*\\nshe scrolled past",
        "[STYLE_2]\\n *that's not us*",
        "[STYLE_3]\\n she sent it\\nto herself\\nwithout saying anything",
        "We're going furniture\\nshopping Saturday",
    ],
]

FILL_STORY_EXAMPLES = [
    # --- Mom / empty corner: dismisses two, finds the third ---
    [
        "My mom had this empty\\ncorner for years\\nI used AI to fix it",
        "She'd rejected every\\nsuggestion I'd had",
        "[FILL_1]\\n *not enough storage*\\nshe said",
        "[FILL_2]\\n *too much going on*",
        "[FILL_3]\\n she went quiet\\nthen asked\\n*where do I get that*",
        "She's already measuring\\nthe space",
    ],
    # --- Partner / awkward nook: indifferent, indifferent, then locked in ---
    [
        "My girlfriend had\\nthis awkward nook\\nfor two years\\nI tried using AI to fix it",
        "Nothing we looked at\\never felt right",
        "[FILL_1]\\n *fine but not special*",
        "[FILL_2]\\n she shrugged\\nand kept scrolling",
        "[FILL_3]\\n she made me\\nzoom in three times",
        "We're ordering it\\nthis weekend",
    ],
    # --- Dad / blank wall: stubborn, dismisses one, then the one that got him ---
    [
        "My dad has stared\\nat this blank wall\\nfor five years\\nI used AI to fix it",
        "He says he's\\n*thinking about it*\\nhe is not",
        "[FILL_1]\\n *too much work*\\nhe said",
        "[FILL_2]\\n *I don't know*\\nnot a yes",
        "[FILL_3]\\n he sent it to\\nthe family group chat\\nwithout asking me",
        "He drove to the store\\nthe same day",
    ],
]


def generate_screen_text(client, items: list[str], fill_mode: bool = False, image_path: str = None) -> list[str]:
    """
    Generate 6 screen text overlays for carousel slides using Gemini.

    Slide 1: Hook — introduce the person and the problem
    Slide 2: Context — why it matters, backstory
    Slides 3-4: Style/fill reveals with a genuine reaction
    Slide 5: Resolution — what they're doing now
    Slide 6: (handled by edit.py — "Staged AI" appended automatically)

    image_path: path to the original room image. When provided, the image is
    passed to Gemini so the story references the correct room type.

    Returns list of 6 strings. The 6th is a short closing line;
    edit.py will append "Staged AI" to it.
    """

    items_str = ", ".join(items)
    examples = FILL_STORY_EXAMPLES if fill_mode else STORY_EXAMPLES
    item_label = "fill idea" if fill_mode else "style"

    formatted_examples = ""
    for idx, ex in enumerate(examples, 1):
        formatted_examples += f"\nEXAMPLE {idx}:\n"
        for slide_num, line in enumerate(ex, 1):
            formatted_examples += f"  {slide_num}. {line}\n"

    room_instruction = (
        "I am attaching the actual room photo. "
        "Look at it carefully and identify the EXACT room type (e.g. living room, bedroom, kitchen, corner nook, under-stairs space, etc.). "
        "Every slide of the story MUST reference that specific room and nothing else. "
        "Never invent a different room type."
        if image_path else
        "Write about a generic home space."
    )

    prompt = f"""You write short-form video captions for an interior design app called Staged AI.

The user has a room photo. The app reimagined it in these {item_label}s: {items_str}

{room_instruction}

Write a 6-slide story. The story is always about someone specific — a mom, dad, girlfriend, roommate, landlord, sister, etc. It should feel real and earned. The person is skeptical or picky. Most of the designs don't land. One finally does. That tension is what makes it worth watching.

STRUCTURE:
1. HOOK — introduce the person, the specific room shown in the photo, AND the fact that you used AI to fix it. This must be on slide 1. Examples: "I used AI to fix my mom's living room", "my dad's bedroom hadn't changed in years so I used AI", "I tried using AI to figure out what to do with this space"
2. CONTEXT — why this room matters, their resistance to change, the backstory
3. STYLE REVEAL + DISMISSAL — show {items[0]}, they don't like it or are indifferent. Show their actual reaction
4. STYLE REVEAL + INDIFFERENCE — show {items[1]}, still not quite right. A muted or skeptical response
5. STYLE REVEAL + THE ONE — show {items[2]}, this is the one that gets them. A real moment — silence, grabbing the phone, sending it somewhere
6. RESOLUTION — what's happening now as a result (don't include "Staged AI", it's added automatically)

RULES:
- No full stops (periods). Ever
- No emojis. Ever
- Write about someone else, never "I redesigned" — always "I showed my mom" or "my dad saw"
- Use \\n to break lines. Keep each line to roughly 3-5 words so it reads well on a phone screen
- Italicize quoted reactions or thoughts with *asterisks* like *too cold* or *where do I get that*
- Each slide should be 2-4 short lines separated by \\n
- Slides 3, 4, and 5 MUST start with the actual {item_label} name on the first line
- The {item_label} names to use are exactly: {items_str}
- Slides 3 and 4 must show rejection or indifference — not excitement. Vary how they dismiss it
- Slide 5 is the turn — make the reaction specific and real, not generic
- Slide 1 MUST mention using AI to fix/redesign/figure out the space
- Don't start every slide with the same word
- Don't repeat the same sentence structure across slides

{formatted_examples}

Now write a NEW story (not a copy of any example above) for these {item_label}s: {items_str}

Return exactly 6 lines, one per slide. Nothing else — no numbering, no labels, no explanation."""

    print("Generating story captions...")
    try:
        contents = [prompt]
        if image_path:
            try:
                contents = [Image.open(image_path), prompt]
            except Exception:
                pass  # fall back to text-only if image can't be loaded

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0.9,
            ),
        )

        text = response.text.strip()
        captions = [line.strip() for line in text.split("\n") if line.strip()]

        if len(captions) < 6:
            while len(captions) < 6:
                captions.append(f"{items[len(captions) - 1]}\\nwhich one would you pick")

        return captions[:6]

    except Exception as e:
        print(f"Error generating story captions: {e}")
        return [
            f"I used AI to fix\\nmy mom's room\\nshe didn't ask for this",
            f"She's wanted to change it\\nfor years but hates\\nevery suggestion",
            f"{items[0]}\\n *not really me*\\nshe said",
            f"{items[1]}\\n she shrugged\\nand kept scrolling",
            f"{items[2]}\\n she went quiet\\nthen asked\\n*where do I get that*",
            f"She's redecorating now",
        ]
