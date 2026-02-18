import google.genai.types as types
from reimagine import init_gemini


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
    # --- Mom / living room ---
    [
        "I showed my mom\\nwhat AI thinks our\\nliving room could be",
        "She's been complaining\\nabout it for years",
        "[STYLE_1]\\n *her reaction was priceless*",
        "[STYLE_2]\\n she chose this one",
        "She's redecorating now",
    ],
    # --- Dad / garage ---
    [
        "My dad said his\\ngarage was fine\\nthe way it was",
        "It hasn't changed\\nsince 2003",
        "[STYLE_1]\\n he went completely silent",
        "[STYLE_2]\\n he screenshot this one",
        "He's measuring\\nthe walls tomorrow",
    ],
    # --- Landlord / apartment ---
    [
        "Showed my landlord\\nwhat his apartment\\ncould actually look like",
        "He thought I was\\ntrying to raise the rent",
        "[STYLE_1]\\n he called his wife over",
        "[STYLE_2]\\n they both just stared",
        "He's hiring a contractor\\nnext week",
    ],
    # --- Girlfriend / bedroom ---
    [
        "My girlfriend has\\nhated our bedroom\\nsince we moved in",
        "I never understood\\nwhy until I saw these",
        "[STYLE_1]\\n she grabbed my phone",
        "[STYLE_2]\\n *this is the one*",
        "We're going furniture\\nshopping Saturday",
    ],
    # --- Roommate / kitchen ---
    [
        "My roommate said\\nour kitchen was\\nbeyond saving",
        "We haven't had\\npeople over in months",
        "[STYLE_1]\\n he didn't believe\\nit was the same room",
        "[STYLE_2]\\n he sent it\\nto his mom",
        "He's splitting the cost\\nwith me now",
    ],
    # --- Sister / bathroom ---
    [
        "My sister asked me\\nto help with her\\nbathroom renovation",
        "She's been putting\\nit off for two years",
        "[STYLE_1]\\n she saved it immediately",
        "[STYLE_2]\\n this one made\\nher change her mind",
        "She already ordered\\nthe tiles",
    ],
]

FILL_STORY_EXAMPLES = [
    # --- Mom / empty corner ---
    [
        "My mom has had\\nthis empty corner\\nfor three years",
        "She never knew\\nwhat to do with it",
        "[FILL_1]\\n she actually gasped",
        "[FILL_2]\\n *wait go back*",
        "She's already measuring\\nthe space",
    ],
    # --- Partner / awkward nook ---
    [
        "My girlfriend keeps\\ncomplaining about this\\nawkward space",
        "Nothing we tried\\never looked right",
        "[FILL_1]\\n she made me\\nzoom in",
        "[FILL_2]\\n this is the one\\nshe won't stop\\ntalking about",
        "We're ordering it\\nthis weekend",
    ],
    # --- Dad / empty wall ---
    [
        "My dad has stared at\\nthis blank wall\\nfor five years",
        "He says he's\\n*thinking about it*",
        "[FILL_1]\\n he finally stopped thinking",
        "[FILL_2]\\n he sent this\\nto the family group chat",
        "He drove to the store\\nthe same day",
    ],
]


def generate_screen_text(client, items: list[str], fill_mode: bool = False) -> list[str]:
    """
    Generate 6 screen text overlays for carousel slides using Gemini.

    Slide 1: Hook — introduce the person and the problem
    Slide 2: Context — why it matters, backstory
    Slides 3-4: Style/fill reveals with a genuine reaction
    Slide 5: Resolution — what they're doing now
    Slide 6: (handled by edit.py — "Staged AI" appended automatically)

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

    prompt = f"""You write short-form video captions for an interior design app called Staged AI.

The user has a room photo. The app reimagined it in these {item_label}s: {items_str}

Write a 6-slide story. The story is always about someone specific — a mom, dad, girlfriend, roommate, landlord, sister, etc. It should feel like something that genuinely mattered to the author. The person had a real problem with their space, the AI showed them possibilities, and their reaction was worth sharing.

STRUCTURE:
1. HOOK — introduce the person and the space problem (this goes over the original photo)
2. CONTEXT — why this matters, how long it's been an issue, the backstory
3. STYLE REVEAL + REACTION — show {items[0]} with their genuine reaction
4. STYLE REVEAL + MOMENT — show {items[1]} with what they did or said
5. ANOTHER REVEAL or REACTION — show {items[2]} with a reaction or moment
6. RESOLUTION — what's happening now (don't include "Staged AI", it's added automatically)

RULES:
- No full stops (periods). Ever
- No emojis. Ever
- Write about someone else, never "I redesigned" — always "I showed my mom" or "my dad saw"
- Use \\n to break lines. Keep each line to roughly 3-5 words so it reads well on a phone screen
- Italicize key reactions with *asterisks* like *she couldn't believe it* or *go back to that one*
- Each slide should be 2-4 short lines separated by \\n
- The story should have emotional weight — this person cared about their space
- Don't repeat the same sentence structure across slides
- Don't start every slide with the same word
- Slides 3-5 MUST start with the actual {item_label} name on the first line
- The {item_label} names to use are exactly: {items_str}

{formatted_examples}

Now write a NEW story (not a copy of any example above) for these {item_label}s: {items_str}

Return exactly 6 lines, one per slide. Nothing else — no numbering, no labels, no explanation."""

    print("Generating story captions...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
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
            f"I showed my mom\\nwhat AI thinks our\\nroom could look like",
            f"She's wanted to\\nchange it for years",
            f"{items[0]}\\n *her jaw dropped*",
            f"{items[1]}\\n she chose this one\\nimmediately",
            f"{items[2]}\\n *wait go back*",
            f"She's redecorating now",
        ]
