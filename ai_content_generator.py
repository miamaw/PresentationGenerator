"""
AI Content Generator for Presentation Generator
================================================
Integrates with various AI providers to generate lesson content
"""

import re


def get_system_instructions():
    """Return system instructions for AI"""
    return """You are an expert English teacher creating lesson content for a PowerPoint generator.

â›"â›"â›" CRITICAL TAG REQUIREMENT â›"â›"â›"
ALL style tags MUST be explicitly closed: [tag]content[/tag]
NEVER write: [emphasis] word  âŒâŒâŒ WRONG
ALWAYS write: [emphasis]word[/emphasis]  âœ…âœ…âœ… CORRECT
This is a TECHNICAL REQUIREMENT. Tags without closing brackets will break the system.

CRITICAL RULES - YOU MUST FOLLOW EXACTLY:

1. EVERY slide starts with "Slide X" on its own line (where X is 1, 2, 3, etc.)
2. EVERY slide has "Title: [text]" on the next line
3. Content sections start with one of these EXACT words followed by colon:
   - Content:
   - Left:
   - Right:
   - LeftTop:
   - RightTop:
   - LeftBottom:
   - RightBottom:
   - Notes:
   
   NOTE: You can combine layout types on the same slide:
   - Content: + LeftTop:/RightTop:/etc. will stack vertically (Content on top)
   - Content: + Left:/Right: will stack vertically (Content on top)
   - This is useful for adding instructions above structured content

4. Separate slides with "---" on its own line

5. Use style tags with EXPLICIT CLOSING TAGS (CRITICAL):
   - [vocabulary]term[/vocabulary] for new terms
   - [question]question text?[/question] for questions
   - [answer]answer text[/answer] for answers
   - [emphasis]important text[/emphasis] for important points
   - [step] for sequential reveals (no closing tag needed)
   
   EXAMPLES OF CORRECT TAG USAGE:
   âœ… Content: [emphasis]Lesson 1[/emphasis]
   âœ… Left: [vocabulary]formal[/vocabulary]
   âœ… Content: [question]Have you ever traveled?[/question]
   âœ… Content: I [answer]went[/answer] to Spain.
   
   EXAMPLES OF INCORRECT TAG USAGE:
   âŒ Content: [emphasis] Lesson 1  (missing closing tag)
   âŒ Left: [vocabulary] formal  (missing closing tag)
   âŒ Content: [question] Have you ever traveled?  (missing closing tag)

6. NO markdown formatting (no ##, no **, no bullet points like - or *)
7. Use â€¢ for bullet points if needed
8. Keep titles under 60 characters
9. Include Notes: on every slide with teaching instructions

EXAMPLE OUTPUT:

Slide 1
Title: Introduction to Business Emails
Content: [emphasis]Lesson 1[/emphasis]
Content: Professional Communication
Content: 
Content: Today's Focus:
Content: [step] Email structure
Content: [step] Formal language
Content: [step] Common phrases
Notes: Warm-up discussion about email challenges. 5 minutes.

---

Slide 2
Title: Key Vocabulary
Left: [vocabulary]formal[/vocabulary]
Right: Following official rules or customs
Left: [vocabulary]concise[/vocabulary]
Right: Giving information clearly and briefly
Notes: Drill pronunciation. Check understanding with examples.

---

You MUST output ONLY the content file. NO introduction, NO explanations, NO extra text.
Start directly with "Slide 1" and end with the last slide's Notes.
"""



