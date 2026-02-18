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
    Write a 6-part story about a (Mom/Landlord/Partner) reacting to these styles: {items_str}.
    
    RULES:
    1. Each line = one complete slide. Do NOT split a sentence across slides.
    2. Max 3 words per line. You MUST include a \\n every 2 or 3 words.
    3. No emojis. No repetitive starts (don't repeat the subject every slide).
    
    EXAMPLE ARC:
    1. My landlord\\ninsists this\\nroom is fine
    2. Then I showed\\nthe {items[0]}\\ndesign version
    3. He actually\\n*blinked twice*\\nin pure silence
    4. Now he is\\nmeasuring for\\n{items[1]} furniture
    5. He even asked\\nfor the {items[2]}\\nstyle guide
    6. Guess who is\\nrenovating in\\n{items[4]} now?
    
    Return exactly 6 lines. Each line MUST have multiple \\n breaks.
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
