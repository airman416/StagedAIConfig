import google.genai.types as types
from reimagine import init_gemini


def generate_screen_text(client, items: list[str], fill_mode: bool = False) -> list[str]:
    """
    Generate cohesive screen text (overlays) across 6 carousel slides using Gemini.
    
    Slide 1: Hook/Intro
    Slides 2-6: Showcase the generated styles/ideas with narrative text.
    
    Args:
        client: Gemini client
        items: List of style names or fill ideas (should be 5 items)
        fill_mode: Whether we are in 'fill' mode or 'style' mode
        
    Returns:
        List of 6 strings (one for each slide).
    """
    
    item_type = "creative fill ideas" if fill_mode else "interior design styles"
    items_str = ", ".join(items)
    
    # Context based on mode
    if fill_mode:
        scenario = "We have an empty, awkward space that needs filling."
        hook_example = "What should I put in this empty corner? 😩"
    else:
        # Renovation mode (custom ugly/relatable look)
        scenario = "We have a REGULAR, slightly messy/ugly room that needs help."
        hook_example = "My living room looks so sad... help me fix it! 😩"


    prompt = f"""
    You are a social media storyteller for an interior design app called \"Staged AI\".
    
    We have a carousel with 6 slides:
    - Slide 1: The original "before" photo ({scenario}).
    - Slides 2-6: Five different {item_type} applied to the room. The styles are: {items_str}.
    
    GOAL: Write a COHESIVE, ENTERTAINING 6-PART STORY that flows across the slides.
    
    TONE: Millennial / Gen Z. Use emojis.
    - Use *asterisks* for actions/reactions (e.g. *her reaction was priceless*, *gasps in aesthetic*, *crying in poor*).
    - Avoid cheesy direct quotes like "Too clean for me!". Instead describe the vibe or reaction.
    - Be punchy and relatable. 
    
    FORMATTING RULES (CRITICAL):
    - MAX 5 WORDS PER LINE.
    - MAX 10 WORDS TOTAL per slide.
    - Use \\n to force line breaks.
    - KEEP IT SHORT.
    
    Choose ONE random story archetype from below (or invent a similar one):
    
    Archetype A (The Mom Makeover):
    1. "I showed my mom\\nwhat AI thinks\\nher living room could be"
    2. "{items[0]}??\\n*she was literally speechless* 😶"
    3. "Then we tried {items[1]}\\n*too fancy for the dog* 😂"
    4. "But {items[2]}...\\nWait, she actually loved this??"
    5. "I think she's obsessed\\nwith {items[3]} now ✨"
    6. "She's at Home Depot.\\nThanks Staged AI 💀" ({items[4]})

    Archetype B (The Rental Upgrade):
    1. "My landlord said no paint\\nso I asked AI instead 🤫"
    2. "This is what it looks like\\nvs {items[0]} ✨"
    3. "{items[1]} vibe\\nis kinda everything??"
    4. "I didn't know I needed\\n{items[2]} until now."
    5. "Which one should I\\nsecretly do? {items[3]}..."
    6. "Don't tell my landlord 🤫\\nStaged AI" ({items[4]})
    
    Archetype C (The Partner Test):
    1. "My boyfriend thinks\\nhis apartment is fine 🚩"
    2. "Showed him {items[0]}\\n*his reaction was priceless* 💀"
    3. "He actually admitted\\n{items[1]} is better."
    4. "Imagine if he actually\\ncleaned up for {items[2]}..."
    5. "We are definitely doing\\n{items[3]}. No debate."
    6. "Relationship saved. ✅\\nStaged AI" ({items[4]})

    INSTRUCTIONS:
    - Pick ONE storyline.
    - Write 6 short captions.
    - STRICTLY follow the line break and word count rules.
    - Mention the generated style names naturally.
    - Slide 6 should always wrap up the story.
    
    Output format:
    Return ONLY the 6 captions, one per line.
    """
    
    print("✍️  Weaving a story for captions...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.8,
            )
        )
        
        text = response.text.strip()
        captions = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Ensure we have exactly 6 captions (some models might output fewer or more)
        if len(captions) < 6:
            # Fallback if too few
            while len(captions) < 6:
                captions.append("Which one is your fav? 👇")
        
        return captions[:6]
        
    except Exception as e:
        print(f"❌ Error generating story captions: {e}")
        # Fallback list
        return [
            "Help me fix this space! 😭",
            f"Option 1: {items[0]} ✨",
            f"Option 2: {items[1]} 🌿",
            f"Option 3: {items[2]} 💡",
            f"Option 4: {items[3]} 🏠",
            f"Option 5: {items[4]} - Your pick? 👇"
        ]