def get_gemini_system_instructions():
    """Return GEMINI-SPECIFIC system instructions (NO TAGS version)"""
    return """You are an expert English teacher creating lesson content for a PowerPoint generator.

🔵 GEMINI-SPECIFIC VERSION - NO STYLE TAGS!

This version does NOT use style tags like [vocabulary], [emphasis], etc.
Instead, you use NATURAL FORMATTING: CAPITALS, **bold**, emojis, arrows.

CRITICAL RULES - YOU MUST FOLLOW EXACTLY:

1. EVERY slide starts with "Slide X" on its own line (where X is 1, 2, 3, etc.)
2. EVERY slide has "Title: [text]" on the next line
3. Content sections start with one of these EXACT words followed by colon:
   - Content:
   - Left:
   - Right:
   - LeftTop:
   - RightTop:
   - LeftBottom:
   - RightBottom:
   - Notes:
   
4. You CAN mix layout types on the same slide:
   - Content: + LeftTop:/RightTop:/etc. stacks vertically (Content on top)
   - Content: + Left:/Right: stacks vertically (Content on top)
   - Keep Content: brief (1-3 lines) when mixing

5. Separate slides with "---" on its own line

6. ❌ NO STYLE TAGS! Instead use NATURAL FORMATTING:
   
   FOR EMPHASIS/IMPORTANT:
   ❌ Don't use: [emphasis] Important point
   ✅ Do use: **IMPORTANT POINT**
   ✅ Or use: 🔑 IMPORTANT POINT
   
   FOR VOCABULARY:
   ❌ Don't use: [vocabulary] resilience
   ✅ Do use: **resilience** (n.)
   ✅ Or use: ★ VOCABULARY: resilience
   
   FOR QUESTIONS:
   ❌ Don't use: [question] What do you think?
   ✅ Do use: 💬 QUESTION: What do you think?
   ✅ Or use: Q: What do you think?
   
   FOR ANSWERS:
   ❌ Don't use: [answer] Here's the answer
   ✅ Do use: → ANSWER: Here's the answer
   ✅ Or use: A: Here's the answer
   
   USE EMOJIS LIBERALLY:
   💡 TIP / IDEA
   ⚠️ WARNING / CAUTION
   🔑 KEY POINT / ESSENTIAL
   ✅ CORRECT / RIGHT
   ❌ INCORRECT / WRONG
   💬 QUESTION / DISCUSSION
   → ANSWER / RESULT
   ★ IMPORTANT / HIGHLIGHT
   📝 EXAMPLE / NOTE
   🎯 GOAL / TARGET
   
   USE CAPITALS for emphasis:
   IMPORTANT: Check your work!
   KEY CONCEPT: Past Simple
   REMEMBER: Always validate!
   
   USE SYMBOLS:
   • Bullet points
   ○ Sub-points
   ✓ Correct
   ✗ Incorrect
   → Arrow to next idea
   ← Look back
   
   USE LABELS:
   FORM: Subject + Verb
   EXAMPLE: I went yesterday
   TIME MARKERS: yesterday, last week
   COMMON ERROR: didn't went → didn't go

7. CONTENT LENGTH:
   - Slide titles: Max 60 characters
   - Content section (when mixing): 1-3 lines only
   - Single column: Up to 500 characters
   - Two columns: Up to 300 characters per column
   - Four boxes: Up to 150 characters per box

8. TEACHER NOTES:
   Always include Notes: with timing, interaction type, and key teaching points

EXAMPLE SLIDE (Gemini version):

Slide 2
Title: Past Simple - Finished Actions
Content: ⏰ Use Past Simple for completed actions at specific past times
Content: Common time markers: yesterday, last week, in 2020
LeftTop: **FORM:**
LeftTop: Subject + Verb-ed
LeftTop: Examples: walked, played
RightTop: **EXAMPLES:**
RightTop: ✅ I walked to school yesterday
RightTop: ✅ They played tennis last week
LeftBottom: **TIME MARKERS:**
LeftBottom: • yesterday
LeftBottom: • last week
LeftBottom: • in 2020
RightBottom: ⚠️ **COMMON ERRORS:**
RightBottom: ❌ I didn't went
RightBottom: ✅ I didn't go
Notes: Review form. Drill examples. Check understanding with CCQs. 7 minutes.

---

Now create the lesson following these rules. Use natural formatting, NO style tags!
"""


def get_instructions_for_provider(provider="standard"):
    """
    Get appropriate instructions based on provider.
    
    Args:
        provider: "standard" (ChatGPT/Claude/default) or "gemini"
        
    Returns:
        System instructions string
    """
    if provider.lower() == "gemini":
        return get_gemini_system_instructions()
    else:
        return get_system_instructions()



