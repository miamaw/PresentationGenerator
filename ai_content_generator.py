"""
AI Content Generator for Presentation Generator
================================================
Integrates with various AI providers to generate lesson content
"""

import re


def get_system_instructions():
    """Return system instructions for AI"""
    return """You are an expert English teacher creating lesson content for a PowerPoint generator.

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

4. Separate slides with "---" on its own line

5. Use style tags:
   - [vocabulary] for new terms
   - [question] for questions
   - [answer] for answers
   - [emphasis] for important points
   - [step] for sequential reveals

6. NO markdown formatting (no ##, no **, no bullet points like - or *)
7. Use • for bullet points if needed
8. Keep titles under 60 characters
9. Include Notes: on every slide with teaching instructions

EXAMPLE OUTPUT:

Slide 1
Title: Introduction to Business Emails
Content: [emphasis] Lesson 1
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
Left: [vocabulary] formal
Right: Following official rules or customs
Left: [vocabulary] concise
Right: Giving information clearly and briefly
Notes: Drill pronunciation. Check understanding with examples.

---

You MUST output ONLY the content file. NO introduction, NO explanations, NO extra text.
Start directly with "Slide 1" and end with the last slide's Notes.
"""


def clean_ai_output(text):
    """Clean and fix common AI output issues"""
    
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
    Generate lesson content using Google Gemini
    """
    try:
        import google.generativeai as genai
    except ImportError:
        return None, "Please install google-generativeai: pip install google-generativeai"
    
    try:
        genai.configure(api_key=api_key)
        
        # Use Gemini 1.5 Flash (free tier)
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config={
                'temperature': 0.7,
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 4096,
            }
        )
        
        # Build the full prompt
        full_prompt = f"""{get_system_instructions()}

USER REQUEST:
Level: {level}
Duration: {duration} minutes
Topic: {user_prompt}

Generate a complete lesson with 8-10 slides following the exact format specified above.
Remember: Start DIRECTLY with "Slide 1" - no introduction or explanation."""
        
        # Generate content
        response = model.generate_content(full_prompt)
        
        if not response or not response.text:
            return None, "No response from AI"
        
        # Clean the output
        content = clean_ai_output(response.text)
        
        # Validate format
        is_valid, errors = validate_format(content)
        
        if not is_valid:
            # Try one more time with corrections
            correction_prompt = f"""The previous output had these errors:
{chr(10).join(errors)}

Please regenerate the lesson fixing these issues. Remember:
- Start with "Slide 1" (capital S)
- Every slide needs "Title: [text]" (capital T)
- Use Content:, Left:, Right:, etc. (capital first letter)
- Output ONLY the lesson content, no explanations.

Original request: {user_prompt}
Level: {level}, Duration: {duration} minutes"""
            
            retry_response = model.generate_content(correction_prompt)
            content = clean_ai_output(retry_response.text)
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