def clean_ai_output(text):
    """Clean and fix common AI output issues + warn about layout mixing"""
    
    # Remove any markdown code blocks
    text = re.sub(r'```[\w]*\n?', '', text)
    
    # Remove any introductory text before first "Slide"
    match = re.search(r'(Slide \d+)', text)
    if match:
        text = text[match.start():]
    
    # Remove any concluding text after last slide
    lines = text.split('\n')
    last_content_idx = 0
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith('Notes:') or lines[i].strip() == '---':
            last_content_idx = i
            break
    
    if last_content_idx > 0:
        text = '\n'.join(lines[:last_content_idx + 1])
    
    # Fix common formatting issues
    text = text.replace('**', '')  # Remove markdown bold
    text = text.replace('##', '')  # Remove markdown headers
    text = text.replace('- ', '• ')  # Replace markdown bullets
    
    # TAG FIXING - Two-pass approach
    # Pass 1: Remove extra spaces inside tags
    for tag in ['vocabulary', 'question', 'answer', 'emphasis']:
        text = re.sub(rf'\[{tag}\]\s+', rf'[{tag}]', text, flags=re.IGNORECASE)
        text = re.sub(rf'\s+\[/{tag}\]', rf'[/{tag}]', text, flags=re.IGNORECASE)
    
    # Pass 2: Close unclosed tags
    for tag in ['vocabulary', 'question', 'answer', 'emphasis']:
        pattern = rf'\[{tag}\]([^\[\]]+?)(?=\n|$|Content:|Left:|Right:|LeftTop:|RightTop:|LeftBottom:|RightBottom:|Notes:)'
        
        def replace_func(match):
            content = match.group(1).strip()
            if not content.endswith(f'[/{tag}]'):
                return f'[{tag}]{content}[/{tag}]'
            return match.group(0)
        
        text = re.sub(pattern, replace_func, text, flags=re.IGNORECASE)
    
    # Remove undefined tags
    text = re.sub(r'\[example\]\s*', '', text, flags=re.IGNORECASE)
    
    # LAYOUT MIXING INFO - Now supported!
    slides = text.split('---')
    info_messages = []
    
    for slide in slides:
        lines = slide.split('\n')
        
        # Find slide identifier
        slide_id = None
        for line in lines:
            if line.strip().startswith('Slide '):
                slide_id = line.strip()
                break
        
        if not slide_id:
            continue
        
        # Check for layout mixing
        has_four_box = any(l.strip().startswith(('LeftTop:', 'RightTop:', 'LeftBottom:', 'RightBottom:')) for l in lines)
        has_two_col = any(l.strip().startswith(('Left:', 'Right:')) for l in lines)
        has_content = any(l.strip().startswith('Content:') for l in lines)
        
        if has_four_box and has_content:
            info_messages.append(f"ℹ️  {slide_id}: Uses mixed layout (Content + four-box)")
            info_messages.append(f"   → Content will appear above the four boxes")
        elif has_two_col and has_content:
            info_messages.append(f"ℹ️  {slide_id}: Uses mixed layout (Content + two-column)")
            info_messages.append(f"   → Content will appear above the columns")
    
    # Print info messages
    if info_messages:
        print("\n" + "="*70)
        print("ℹ️  MIXED LAYOUTS DETECTED (Content will stack vertically)")
        print("="*70)
        for msg in info_messages:
            print(msg)
        print("="*70 + "\n")
    
    # Ensure proper spacing around ---
    text = re.sub(r'\n---\n', '\n\n---\n\n', text)
    
    return text.strip()


def validate_format(text):
    """
    Validate that the AI output follows the correct format
    Returns: (is_valid, errors_list)
    """
    errors = []
    lines = text.split('\n')
    
    # Check for slides
    slide_count = len([l for l in lines if l.strip().startswith('Slide ')])
    if slide_count == 0:
        errors.append("No slides found. Must start with 'Slide 1'")
        return False, errors
    
    # Check each slide has a title
    current_slide = None
    has_title = False
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('Slide '):
            if current_slide and not has_title:
                errors.append(f"{current_slide}: Missing 'Title:' line")
            current_slide = line
            has_title = False
        
        if line.startswith('Title:'):
            has_title = True
    
    # Check last slide
    if current_slide and not has_title:
        errors.append(f"{current_slide}: Missing 'Title:' line")
    
    # Check for valid section headers
    valid_sections = ['Content:', 'Left:', 'Right:', 'LeftTop:', 'RightTop:', 
                     'LeftBottom:', 'RightBottom:', 'Notes:', 'Title:', 'Template:']
    
    for i, line in enumerate(lines, 1):
        if ':' in line and not line.startswith('#'):
            section = line.split(':')[0] + ':'
            if section not in valid_sections and not line.strip().startswith('Slide'):
                # Check if it might be a typo
                if any(sec in line for sec in ['content', 'left', 'right', 'notes']):
                    errors.append(f"Line {i}: '{section}' should be capitalized (e.g., 'Content:')")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def generate_with_gemini(user_prompt, api_key, level="B1", duration="60"):
    """
    Generate lesson content using Google Gemini (updated for 2025 API)
    """
    try:
        import google.generativeai as genai
    except ImportError:
        return None, "Please install google-generativeai: pip install google-generativeai"
    
    try:
        genai.configure(api_key=api_key)

        # âœ… Use latest Gemini 
        model = genai.GenerativeModel(
            "models/gemini-flash-latest",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,  # supports longer lessons
            }
        )

        # Build the system + user prompt
        full_prompt = f"""{get_system_instructions()}

USER REQUEST:
Level: {level}
Duration: {duration} minutes
Topic: {user_prompt}

Generate a complete lesson with 8â€“10 slides following the exact format specified above.
Start DIRECTLY with "Slide 1" â€” no intro or commentary.
"""

        # Generate content
        response = model.generate_content(full_prompt)

        if not response or not getattr(response, "text", None):
            return None, "No response text from Gemini"

        # Clean and validate
        content = clean_ai_output(response.text)
        is_valid, errors = validate_format(content)

        if not is_valid:
            correction_prompt = f"""The previous output had formatting issues:
{chr(10).join(errors)}

Please regenerate correctly following the strict format.
Start with "Slide 1" and include Notes: on every slide.
"""
            retry = model.generate_content(correction_prompt)
            content = clean_ai_output(retry.text)
            is_valid, errors = validate_format(content)

        return content, None if is_valid else f"Format issues: {', '.join(errors)}"

    except Exception as e:
        return None, f"Error: {str(e)}"



def generate_with_openai(user_prompt, api_key, level="B1", duration="60"):
    """
    Generate lesson content using OpenAI
    """
    try:
        import openai
    except ImportError:
        return None, "Please install openai: pip install openai"
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": get_system_instructions()},
                {"role": "user", "content": f"""Level: {level}
Duration: {duration} minutes
Topic: {user_prompt}

Generate a complete lesson with 8-10 slides."""}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        content = clean_ai_output(response.choices[0].message.content)
        is_valid, errors = validate_format(content)
        
        return content, None if is_valid else f"Format issues: {', '.join(errors)}"
        
    except Exception as e:
        return None, f"Error: {str(e)}"


def generate_with_claude(user_prompt, api_key, level="B1", duration="60"):
    """
    Generate lesson content using Anthropic Claude
    """
    try:
        import anthropic
    except ImportError:
        return None, "Please install anthropic: pip install anthropic"
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": f"""{get_system_instructions()}

Level: {level}
Duration: {duration} minutes
Topic: {user_prompt}

Generate a complete lesson with 8-10 slides."""
            }]
        )
        
        content = clean_ai_output(message.content[0].text)
        is_valid, errors = validate_format(content)
        
        return content, None if is_valid else f"Format issues: {', '.join(errors)}"
        
    except Exception as e:
        return None, f"Error: {str(e)}"


# Prompt templates
PROMPT_TEMPLATES = {
    "Custom": "",
    
    "Conversation Practice": """Create a conversation practice lesson about {topic}.
Include: icebreaker questions, useful phrases for the topic, a sample dialogue, 
role-play scenarios, and follow-up discussion questions.
Focus on natural, everyday language.""",
    
    "Business English": """Create a Business English lesson on {topic}.
Include: professional vocabulary (6-8 terms), formal language patterns,
a real-world business scenario or example, and a practice writing/speaking activity.
Use appropriate business context.""",
    
    "Grammar Focus": """Create a grammar lesson teaching {topic}.
Include: clear rule explanation with examples, common errors section,
controlled practice exercises (fill-in-the-blank or multiple choice),
and a freer practice activity. Use 4-box layout for grammar explanation slide.""",
    
    "Reading Comprehension": """Create a reading comprehension lesson about {topic}.
Include: a reading passage (180-250 words) suitable for the level,
vocabulary pre-teaching (6-8 words), comprehension questions (4-5),
and a follow-up discussion or writing task.""",
    
    "Vocabulary": """Create a vocabulary lesson introducing {topic}-related words.
Include: 8-12 vocabulary items with clear definitions and examples,
pronunciation notes, practice activities (matching, gap-fill, or sentence creation),
and a speaking activity using the new vocabulary.""",
    
    "Listening/Speaking": """Create a lesson developing listening and speaking skills on {topic}.
Include: discussion questions to activate prior knowledge, key phrases for the topic,
a listening comprehension task (describe what they should listen for),
and structured speaking practice."""
}


def get_template_prompt(template_name, topic="", level="B1", duration="60"):
    """
    Get a pre-filled prompt based on template type
    """
    if template_name == "Custom":
        return ""
    
    template = PROMPT_TEMPLATES.get(template_name, "")
    if topic:
        template = template.replace("{topic}", topic)
    
    return template