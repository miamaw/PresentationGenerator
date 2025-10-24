"""
Universal PowerPoint Generator - Web App
=========================================
Fully customizable presentation generator for educators
With integrated live preview and comprehensive help
"""

import streamlit as st
import os
import io
import base64
import re
from pathlib import Path
from tag_parser import parse_inline_tags

# Import the universal generator
GENERATOR_AVAILABLE = False
PREVIEW_AVAILABLE = True  # Built-in preview always available
AI_AVAILABLE = False

# Try to import core generator
try:
    from generate_presentation_universal import (
        merge_config, parse_content_file, build_presentation,
        validate_slide, DEFAULT_CONFIG
    )
    GENERATOR_AVAILABLE = True
except ImportError as e:
    st.warning(f"âš ï¸ Core generator not found. Preview and AI features still available.")
    # Fallback DEFAULT_CONFIG
    DEFAULT_CONFIG = {
        "background_image": None,
        "background_color": [255, 255, 255],
        "title_color": [0, 0, 0],
        "text_color": [64, 64, 64],
        "font_name": "Arial",
        "title_font_name": "Arial",
        "slide_width": 13.33,
        "slide_height": 7.5,
        "enable_slide_numbers": True,
        "enable_overflow_warnings": True,
        "styles": {
            "vocabulary": {"font_size": 24, "color": [0, 128, 0], "bold": True},
            "question": {"font_size": 20, "color": [128, 0, 128], "bold": False},
            "answer": {"font_size": 18, "color": [128, 128, 128], "italic": True},
            "emphasis": {"font_size": 22, "color": [192, 0, 0], "bold": True}
        }
    }

# Try to import AI generator (optional)
try:
    from ai_content_generator import (
        generate_with_gemini, generate_with_openai, generate_with_claude,
        get_template_prompt, PROMPT_TEMPLATES
    )
    AI_AVAILABLE = True
    st.success("âœ… AI Content Generator loaded successfully!")
except ImportError as e:
    # AI features are optional
    PROMPT_TEMPLATES = {}
    st.info("ðŸ’¡ AI features not available. Install packages: pip install google-generativeai openai anthropic")

# Page configuration
st.set_page_config(
    page_title="Universal PowerPoint Generator",
    page_icon="ðŸŽ¨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-weight: bold;
    }
    .stButton>button {
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


def rgb_to_hex(rgb):
    """Convert RGB list to hex color"""
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])


def hex_to_rgb(hex_color):
    """Convert hex color to RGB list"""
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]

def normalize_legacy_inline_tags(text):
    """
    Ensures open-only tags like [emphasis] word or inline [answer]went
    are converted into closed-tag form [emphasis]word[/emphasis].
    Works anywhere in the line.
    """
    import re
    # Normalize spacing
    text = re.sub(r'\s+', ' ', text)

    # Convert bare [tag] word â†’ [tag]word[/tag]
    def close_tag(m):
        tag, inner = m.group(1), m.group(2).strip()
        return f"[{tag}]{inner}[/{tag}]"

    text = re.sub(
        r'\[(vocabulary|question|answer|emphasis)\]\s*([^\[\]]+?)(?=\s|[.,!?]|$)',
        close_tag,
        text,
        flags=re.I
    )

    return text



def get_quick_reference():
    """Return quick reference text"""
    return """QUICK REFERENCE
===============

Slide Structure:
  Slide #
  Title: ...
  Content: ...
  ---

Layouts:
  â€¢ Content: single column
  â€¢ Left:/Right: two columns  
  â€¢ LeftTop/RightTop/
    LeftBottom/RightBottom: 4-box

Special Tags:
  [step] - animations
  [vocabulary] - custom style
  [question] - custom style
  [answer] - custom style
  [emphasis] - custom style
"""


def get_sample_template():
    """Return sample lesson template"""
    return """# Sample Lesson Template

Slide 1
Title: Lesson Title Here
Content: [emphasis] Main Topic
Content: 
Content: Today's Focus:
Content: [step] Learning objective 1
Content: [step] Learning objective 2
Content: [step] Learning objective 3
Notes: Introduction and warm-up. 5 minutes.

---

Slide 2
Title: Discussion Question
Content: [question] What is your experience with this topic?
Content: 
Content: Think about:
Content: â€¢ Point to consider 1
Content: â€¢ Point to consider 2
Content: â€¢ Point to consider 3
Notes: Pair discussion 3 minutes.

---

Slide 3
Title: Key Vocabulary
Left: [vocabulary] term one
Right: Definition of first term
Left: [vocabulary] term two
Right: Definition of second term
Notes: Drill pronunciation.

---
"""


# ============================================================================
# PREVIEW FUNCTIONS
# ============================================================================

def parse_slides_for_preview(content):
    """Parse content and return structured slide data for preview"""
    slides = []
    current_slide = None
    
    for line in content.split('\n'):
        line = line.strip()
        
        # Skip comments and empty lines
        if line.startswith('#') or not line:
            continue
        
        # New slide
        if line.lower().startswith('slide '):
            if current_slide:
                slides.append(current_slide)
            current_slide = {
                'number': line,
                'title': '',
                'content': [],
                'left': [],
                'right': [],
                'lefttop': [],
                'righttop': [],
                'leftbottom': [],
                'rightbottom': [],
                'notes': []
            }
        
        # Separator
        elif line == '---':
            if current_slide:
                slides.append(current_slide)
                current_slide = None
        
        # Slide properties
        elif current_slide:
            if line.lower().startswith('title:'):
                current_slide['title'] = line[6:].strip()
            elif line.lower().startswith('content:'):
                current_slide['content'].append(line[8:].strip())
            elif line.lower().startswith('left:'):
                current_slide['left'].append(line[5:].strip())
            elif line.lower().startswith('right:'):
                current_slide['right'].append(line[6:].strip())
            elif line.lower().startswith('lefttop:'):
                current_slide['lefttop'].append(line[8:].strip())
            elif line.lower().startswith('righttop:'):
                current_slide['righttop'].append(line[9:].strip())
            elif line.lower().startswith('leftbottom:'):
                current_slide['leftbottom'].append(line[11:].strip())
            elif line.lower().startswith('rightbottom:'):
                current_slide['rightbottom'].append(line[12:].strip())
            elif line.lower().startswith('notes:'):
                current_slide['notes'].append(line[6:].strip())
    
    # Add last slide
    if current_slide:
        slides.append(current_slide)
    
    return slides



def show_slide_preview(slide, slide_num, config):
    """Display a single slide preview with actual styling"""
    
    # Get colors from config
    bg_color = config.get("background_color", [255, 255, 255])
    title_color = config.get("title_color", [0, 0, 0])
    text_color = config.get("text_color", [64, 64, 64])
    
    # Convert to hex for HTML
    bg_hex = rgb_to_hex(bg_color)
    title_hex = rgb_to_hex(title_color)
    text_hex = rgb_to_hex(text_color)
    
    # Get fonts
    title_font = config.get("title_font_name", "Arial")
    body_font = config.get("font_name", "Arial")
    
    # Determine layout
    has_content = len(slide['content']) > 0
    has_two_col = len(slide['left']) > 0 or len(slide['right']) > 0
    has_four_box = any([
        len(slide['lefttop']) > 0,
        len(slide['righttop']) > 0,
        len(slide['leftbottom']) > 0,
        len(slide['rightbottom']) > 0
    ])
    
    # Background styling with base64 encoding for images
    bg_style = f"background-color: {bg_hex};"
    if config.get("background_image") and os.path.exists(config["background_image"]):
        try:
            with open(config["background_image"], "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode()
                # Determine image type
                img_ext = config["background_image"].lower().split('.')[-1]
                mime_type = f"image/{img_ext if img_ext in ['png', 'jpg', 'jpeg'] else 'jpeg'}"
                if img_ext == 'jpg':
                    mime_type = 'image/jpeg'
                bg_style = f"background-image: url('data:{mime_type};base64,{img_data}'); background-size: cover; background-position: center;"
        except Exception as e:
            # Fallback to solid color if image can't be loaded
            bg_style = f"background-color: {bg_hex};"
    
    # Content styling helper
    def get_styled_text(text, config):
        """Apply style tag colors using unified parser"""
        segments = parse_inline_tags(text)
        
        html_parts = []
        for content, style_name in segments:
            if style_name:
                # Get color and formatting for this style
                style = config["styles"].get(style_name, {})
                style_color = rgb_to_hex(style["color"])
                is_bold = style.get("bold", False)
                is_italic = style.get("italic", False)
                
                style_attrs = [f"color: {style_color}"]
                if is_bold:
                    style_attrs.append("font-weight: bold")
                if is_italic:
                    style_attrs.append("font-style: italic")
                
                html_parts.append(f'<span style="{"; ".join(style_attrs)}">{content}</span>')
            else:
                html_parts.append(content)
        
        return ''.join(html_parts)
    
    # Build complete HTML structure
    html_content = f"""
        <div style="
            border: 2px solid #ddd;
            border-radius: 8px;
            padding: 10px;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">
            <div style="
                {bg_style}
                padding: 40px 60px;
                border-radius: 5px;
                min-height: 400px;
                position: relative;
            ">
                <h2 style="
                    color: {title_hex}; 
                    font-family: {title_font}, sans-serif;
                    margin-bottom: 30px; 
                    border-bottom: 2px solid {title_hex}; 
                    padding-bottom: 15px;
                    font-size: 32px;
                    font-weight: bold;
                ">
                    {slide['title'] if slide['title'] else 'Untitled Slide'}
                </h2>
    """
    
    # Single column content
    if has_content:
        html_content += f'<div style="font-family: {body_font}, sans-serif; color: {text_hex}; font-size: 18px; line-height: 1.8;">'
        for item in slide['content']:
            if item:
                styled = get_styled_text(item, config)
                html_content += f'<p style="margin: 12px 0;">{styled}</p>'
        html_content += '</div>'
    
    # Two column layout
    elif has_two_col:
        html_content += '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">'
        
        # Left column
        html_content += f'<div style="font-family: {body_font}, sans-serif; color: {text_hex}; font-size: 18px;">'
        for item in slide['left']:
            if item:
                styled = get_styled_text(item, config)
                html_content += f'<p style="margin: 12px 0;">{styled}</p>'
        html_content += '</div>'
        
        # Right column
        html_content += f'<div style="font-family: {body_font}, sans-serif; color: {text_hex}; font-size: 18px; border-left: 2px solid #ccc; padding-left: 20px;">'
        for item in slide['right']:
            if item:
                styled = get_styled_text(item, config)
                html_content += f'<p style="margin: 12px 0;">{styled}</p>'
        html_content += '</div>'
        
        html_content += '</div>'
    
    # Four box layout
    elif has_four_box:
        html_content += '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">'
        
        # Left column
        html_content += '<div>'
        if slide['lefttop']:
            html_content += f'<div style="border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 5px; background: rgba(255,255,255,0.7); font-family: {body_font}, sans-serif; color: {text_hex}; font-size: 16px;">'
            for item in slide['lefttop']:
                if item:
                    styled = get_styled_text(item, config)
                    html_content += f'<p style="margin: 8px 0;">{styled}</p>'
            html_content += '</div>'
        
        if slide['leftbottom']:
            html_content += f'<div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background: rgba(255,255,255,0.7); font-family: {body_font}, sans-serif; color: {text_hex}; font-size: 16px;">'
            for item in slide['leftbottom']:
                if item:
                    styled = get_styled_text(item, config)
                    html_content += f'<p style="margin: 8px 0;">{styled}</p>'
            html_content += '</div>'
        html_content += '</div>'
        
        # Right column
        html_content += '<div>'
        if slide['righttop']:
            html_content += f'<div style="border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 5px; background: rgba(255,255,255,0.7); font-family: {body_font}, sans-serif; color: {text_hex}; font-size: 16px;">'
            for item in slide['righttop']:
                if item:
                    styled = get_styled_text(item, config)
                    html_content += f'<p style="margin: 8px 0;">{styled}</p>'
            html_content += '</div>'
        
        if slide['rightbottom']:
            html_content += f'<div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background: rgba(255,255,255,0.7); font-family: {body_font}, sans-serif; color: {text_hex}; font-size: 16px;">'
            for item in slide['rightbottom']:
                if item:
                    styled = get_styled_text(item, config)
                    html_content += f'<p style="margin: 8px 0;">{styled}</p>'
            html_content += '</div>'
        html_content += '</div>'
        
        html_content += '</div>'
    
    # Close slide container
    html_content += '</div></div>'
    
    # Render all HTML at once
    st.markdown(html_content, unsafe_allow_html=True)
    
    # Show notes if present (keep this yellow styling)
    if slide['notes']:
        st.markdown('''
            <div style="
                margin-top: 15px; 
                padding: 15px; 
                background: #FFF9C4; 
                border-left: 4px solid #FBC02D;
                border-radius: 3px;
            ">
                <strong style="color: #F57F17;">ðŸ“ Teacher Notes:</strong>
        ''', unsafe_allow_html=True)
        for note in slide['notes']:
            if note:
                st.markdown(f'<p style="margin: 5px 0; color: #666; font-size: 0.9em;">{note}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Slide number badge
    st.markdown(f'''
        <div style="text-align: right; margin-top: 10px;">
            <span style="
                background: #1976D2;
                color: white;
                padding: 5px 15px;
                border-radius: 15px;
                font-size: 0.9em;
                font-weight: bold;
            ">
                Slide {slide_num}
            </span>
        </div>
    ''', unsafe_allow_html=True)

# ============================================================================
# VALIDATION AND GENERATION FUNCTIONS
# ============================================================================

def validate_content():
    """Validate the content"""
    if not st.session_state.content.strip():
        st.warning("âš ï¸ Please enter some content first")
        return
    
    if not GENERATOR_AVAILABLE:
        st.error("âš ï¸ Generator module not available")
        return
    
    try:
        temp_file = "temp_validation.txt"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(st.session_state.content)
        
        slides = parse_content_file(temp_file)
        
        all_issues = []
        for i, slide in enumerate(slides, 1):
            issues = validate_slide(slide, i, st.session_state.custom_config)
            all_issues.extend(issues)
        
        st.session_state.validation_results = {
            'success': True,
            'slide_count': len(slides),
            'issues': all_issues
        }
        
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
    except Exception as e:
        st.session_state.validation_results = {
            'success': False,
            'error': str(e)
        }


def generate_presentation():
    """Generate PowerPoint presentation"""
    if not st.session_state.content.strip():
        st.warning("âš ï¸ Please enter some content first")
        return
    
    if not GENERATOR_AVAILABLE:
        st.error("âš ï¸ Generator module not available")
        return
    
    try:
        with st.spinner("ðŸŽ¨ Generating presentation..."):
            temp_input = "temp_content.txt"
            with open(temp_input, 'w', encoding='utf-8') as f:
                f.write(st.session_state.content)
            
            temp_output = "temp_presentation.pptx"
            slides = parse_content_file(temp_input)
            build_presentation(slides, temp_output, st.session_state.custom_config)
            
            with open(temp_output, 'rb') as f:
                pptx_data = f.read()
            
            st.success("âœ… Presentation generated successfully!")
            st.download_button(
                label="ðŸ“¥ Download PowerPoint",
                data=pptx_data,
                file_name="presentation.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
            
            if os.path.exists(temp_input):
                os.remove(temp_input)
            if os.path.exists(temp_output):
                os.remove(temp_output)
            
    except Exception as e:
        st.error(f"âŒ Error generating presentation: {str(e)}")
        st.exception(e)

# ============================================================================
# AI CONTENT GENERATION
# ============================================================================

def generate_lesson_with_ai(prompt, level, duration):
    """Generate lesson content using AI"""
    if 'ai_generating' not in st.session_state:
        st.session_state.ai_generating = False
    
    st.session_state.ai_generating = True
    
    try:
        provider = st.session_state.get('ai_provider')
        api_key = st.session_state.get('ai_key')
        
        if not provider or not api_key:
            st.error("âŒ Please configure AI provider and API key in sidebar")
            return
        
        with st.spinner(f"ðŸ¤– {provider} is generating your lesson..."):
            if "Gemini" in provider:
                content, error = generate_with_gemini(prompt, api_key, level, duration)
            elif "OpenAI" in provider:
                content, error = generate_with_openai(prompt, api_key, level, duration)
            elif "Claude" in provider:
                content, error = generate_with_claude(prompt, api_key, level, duration)
            else:
                content, error = None, "Unknown provider"
            
            if error:
                st.error(f"âŒ Generation failed: {error}")
                st.info("ðŸ’¡ Tip: Try rephrasing your prompt or check your API key")
            elif content:
                st.session_state.content = content
                st.success("âœ… Lesson generated! Content loaded into editor below.")
                st.info("ðŸ‘€ Review the content and click 'Generate PowerPoint' when ready")
                st.rerun()
            else:
                st.error("âŒ No content generated. Please try again.")
    
    except Exception as e:
        st.error(f"âŒ Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    
    finally:
        st.session_state.ai_generating = False

# ============================================================================
# EDITOR WITH PREVIEW
# ============================================================================

def show_editor():
    """Enhanced editor with live preview panel"""
    st.header("Content Editor")

    # AI Generator section
    if AI_AVAILABLE and hasattr(st.session_state, 'ai_provider') and st.session_state.ai_provider and st.session_state.ai_provider != "None":
        with st.expander("ðŸ¤– Generate with AI", expanded=False):
            st.markdown("### Describe Your Lesson")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                lesson_type = st.selectbox(
                    "Lesson Type:",
                    list(PROMPT_TEMPLATES.keys()) if AI_AVAILABLE else ["Custom"]
                )
            
            with col2:
                level = st.selectbox("Level:", ["A1", "A2", "B1", "B2", "C1", "C2"], index=2)
            
            with col3:
                duration = st.selectbox("Duration:", ["30", "45", "60", "90"], index=2)
            
            # Topic/prompt input
            if lesson_type == "Custom":
                topic_prompt = st.text_area(
                    "Describe what you want:",
                    placeholder="e.g., Create a lesson about job interviews...",
                    height=100
                )
            else:
                topic = st.text_input(
                    "Topic:",
                    placeholder="e.g., job interviews, complaints, past tense..."
                )
                
                if topic:
                    template_text = get_template_prompt(lesson_type, topic, level, duration)
                    topic_prompt = st.text_area(
                        "AI Prompt (edit if needed):",
                        value=template_text,
                        height=100
                    )
                else:
                    topic_prompt = ""
            
            # Generate button
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("âœ¨ Generate Lesson", type="primary", disabled=not topic_prompt):
                    if not st.session_state.ai_key:
                        st.error("âš ï¸ Please add your API key in the sidebar")
                    else:
                        generate_lesson_with_ai(topic_prompt, level, duration)
            
            with col2:
                if st.session_state.get('ai_generating'):
                    st.info("ðŸ¤– AI is generating your lesson...")
    
    st.markdown("---")
    
    # File operations
   
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        uploaded_file = st.file_uploader("ðŸ“‚ Upload .txt file", type=['txt'])
        if uploaded_file is not None:
            content = uploaded_file.read().decode('utf-8')
            st.session_state.content = content
            st.success(f"Loaded: {uploaded_file.name}")
    
    with col2:
        if st.session_state.content:
            st.download_button(
                label="ðŸ’¾ Download .txt",
                data=st.session_state.content,
                file_name="lesson_content.txt",
                mime="text/plain"
            )
    
    # Two column layout: Editor + Preview
    editor_col, preview_col = st.columns([1, 1])
    
    with editor_col:
        st.markdown("### âœï¸ Edit Content")
        content = st.text_area(
            "Content Editor",
            value=st.session_state.content,
            height=500,
            help="Write your lesson content here",
            label_visibility="collapsed"
        )
        st.session_state.content = content
    
    with preview_col:
        st.markdown("### ðŸ‘ï¸ Live Preview")
        
        if st.session_state.content.strip():
            try:
                slides = parse_slides_for_preview(st.session_state.content)
                
                if slides:
                    # Slide selector
                    slide_options = [f"Slide {i+1}: {s['title'][:30] if s['title'] else 'Untitled'}" 
                                   for i, s in enumerate(slides)]
                    
                    selected = st.selectbox(
                        "Select slide to preview:",
                        range(len(slides)),
                        format_func=lambda x: slide_options[x]
                    )
                    
                    # Show preview
                    show_slide_preview(slides[selected], selected + 1, st.session_state.custom_config)
                    
                    # Navigation
                    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
                    with nav_col1:
                        if selected > 0:
                            if st.button("â¬…ï¸ Previous"):
                                st.rerun()
                    with nav_col3:
                        if selected < len(slides) - 1:
                            if st.button("Next âž¡ï¸"):
                                st.rerun()
                    
                    st.info(f"ðŸ“Š Total slides: {len(slides)}")
                else:
                    st.warning("No slides found. Start with:\n```\nSlide 1\nTitle: Your Title\nContent: Your content\n```")
            except Exception as e:
                st.error(f"Preview error: {str(e)}")
                st.info("Check your syntax and try again")
        else:
            st.info("ðŸ‘ˆ Start typing to see preview")
            st.markdown("""
            **Quick Start:**
            ```
            Slide 1
            Title: My First Slide
            Content: Hello World!
            ---
            ```
            """)
    
    # Action buttons below
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        validate_button = st.button("âœ… Validate Content", use_container_width=True)
    
    with col2:
        generate_button = st.button("ðŸŽ¨ Generate PowerPoint", 
                                    type="primary", 
                                    use_container_width=True,
                                    disabled=not GENERATOR_AVAILABLE)
    
    with col3:
        clear_button = st.button("ðŸ—‘ï¸ Clear All", use_container_width=True)
    
    # Handle button actions
    if validate_button:
        validate_content()
    
    if generate_button:
        generate_presentation()
    
    if clear_button:
        st.session_state.content = ""
        st.session_state.validation_results = None
        st.rerun()
    
    # Show validation results
    if st.session_state.validation_results:
        st.markdown("---")
        st.markdown("### ðŸ” Validation Results")
        
        results = st.session_state.validation_results
        
        if results['success']:
            st.success(f"âœ… Found {results['slide_count']} slides")
            
            if results['issues']:
                st.warning(f"âš ï¸ {len(results['issues'])} issues found:")
                for issue in results['issues']:
                    st.write(f"  â€¢ {issue}")
            else:
                st.success("âœ… No issues found! Ready to generate.")
        else:
            st.error("âŒ Validation failed:")
            st.write(results['error'])


# ============================================================================
# QUICK REFERENCE
# ============================================================================

def show_reference():
    """Show quick reference guide"""
    st.header("ðŸ“– Quick Reference Guide")
    
    st.markdown(get_quick_reference())
    
    st.markdown("### Layout Types")
    
    st.markdown("**Single Column:**")
    st.code("Content: Main point", language="text")
    
    st.markdown("**Two Columns:**")
    st.code("Left: Left content\nRight: Right content", language="text")
    
    st.markdown("**Four Boxes:**")
    st.code("LeftTop: Content\nRightTop: Content\nLeftBottom: Content\nRightBottom: Content", language="text")
    
    st.markdown("### Style Tags")
    st.markdown("""
- `[vocabulary]` - Custom color (set in sidebar)
- `[question]` - Custom color (set in sidebar)
- `[answer]` - Custom color (set in sidebar)
- `[emphasis]` - Custom color (set in sidebar)
- `[step]` - Creates animation steps
""")


def get_ai_instructions():
    """
    Return the full AI Instruction File for human users.
    This file is downloaded via the Help tab so users can give it directly
    to ChatGPT, Claude, Gemini, etc., to create content manually.
    """
    return """================================================================================
AI INSTRUCTIONS: PowerPoint Generator Content Format 
================================================================================

PURPOSE
--------
You are creating English lesson content for the Universal PowerPoint Generator.
The goal is to produce text-based lesson slides that the generator can automatically
convert into PowerPoint format with correct layout and styling.

================================================================================
âš ï¸  CRITICAL TAG USAGE 
================================================================================

**INLINE TAGS MUST BE EXPLICITLY CLOSED**

The system now requires that all inline style tags wrap ONLY the exact word or 
phrase you want to style. Tags will NO LONGER capture multiple words automatically.

âœ… CORRECT - Explicit closing tags:
Content: The student [answer]completed[/answer] the task.
Content: [question]Have you ever traveled abroad?[/question]
Content: He used the [vocabulary]Present Perfect[/vocabulary] tense.
Content: [emphasis]Never forget[/emphasis] to add the final -ed.

âŒ INCORRECT - Will only style ONE word:
Content: [answer] completed the task  â† Only "completed" will be styled!
Content: [emphasis] Never forget      â† Only "Never" will be styled!

================================================================================
FORMAT OVERVIEW
================================================================================

1ï¸âƒ£ Every slide must start with:
   Slide X
   Title: [your slide title]

2ï¸âƒ£ Content must use one of the following layout types:
   - Single column â†’ Content:
   - Two columns â†’ Left: / Right:
   - Four boxes â†’ LeftTop:, RightTop:, LeftBottom:, RightBottom:

3ï¸âƒ£ Each slide ends (optionally) with a separator:
   ---

4ï¸âƒ£ Every slide MUST have:
   - A Title line
   - At least one content section
   - Notes: (teacher instructions, timing, etc.)

5ï¸âƒ£ Titles must be under 60 characters.

================================================================================
LAYOUT TYPES
================================================================================

âœ… **SINGLE COLUMN**
For objectives, introductions, or explanations.

Slide 1
Title: Lesson Objectives
Content: [emphasis]Lesson 1[/emphasis] â€“ Past Simple
Content: [step] Talk about past experiences
Content: [step] Describe completed actions
Notes: Review previous session briefly. 5 mins.

---

âœ… **TWO COLUMNS**
For vocabulary, comparisons, or short Q&A.

Slide 2
Title: Vocabulary â€“ Travel Verbs
Left: [vocabulary]book[/vocabulary]
Right: to arrange a ticket, hotel, or flight
Left: [vocabulary]pack[/vocabulary]
Right: to put things in a bag for travel
Notes: Drill pronunciation and example sentences.

---

âœ… **FOUR BOXES**
For grammar, structured topics, or examples.

Slide 3
Title: Grammar â€“ Past Simple
LeftTop: [emphasis]FORM[/emphasis]
LeftTop: Subject + Verb (-ed or irregular)
RightTop: [emphasis]USE[/emphasis]
RightTop: Finished actions in finished time
LeftBottom: [emphasis]EXAMPLES[/emphasis]
LeftBottom: â€¢ I [answer]went[/answer] to France in 2018.
RightBottom: [emphasis]TIME MARKERS[/emphasis]
RightBottom: â€¢ yesterday â€¢ last week â€¢ in 2010
Notes: Elicit examples. Clarify difference between regular/irregular verbs.

---

âœ… **READING COMPREHENSION**
Use LeftTop for passage, LeftBottom for questions.

Slide 4
Title: Reading â€“ Weekend Plans
LeftTop: Last weekend I visited my grandparents. We cooked together and watched a film.
LeftBottom: [question]What did the writer do last weekend?[/question]
LeftBottom: [question]Who did they visit?[/question]
Notes: Read aloud, check comprehension, highlight past tense verbs.

================================================================================
STYLE TAGS - EXPLICIT CLOSING REQUIRED
================================================================================

âœ… Supported tags:
[vocabulary]...[/vocabulary]   â†’ new terms
[question]...[/question]       â†’ learner prompts  
[answer]...[/answer]           â†’ model answers
[emphasis]...[/emphasis]       â†’ important points
[step]                         â†’ sequential reveal (no closing tag needed)

================================================================================
INLINE TAG RULES (UPDATED)
================================================================================

**Rule 1: Always use explicit closing tags for words/phrases you want styled**

âœ… CORRECT Examples:
Content: The student [answer]completed[/answer] the task.
Content: [question]Have you ever traveled abroad?[/question]
Content: Use the [vocabulary]Present Perfect[/vocabulary] tense.
Content: [emphasis]Never[/emphasis] forget the -ed ending.
Left: [vocabulary]resilient[/vocabulary]
Right: able to recover quickly from difficulties

**Rule 2: Tags wrap the EXACT content to be styled**

âœ… Style one word:
[answer]completed[/answer]

âœ… Style multiple words:
[vocabulary]Present Perfect[/vocabulary]

âœ… Style entire question:
[question]What is your favorite color?[/question]

**Rule 3: Do NOT use open-only tags expecting multi-word capture**

âŒ WRONG:
Content: [emphasis] This will not style the whole phrase

âœ… CORRECT:
Content: [emphasis]This will style the whole phrase[/emphasis]

**Rule 4: For [step] tags, no closing tag is needed**

âœ… CORRECT:
Content: [step] First point
Content: [step] Second point
Content: [step] Third point

**Rule 5: Never double-wrap or repeat tags**

âŒ WRONG:
[emphasis][emphasis]word[/emphasis][/emphasis]
[emphasis] word [emphasis]

âœ… CORRECT:
[emphasis]word[/emphasis]

================================================================================
COMPLETE EXAMPLES BY USE CASE
================================================================================

**Example 1: Vocabulary Slide**
```
Slide 2
Title: Key Business Vocabulary
Left: [vocabulary]delegate[/vocabulary]
Right: to give tasks or responsibilities to others
Left: [vocabulary]prioritize[/vocabulary]
Right: to arrange tasks by importance
Left: [vocabulary]collaborate[/vocabulary]
Right: to work together with others
Notes: Drill pronunciation. Check understanding with example sentences.

---
```

**Example 2: Grammar Explanation**
```
Slide 3
Title: Past Simple - Negative Form
LeftTop: [emphasis]STRUCTURE[/emphasis]
LeftTop: Subject + did not + base verb
RightTop: [emphasis]EXAMPLES[/emphasis]
RightTop: â€¢ I [answer]did not go[/answer] to work yesterday.
RightTop: â€¢ She [answer]didn't travel[/answer] last month.
LeftBottom: [emphasis]CONTRACTIONS[/emphasis]
LeftBottom: did not = didn't
RightBottom: [emphasis]COMMON ERRORS[/emphasis]
RightBottom: âŒ I didn't went
RightBottom: âœ… I didn't go
Notes: Emphasize the base form after 'didn't'. Practice with error correction.

---
```

**Example 3: Discussion Questions**
```
Slide 4
Title: Speaking Activity
Content: [emphasis]Think-Pair-Share[/emphasis]
Content: 
Content: [question]Have you ever worked abroad?[/question]
Content: [question]What challenges did you face?[/question]
Content: [question]Would you do it again?[/question]
Content: 
Content: [step] Think individually (1 minute)
Content: [step] Discuss with partner (3 minutes)
Content: [step] Share with class (5 minutes)
Notes: Monitor for accurate past tense usage. Encourage follow-up questions.

---
```

**Example 4: Reading Comprehension**
```
Slide 5
Title: Reading - Career Change
LeftTop: Maria decided to change careers at age 35. She left her job in banking to become a teacher. It was difficult at first, but she felt happier. Now she helps young people learn English.
LeftBottom: [question]What was Maria's previous job?[/question]
LeftBottom: [question]How old was she when she changed careers?[/question]
LeftBottom: [question]What does Maria teach now?[/question]
Notes: Pre-teach: career change, banking, difficult. Read aloud, then students answer in pairs.

---
```

================================================================================
NOTES
================================================================================
- Always include Notes: at the end of each slide.
- Include:
  â€¢ Timing estimate (e.g., "5 minutes")
  â€¢ Activity type (e.g., pair work, class discussion)
  â€¢ Teaching tips, e.g., "Drill pronunciation", "Monitor accuracy"
  â€¢ Optional: image or activity suggestions

Example:
Notes: Pair work 5 minutes. Encourage full sentences. Monitor for correct past tense.

================================================================================
COMMON MISTAKES TO AVOID
================================================================================
âŒ Missing "Slide X" or "Title:"
âŒ Mixing Left/Right with LeftTop/RightTop on the same slide
âŒ Forgetting Notes:
âŒ Including image filenames or PowerPoint animation settings
âŒ Using markdown symbols (#, **, -, etc.)
âŒ Writing too much text per box (keep it concise)
âŒ Using open-only tags like [emphasis] without closing them
âŒ Expecting [tag] word to style multiple words

================================================================================
OUTPUT STRUCTURE SUMMARY
================================================================================
Slide 1 â€“ Title + Objectives  
Slide 2 â€“ Lead-in Discussion  
Slide 3 â€“ Reading + Questions  
Slide 4 â€“ Vocabulary  
Slide 5 â€“ Grammar Explanation  
Slide 6 â€“ Controlled Practice  
Slide 7 â€“ Speaking/Production  
Slide 8 â€“ Recap + Homework  

================================================================================
TAG USAGE SUMMARY
================================================================================

âœ… DO:
- Use explicit closing tags: [tag]content[/tag]
- Wrap exact words/phrases you want styled
- Use [step] without closing tag for animations
- Put Notes: on every slide

âŒ DON'T:
- Use open-only tags expecting multi-word capture
- Forget closing tags
- Double-wrap tags
- Mix layout types on same slide

================================================================================
QUALITY CHECKLIST
================================================================================
Before outputting your lesson, verify:

âœ… Every slide starts with "Slide X"
âœ… Every slide has "Title:"
âœ… All inline tags have proper closing tags (except [step])
âœ… Every slide has "Notes:"
âœ… Slide separator "---" between slides
âœ… No markdown formatting (##, **, -, etc.)
âœ… Appropriate layout chosen for content type
âœ… Text length suitable for slide (not too long)
âœ… Grammar and vocabulary appropriate for stated level
âœ… Activities match stated duration

================================================================================
END OF INSTRUCTIONS
================================================================================
Start your output immediately with "Slide 1".
Do not include any introductions, explanations, or commentary.
Output ONLY the formatted lesson content.
"""



def get_gemini_instructions():
    """Return GEMINI-SPECIFIC instruction file content - NO TAGS VERSION"""
    return """================================================================================
GEMINI-SPECIFIC INSTRUCTIONS: PowerPoint Generator Content Format
================================================================================

PURPOSE: You are creating lesson content for the PowerPoint Generator.
This is a SIMPLIFIED version specifically for Gemini - NO STYLE TAGS USED.

IMPORTANT: This version does NOT use style tags like [vocabulary], [emphasis], etc.
Those are for other AI models. Gemini creates clean, plain text content.

================================================================================
CRITICAL FORMATTING RULES
================================================================================

1. EVERY slide must start with "Slide X" (where X is any number)
2. EVERY slide must have "Title: [text]"
3. Content is organized in sections: Content:, Left:, Right:, etc.
4. Use "---" to separate slides (optional but recommended)
5. Multiple lines under the same section are allowed
6. Lines starting with "#" are comments (ignored)

================================================================================
CONTENT SECTIONS
================================================================================

Content:        Single column content (default layout)
Left:           Left column in two-column layout
Right:          Right column in two-column layout
LeftTop:        Top-left box in four-box layout
RightTop:       Top-right box in four-box layout
LeftBottom:     Bottom-left box in four-box layout
RightBottom:    Bottom-right box in four-box layout
Notes:          Teacher notes (not visible on slides)

================================================================================
FLEXIBLE LAYOUTS - YOU CAN MIX SECTIONS!
================================================================================

The system now supports MIXING layout types on one slide:

✅ ALLOWED COMBINATIONS:
   • Content + Left/Right (intro text above two columns)
   • Content + Four boxes (intro text above four sections)
   • Content only (traditional single column)
   • Left/Right only (traditional two columns)
   • Four boxes only (traditional grid)
   • Reading layout (LeftTop=passage, LeftBottom=questions only)

The system automatically stacks sections vertically:
- Content section (if present): Gets 30% of space at TOP
- Main section (columns/boxes): Gets 70% of space at BOTTOM

EXAMPLE:
```
Slide 2
Title: Grammar Overview
Content: Use Past Simple for finished actions in the past.
Content: Common time markers: yesterday, last week, in 2020.
LeftTop: FORM: Subject + Verb-ed (regular) or irregular form
RightTop: EXAMPLES: I visited London. She went to Paris.
LeftBottom: TIME MARKERS: yesterday, last week, in 2010, ago
RightBottom: COMMON ERRORS: I didn't went ❌ → I didn't go ✅
```

This creates:
- Introduction text at top (30%)
- Four grammar boxes below (70%)

================================================================================
TEXT FORMATTING - NO STYLE TAGS!
================================================================================

IMPORTANT: Do NOT use style tags like [vocabulary], [emphasis], [question], etc.
Those are for other AI models only.

Instead, use natural text formatting:

FOR VOCABULARY TERMS:
  ❌ Don't use: [vocabulary] resilience
  ✅ Do use: resilience (meaning: ability to recover)
  ✅ Or use: **resilience** (if you want emphasis)
  ✅ Or use: RESILIENCE (all caps for emphasis)

FOR IMPORTANT POINTS:
  ❌ Don't use: [emphasis] Remember this!
  ✅ Do use: REMEMBER THIS! (all caps)
  ✅ Or use: **Remember this!** (bold-style text)
  ✅ Or use: → Remember this! (with arrow)

FOR QUESTIONS:
  ❌ Don't use: [question] What do you think?
  ✅ Do use: QUESTION: What do you think?
  ✅ Or use: Q: What do you think?
  ✅ Or use: 💬 What do you think? (with emoji)

FOR ANSWERS:
  ❌ Don't use: [answer] This is the answer
  ✅ Do use: ANSWER: This is the answer
  ✅ Or use: A: This is the answer
  ✅ Or use: → This is the answer (with arrow)

NATURAL EMPHASIS:
  • Use CAPITAL LETTERS for emphasis
  • Use bullet points for lists
  • Use numbers for sequences: 1. 2. 3.
  • Use arrows: → ← ↑ ↓
  • Use symbols: ✓ ✗ • ○ ★
  • Use emojis: 💡 🔑 ⚠️ ✅ ❌

================================================================================
ANIMATIONS - SIMPLE APPROACH
================================================================================

For sequential reveals, just number your points naturally:

GOOD:
```
Content: Today's Learning Objectives:
Content: 1. Understand Past Simple structure
Content: 2. Practice with time markers
Content: 3. Compare with Present Perfect
```

BAD:
```
Content: [step] Understand Past Simple
Content: [step] Practice with time markers
```
(NO [step] tags!)

The presentation will display all points together, which is fine for most lessons.
You can add animations manually in PowerPoint later if needed.

================================================================================
LAYOUT SELECTION LOGIC
================================================================================

USE Content: FOR:
- Simple slides with one main message
- Title slides with objectives
- Instructions
- Single-topic explanations
- Introduction text above other layouts

USE Left: and Right: FOR:
- Vocabulary (word | definition)
- Comparisons (before | after)
- Advantages vs Disadvantages
- Theory vs Practice
- Two contrasting concepts

USE LeftTop:, RightTop:, LeftBottom:, RightBottom: FOR:
- Four related concepts (4 project phases, 4 skills, 4 tenses)
- Grammar explanations with examples and practice
- Pros/cons with solutions/alternatives
- Four categories of vocabulary

USE LeftTop: (passage) and LeftBottom: (questions) ONLY FOR:
- Reading comprehension (passage at top, questions at bottom)
- Case studies with questions
- Longer texts with follow-up

MIXING LAYOUTS:
- Use Content: for a brief intro (1-3 lines)
- Then use Left:/Right: OR four-box layout for main content
- System automatically stacks them vertically

================================================================================
CONTENT LENGTH GUIDELINES
================================================================================

Slide Titles:       Max 60 characters
Single Column:      Up to 500 characters per slide
Two Columns:        Up to 300 characters per column
Four Boxes:         Up to 150 characters per box
Reading Passages:   800-1000 characters (150-250 words)
Questions:          3-5 questions per slide maximum
Vocabulary Items:   4-6 terms per slide

Content Section (when mixing):
  Keep brief!       1-3 lines maximum
  Purpose:          Introduction/context for main content below

IMPORTANT: Long text automatically reduces font size, but there are limits!

================================================================================
IMAGES & ANIMATIONS - HANDLE IN POWERPOINT
================================================================================

DO NOT INCLUDE IMAGE REFERENCES OR ANIMATION SPECS IN YOUR CONTENT FILE.

Instead:
✓ Generate clean text-based slides
✓ Add images later in PowerPoint using Insert > Pictures
✓ Recommended: Use stock photo sites like Unsplash, Pexels, Pixabay
✓ Add animations in PowerPoint using the Animations tab
✓ Simple, clean content is better than complex formatting

Why this approach is better:
- Easier to find and place images in PowerPoint
- More control over image sizing and positioning
- Access to PowerPoint's full animation suite
- Can use built-in stock images (Insert > Stock Images)
- Easier to update and modify later

================================================================================
LESSON STRUCTURE TEMPLATE
================================================================================

A well-structured lesson should follow this pattern:

Slide 1: Title + Objectives
```
Slide 1
Title: Professional Email Writing - Lesson 1
Content: LESSON FOCUS: Business Communication Skills
Content: 
Content: Today's Learning Objectives:
Content: 1. Email structure and conventions
Content: 2. Professional language and tone
Content: 3. Common business phrases
Notes: Warm-up about email challenges. 5 minutes.
```

Slide 2: Lead-in / Discussion
```
Slide 2
Title: Discussion Questions
Content: THINK ABOUT:
Content: • How many emails do you write per week?
Content: • What makes a professional email effective?
Content: • What are common mistakes you've seen?
Notes: Pair discussion 3 minutes. Elicit responses.
```

Slide 3: Vocabulary (Two-Column)
```
Slide 3
Title: Key Vocabulary
Left: **formal** (adj.)
Left: following official rules or customs
Left: 
Left: **concise** (adj.)
Left: giving information clearly with few words
Right: **recipient** (n.)
Right: the person who receives something
Right: 
Right: **subject line** (n.)
Right: the title/summary of an email
Notes: Drill pronunciation. Check understanding with CCQs.
```

Slide 4: Reading / Case Study (with intro)
```
Slide 4
Title: Email Example Analysis
Content: Read the email below. What makes it professional?
LeftTop: Dear Mr. Johnson, I am writing to follow up on our meeting last Tuesday regarding the marketing proposal. As discussed, I have attached the revised document for your review. Please let me know if you have any questions or require further information. I look forward to hearing from you. Best regards, Sarah Chen
LeftBottom: Q1: What is the purpose of this email?
LeftBottom: Q2: What makes the tone professional?
LeftBottom: Q3: Find three formal phrases.
Notes: Read aloud once. Students answer in pairs. 7 minutes.
```

Slide 5: Grammar / Language Focus (Four-Box with intro)
```
Slide 5
Title: Professional Email Phrases
Content: ESSENTIAL PHRASES for business emails:
LeftTop: OPENING PHRASES
LeftTop: • I am writing to...
LeftTop: • Thank you for...
LeftTop: • Following up on...
RightTop: CLOSING PHRASES
RightTop: • Please let me know...
RightTop: • I look forward to...
RightTop: • Best regards / Kind regards
LeftBottom: REQUESTING INFORMATION
LeftBottom: • Could you please...?
LeftBottom: • I would appreciate if...
LeftBottom: • Would it be possible to...?
RightBottom: PROVIDING INFORMATION
RightBottom: • I am pleased to inform you...
RightBottom: • Please find attached...
RightBottom: • As requested, I have...
Notes: Copy these into notebooks. Practice in next activity. 10 minutes.
```

Slide 6: Practice Activity
```
Slide 6
Title: Writing Practice
Content: TASK: Write a professional email
Content: 
Content: Situation: You need to request a meeting with your manager.
Content: 
Content: Include:
Content: • Appropriate greeting
Content: • Clear purpose
Content: • Polite request
Content: • Professional closing
Notes: Individual writing 12 minutes. Peer review 5 minutes.
```

Slide 7: Common Errors
```
Slide 7
Title: Common Mistakes to Avoid
Left: ❌ INFORMAL / WRONG
Left: • Hi buddy!
Left: • Wanna meet?
Left: • Thx!
Left: • URGENT!!!
Right: ✅ FORMAL / CORRECT
Right: • Dear Mr./Ms. [Name],
Right: • Would you be available to meet?
Right: • Thank you.
Right: • Important: [clear subject]
Notes: Discuss why these are problematic. 5 minutes.
```

Slide 8: Recap + Homework
```
Slide 8
Title: Summary & Homework
Content: TODAY WE LEARNED:
Content: ✓ Email structure and format
Content: ✓ Professional phrases and tone
Content: ✓ Common mistakes to avoid
Content: 
Content: HOMEWORK:
Content: Write two professional emails (scenarios provided in handout)
Content: Due: Next class
Notes: Review key points. Distribute homework handout. 3 minutes.
```

================================================================================
EXAMPLE COMPLETE SLIDE - MIXED LAYOUT
================================================================================

```
Slide 3
Title: Present Simple vs Present Continuous
Content: KEY DIFFERENCES between these two tenses:
Content: Use the chart below to compare form and usage.
LeftTop: PRESENT SIMPLE
LeftTop: Form: Subject + base verb (+ s/es)
LeftTop: Usage: Habits, routines, facts
LeftTop: Time words: always, usually, every day
RightTop: PRESENT CONTINUOUS
RightTop: Form: Subject + am/is/are + verb-ing
RightTop: Usage: Actions happening now
RightTop: Time words: now, at the moment, currently
LeftBottom: EXAMPLES - Present Simple
LeftBottom: • I work in an office. (permanent)
LeftBottom: • She drinks coffee every morning. (habit)
LeftBottom: • The sun rises in the east. (fact)
RightBottom: EXAMPLES - Present Continuous
RightBottom: • I am working from home today. (temporary)
RightBottom: • She is drinking coffee right now. (happening now)
RightBottom: • The sun is shining at the moment. (current)
Notes: Highlight the differences. Elicit more examples. CCQ: "Do we use Present Simple for temporary situations?" (No). 8 minutes.
```

This creates:
- Brief introduction at top (explanation of what students will see)
- Four comparison boxes below (organized comparison of two tenses)

================================================================================
TEACHER NOTES - ALWAYS INCLUDE
================================================================================

Every slide should have Notes: with:
- Timing estimate (e.g., "5 minutes")
- Interaction type (pair work, whole class, individual)
- Key instructions for teacher
- Common errors to watch for
- Extension activities if time permits
- CCQs (Concept Checking Questions)

EXAMPLE:
```
Notes: Elicit answers first. Drill pronunciation. CCQ: "Is this action happening now?" (for Present Simple - No). Give 2 min for pair discussion. Monitor for present simple errors. 8-10 minutes total. Extension: Students create their own sentences.
```

================================================================================
COMMON MISTAKES TO AVOID
================================================================================

❌ Using style tags: [emphasis], [vocabulary], [question], [answer], [step]
   (These are for other AI models, not Gemini!)

❌ Forgetting "Slide X" at the start

❌ Missing "Title:" on any slide

❌ Using wrong section names (e.g., "LeftSide:" instead of "Left:")

❌ Too much text in four-box layouts (>150 chars per box)

❌ Too much text in Content: when mixing layouts (keep to 1-3 lines)

❌ Forgetting teacher notes

❌ Including image file references (handle in PowerPoint instead)

❌ Trying to specify complex animations (use PowerPoint instead)

✅ Using capital letters, bold markers (**text**), arrows, and emojis for emphasis

✅ Using natural text formatting instead of style tags

✅ Keeping Content: brief when mixing with other layouts

================================================================================
TEXT EMPHASIS TECHNIQUES FOR GEMINI
================================================================================

Instead of style tags, use these natural formatting techniques:

1. CAPITAL LETTERS for emphasis:
   ```
   Content: IMPORTANT: Always check your work!
   ```

2. Bold markers (asterisks):
   ```
   Content: This is **very important** to remember.
   ```

3. Symbols and arrows:
   ```
   Content: → Key point: Practice makes perfect
   Content: ★ Essential vocabulary: resilience
   Content: ✓ Correct answer
   Content: ✗ Incorrect answer
   ```

4. Emojis for visual markers:
   ```
   Content: 💡 TIP: Use context clues
   Content: ⚠️ WARNING: Common mistake ahead
   Content: 🔑 KEY CONCEPT: Past Simple vs Present Perfect
   Content: ✅ DO: Check your spelling
   Content: ❌ DON'T: Forget the past participle
   ```

5. Labels and prefixes:
   ```
   Content: VOCABULARY: resilience (n.) - ability to recover
   Content: QUESTION: How do we form the past tense?
   Content: ANSWER: Add -ed to regular verbs
   Content: EXAMPLE: I walked to school yesterday.
   Content: FORM: Subject + verb-ed
   Content: TIP: Look for time markers
   ```

6. Section headers within content:
   ```
   LeftTop: **ADVANTAGES**
   LeftTop: • Easy to learn
   LeftTop: • Widely used
   
   RightTop: **DISADVANTAGES**
   RightTop: • Can be confusing
   RightTop: • Requires practice
   ```

================================================================================
CONTENT GENERATION CHECKLIST
================================================================================

Before submitting content, verify:
□ Every slide starts with "Slide X"
□ Every slide has "Title: [text]"
□ Appropriate layout chosen for content type
□ NO style tags used ([vocabulary], [emphasis], [question], [answer], [step])
□ Natural formatting used instead (CAPITALS, arrows, emojis, labels)
□ Teacher notes included on every slide
□ Content length appropriate (not too long)
□ When mixing layouts, Content: section is brief (1-3 lines)
□ Slides separated with "---"
□ 8-10 slides total per lesson
□ NO image references (add those in PowerPoint later)
□ NO complex animation specs (handle in PowerPoint)

================================================================================
LEVEL-SPECIFIC GUIDELINES
================================================================================

A1-A2 (Beginner):
- Simple vocabulary and short sentences
- More visual content descriptions in notes
- 6-8 slides per lesson
- Use emojis and symbols for clarity

B1-B2 (Intermediate):
- Moderate complexity vocabulary
- Longer reading passages (150-200 words)
- 8-10 slides per lesson
- Mix layouts for better organization

C1-C2 (Advanced):
- Advanced vocabulary and idioms
- Complex texts (200-250 words)
- 10-12 slides per lesson
- Sophisticated content organization

================================================================================
OUTPUT FORMAT
================================================================================

Your output should be plain text starting with:

```
# Lesson Name
# Level: XX | Duration: XX minutes

Slide 1
Title: ...
Content: ...
Notes: ...

---

Slide 2
...
```

================================================================================
SUMMARY FOR GEMINI
================================================================================

KEY DIFFERENCES from other AI instructions:

1. ❌ NO style tags: [vocabulary], [emphasis], [question], [answer], [step]
2. ✅ USE natural formatting: CAPITALS, **bold**, arrows, emojis, labels
3. ✅ CAN mix layouts: Content: + columns or Content: + four-box
4. ✅ Keep Content: brief when mixing (1-3 lines introduction)
5. ✅ Focus on clear, simple, well-organized content
6. ✅ Let PowerPoint handle images and advanced animations

Gemini creates CLEAN TEXT CONTENT.
The presentation generator handles all the formatting.
Keep it simple and well-organized!

================================================================================
END OF GEMINI-SPECIFIC INSTRUCTIONS
================================================================================
"""



def get_system_instructions():
    """
    Return strict machine-readable instructions for the AI model.
    Used internally when generating lessons automatically.
    """
    return """You are an expert English teacher creating formatted lesson slides
for a PowerPoint generator. Output must follow this structure exactly.

================================================================================
OUTPUT RULES
================================================================================

1ï¸âƒ£ Every slide begins with:
Slide X
Title: [your title]

2ï¸âƒ£ Use ONE layout per slide:
   â€¢ Content: (single column)
   â€¢ Left: / Right: (two columns)
   â€¢ LeftTop:, RightTop:, LeftBottom:, RightBottom: (four boxes)

3ï¸âƒ£ Separate slides with ---
4ï¸âƒ£ Each slide MUST include:
   - A Title
   - At least one content section
   - Notes: (teacher guidance)

5ï¸âƒ£ Do NOT include explanations, markdown, or image references.
6ï¸âƒ£ Use â€¢ for bullet points, not - or *.
7ï¸âƒ£ Keep titles under 60 characters.

================================================================================
STYLE TAGS
================================================================================

âœ… Supported tags:
[vocabulary]...[/vocabulary]   â†’ new terms
[question]...[/question]       â†’ learner prompts
[answer]...[/answer]           â†’ model answers
[emphasis]...[/emphasis]       â†’ important points
[step]                         â†’ sequential reveal

âœ… Inline syntax is REQUIRED:
Each tag must open and close around the exact word or phrase, e.g.:

The student [answer]completed[/answer] the task.
[question]Have you ever traveled abroad?[/question]
He used the [vocabulary]Present Perfect[/vocabulary] tense.
[emphasis]Never forget[/emphasis] to add the final -ed.

âŒ Do NOT leave tags unclosed like "[emphasis] word".
âŒ Do NOT repeat tags twice around the same word.

âœ… If unsure, always output them as closed tags [tag]word[/tag].


================================================================================
LAYOUT EXAMPLES
================================================================================

SINGLE COLUMN
-------------
Slide 1
Title: Objectives
Content: [emphasis]Lesson 1[/emphasis] â€” Past Simple
Content: [step] Describe completed actions
Content: [step] Talk about life experiences
Notes: Review previous session. 5 mins.

---

TWO COLUMNS
------------
Slide 2
Title: Vocabulary â€“ Work Verbs
Left: [vocabulary]manage[/vocabulary]
Right: to be responsible for a team or project
Left: [vocabulary]attend[/vocabulary]
Right: to go to a meeting or event
Notes: Check pronunciation. Ask for examples.

---

FOUR BOXES
-----------
Slide 3
Title: Grammar â€“ Past Simple
LeftTop: [emphasis]FORM[/emphasis]
LeftTop: Subject + Verb (-ed or irregular)
RightTop: [emphasis]USE[/emphasis]
RightTop: Finished actions in finished time
LeftBottom: [emphasis]EXAMPLES[/emphasis]
LeftBottom: I [answer]went[/answer] to France in 2018.
RightBottom: [emphasis]TIME MARKERS[/emphasis]
RightBottom: yesterday, last week, in 2010
Notes: Clarify rule and give examples.

================================================================================
DO NOT INCLUDE
================================================================================
âŒ Markdown (##, **, -, etc.)
âŒ Image or animation instructions
âŒ Mixing layout types
âŒ Empty slides

================================================================================
END
================================================================================
Start your output immediately with "Slide 1".
"""


def show_help_section():
    """Show comprehensive help - now with AI Generator tab"""
    st.header("ℹ️ Help & Documentation")
    
    # Create tabs for different help sections
    help_tab1, help_tab2, help_tab3 = st.tabs([
        "📖 Content Format Guide", 
        "🤖 AI Generator Guide",
        "🎨 Images & Animations"
    ])
    
    # ===== TAB 1: Content Format Guide =====
    with help_tab1:
        st.markdown("### 🤖 Use AI to Create Lesson Content")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Standard Version (ChatGPT, Claude)")
            st.info("💡 **Best for:** ChatGPT, Claude, other AIs that handle tags well")
            
            st.download_button(
                label="📥 Download Standard Instructions",
                data=get_ai_instructions(),
                file_name="AI_Instructions_PowerPoint_Generator.txt",
                mime="text/plain",
                help="Use with ChatGPT, Claude, and other AI models"
            )
            
            st.markdown("""
            **Features:**
            - ✅ Style tags: `[vocabulary]`, `[emphasis]`, etc.
            - ✅ Precise color control
            - ✅ Automatic styling
            """)
        
        with col2:
            st.markdown("#### Gemini Version (No Tags)")
            st.info("💡 **Best for:** Google Gemini - avoids tag errors completely")
            
            st.download_button(
                label="📥 Download GEMINI Instructions (No Tags)",
                data=get_gemini_instructions(),
                file_name="AI_Instructions_GEMINI_NoTags.txt",
                mime="text/plain",
                help="Use this version for Gemini - simpler, no style tags"
            )
            
            st.markdown("""
            **Features:**
            - ✅ NO style tags (avoids errors)
            - ✅ Natural formatting (CAPITALS, **bold**, emojis)
            - ✅ 100% reliable with Gemini
            """)
        
        st.markdown("---")
        
        # Quick reference
        st.markdown("### 📝 Quick Format Reference")
        
        with st.expander("Basic Slide Structure"):
            st.code("""Slide 1
Title: Your Title Here
Content: Your content
Notes: Teacher notes
---

Slide 2
Title: Next Slide
Content: More content
---""", language="text")
        
        with st.expander("Layout Types"):
            st.markdown("""
            **Single Column:**
            ```
            Content: Line 1
            Content: Line 2
            ```
            
            **Two Columns:**
            ```
            Left: Left content
            Right: Right content
            ```
            
            **Four Boxes:**
            ```
            LeftTop: Box 1
            RightTop: Box 2
            LeftBottom: Box 3
            RightBottom: Box 4
            ```
            
            **Mixed Layout (NEW!):**
            ```
            Content: Header text
            LeftTop: Box 1
            RightTop: Box 2
            LeftBottom: Box 3
            RightBottom: Box 4
            ```
            """)
        
        with st.expander("Style Tags (Standard Version Only)"):
            st.markdown("""
            - `[vocabulary]term[/vocabulary]` - Vocabulary terms
            - `[emphasis]text[/emphasis]` - Important points
            - `[question]text?[/question]` - Discussion questions
            - `[answer]text[/answer]` - Model answers
            - `[step]` - Sequential reveals (no closing tag)
            
            **Note:** Gemini version doesn't use these - uses natural formatting instead!
            """)
        
        with st.expander("Natural Formatting (Gemini Version)"):
            st.markdown("""
            Instead of tags, use:
            
            - **CAPITAL LETTERS** for emphasis
            - `**bold text**` with asterisks
            - 💡 🔑 ⚠️ ✅ ❌ 💬 Emojis
            - → ← ↑ ↓ Arrows
            - VOCABULARY: term definitions
            - QUESTION: discussion prompts
            - ANSWER: model responses
            """)
    
    # ===== TAB 2: AI Generator Guide =====
    with help_tab2:
        st.markdown("### 🤖 AI Content Generator - Complete Guide")
        
        st.info("""
        **Two ways to use AI:**
        1. **Built-in Generator** - Integrated in app (requires API key)
        2. **External AI** - Use ChatGPT/Claude/Gemini websites (free option)
        """)
        
        # Quick decision helper
        st.markdown("### 🤔 Which Method Should I Use?")
        
        method_col1, method_col2 = st.columns(2)
        
        with method_col1:
            st.markdown("""
            #### Built-in Generator
            
            **Use if:**
            - ✅ Generate 5+ lessons/week
            - ✅ Want fastest workflow
            - ✅ Willing to pay $0.01-0.10/lesson
            - ✅ Use Gemini (FREE API!)
            
            **Providers:**
            - OpenAI (ChatGPT): $0.01-0.05/lesson
            - Anthropic (Claude): $0.05/lesson
            - Google (Gemini): **FREE!**
            """)
        
        with method_col2:
            st.markdown("""
            #### External Copy/Paste
            
            **Use if:**
            - ✅ Occasional use (1-2 lessons/month)
            - ✅ Want to test first
            - ✅ Happy with manual workflow
            - ✅ Use free ChatGPT web
            
            **Free Options:**
            - ChatGPT (GPT-3.5): Unlimited
            - Claude: Limited messages/day
            - Gemini: Unlimited
            """)
        
        st.markdown("---")
        
        # API Setup Guide
        st.markdown("### 🔑 Getting API Keys")
        
        provider_tabs = st.tabs(["OpenAI (Recommended)", "Google (FREE!)", "Anthropic"])
        
        with provider_tabs[0]:
            st.markdown("""
            #### OpenAI API Setup
            
            **Best for:** Reliable, good value, handles tags well
            
            **Steps:**
            1. Go to https://platform.openai.com/signup
            2. Create account and verify email
            3. Add payment method at https://platform.openai.com/account/billing
            4. Add $5-10 credits (lasts for 50-100 lessons!)
            5. Create API key at https://platform.openai.com/api-keys
            6. Copy key (starts with `sk-...`)
            7. Paste in app settings
            
            **Recommended Model:** `gpt-4o-mini` (cheap + good quality)
            
            **Cost:** ~$0.01 per lesson
            """)
        
        with provider_tabs[1]:
            st.markdown("""
            #### Google Gemini API Setup ⭐ FREE!
            
            **Best for:** FREE unlimited usage!
            
            **Steps:**
            1. Go to https://aistudio.google.com/app/apikey
            2. Sign in with Google account
            3. Click "Create API Key"
            4. Choose project or create new
            5. Copy the key
            6. Paste in app settings
            
            **IMPORTANT:** Use GEMINI-SPECIFIC instructions (no tags)!
            
            **Recommended Model:** `gemini-1.5-flash` (fast + free)
            
            **Cost:** **FREE!** Up to 15 requests/minute
            
            ⚠️ **Note:** Must use Gemini version of instructions (no style tags)
            """)
        
        with provider_tabs[2]:
            st.markdown("""
            #### Anthropic Claude API Setup
            
            **Best for:** Best quality, perfect instruction following
            
            **Steps:**
            1. Go to https://console.anthropic.com
            2. Create account and verify email
            3. Add payment method and credits ($10+)
            4. Create API key at https://console.anthropic.com/settings/keys
            5. Copy key (starts with `sk-ant-...`)
            6. Paste in app settings
            
            **Recommended Model:** `claude-3-5-sonnet-20241022`
            
            **Cost:** ~$0.05 per lesson (expensive but excellent)
            """)
        
        st.markdown("---")
        
        # External AI Guide
        st.markdown("### 🌐 Using External AI (Free Method)")
        
        with st.expander("📝 Step-by-Step: ChatGPT Website"):
            st.markdown("""
            1. Go to https://chat.openai.com
            2. Sign up for free account
            3. Download "Standard Instructions" from this app
            4. Start new conversation in ChatGPT
            5. Paste instructions + your requirements:
               ```
               [Paste instruction file]
               
               Create a 60-minute B1 lesson about:
               - Topic: Past Simple vs Present Perfect
               - Include: vocabulary, examples, practice
               - 8-10 slides
               ```
            6. Copy ChatGPT's output
            7. Paste into this app's editor
            8. Validate and generate!
            
            **Free tier:** GPT-3.5 unlimited ✅
            """)
        
        with st.expander("🔵 Step-by-Step: Gemini Website (FREE)"):
            st.markdown("""
            1. Go to https://gemini.google.com
            2. Sign in with Google account
            3. Download "GEMINI-SPECIFIC Instructions" from this app
            4. Start new conversation
            5. Paste instructions + requirements:
               ```
               [Paste GEMINI instruction file]
               
               Create lesson about Past Simple for B1 students.
               60 minutes, 8-10 slides.
               
               IMPORTANT: Use natural formatting (CAPITALS, **bold**, emojis).
               NO style tags!
               ```
            6. Copy Gemini's output
            7. Paste into this app's editor
            8. Generate!
            
            **Free tier:** Unlimited! ✅
            """)
        
        st.markdown("---")
        
        # Troubleshooting
        st.markdown("### 🔧 Troubleshooting")
        
        with st.expander("❌ 'Invalid API Key' Error"):
            st.markdown("""
            **Solutions:**
            - Check key is copied completely (no spaces)
            - OpenAI keys start with `sk-...`
            - Claude keys start with `sk-ant-...`
            - Make sure you added payment method (if required)
            - Try regenerating the key
            """)
        
        with st.expander("⚠️ Gemini Tag Errors"):
            st.markdown("""
            **Problem:** Gemini creates unclosed tags like `[emphasis] text`
            
            **Solution:**
            ✅ Use GEMINI-SPECIFIC instructions (no tags version)!
            
            Download "GEMINI Instructions (No Tags)" from Tab 1.
            These instructions avoid style tags completely and use natural formatting instead.
            
            **Result:** Zero tag errors! 🎉
            """)
        
        with st.expander("🚫 'Rate Limit Exceeded'"):
            st.markdown("""
            **Solutions:**
            - Wait 1 minute and try again
            - OpenAI Tier 1: 3-5 requests/minute
            - Consider using Gemini (15 requests/minute free!)
            - Upgrade your tier with more credits
            """)
        
        st.markdown("---")
        
        # Quick Comparison
        st.markdown("### ⚖️ Provider Comparison")
        
        comparison_data = {
            "Provider": ["OpenAI (ChatGPT)", "Anthropic (Claude)", "Google (Gemini)"],
            "Cost": ["$0.01-0.05", "$0.05", "FREE!"],
            "Quality": ["⭐⭐⭐⭐", "⭐⭐⭐⭐⭐", "⭐⭐⭐"],
            "Tags": ["✅ Excellent", "✅ Perfect", "⚠️ Use no-tags"],
            "Best For": ["Most users", "Best quality", "Free option"]
        }
        
        st.table(comparison_data)
        
        st.success("""
        **💡 Recommendation:**
        - Testing: Use external ChatGPT (free)
        - Regular use: OpenAI API with gpt-4o-mini ($0.01/lesson)
        - Budget conscious: Gemini API (FREE!)
        - Best quality: Anthropic Claude ($0.05/lesson)
        """)
    
    # ===== TAB 3: Images & Animations =====
    with help_tab3:
        st.markdown("### 🎨 Adding Images & Animations")
        
        st.info("""
        **Best Practice:** Add images and animations AFTER generating your PowerPoint.
        
        This gives you more control and makes it easier to find the perfect visuals.
        """)
        
        img_col1, img_col2 = st.columns(2)
        
        with img_col1:
            st.markdown("#### 📷 Adding Images in PowerPoint")
            st.markdown("""
            **Steps:**
            1. Open your generated presentation
            2. Go to **Insert > Pictures**
            3. Choose from:
               - This Device (your files)
               - Stock Images (built-in)
               - Online Pictures (Bing search)
            4. Resize & position as needed
            
            **Recommended Stock Image Sites:**
            - [Unsplash](https://unsplash.com) - High quality, free
            - [Pexels](https://pexels.com) - Diverse photos & videos
            - [Pixabay](https://pixabay.com) - Photos, vectors, illustrations
            - PowerPoint's built-in stock images
            """)
        
        with img_col2:
            st.markdown("#### ✨ Adding Animations in PowerPoint")
            st.markdown("""
            **Steps:**
            1. Select the text or object
            2. Go to **Animations** tab
            3. Choose an animation effect
            4. Set timing and order
            
            **Popular Choices:**
            - Fade/Appear - subtle reveals
            - Fly In - dynamic entry
            - Wipe - directional reveal
            - Animation Pane - manage all animations
            
            **Note:** The `[step]` tag in your content creates basic text reveals automatically.
            """)
        
        st.markdown("---")
        
        st.markdown("### 📚 Full Documentation")
        
        st.markdown("""
        For complete documentation:
        - Download instruction files above
        - Check the README files in outputs folder
        - All features are documented with examples
        """)


def main():
    """Main application"""
    
    # Header
    st.markdown('<h1 class="main-header">ðŸŽ¨ Universal PowerPoint Generator</h1>', unsafe_allow_html=True)
    st.markdown("**Create customized educational presentations**")
    
    # Initialize session state
    if 'content' not in st.session_state:
        st.session_state.content = ""
    if 'validation_results' not in st.session_state:
        st.session_state.validation_results = None
    if 'custom_config' not in st.session_state:
        st.session_state.custom_config = DEFAULT_CONFIG.copy()
    if 'background_file' not in st.session_state:
        st.session_state.background_file = None
    
    # Sidebar with customization
    with st.sidebar:
        st.header("ðŸŽ¨ Customization")
        
        with st.expander("ðŸ“ Slide Design", expanded=True):
            # Background options
            bg_option = st.radio(
                "Background Type:",
                ["Solid Color", "Upload Image"]
            )
            
            if bg_option == "Solid Color":
                bg_color = st.color_picker(
                    "Background Color",
                    value=rgb_to_hex(st.session_state.custom_config["background_color"])
                )
                st.session_state.custom_config["background_color"] = hex_to_rgb(bg_color)
                st.session_state.custom_config["background_image"] = None
            
            else:  # Upload Image
                uploaded_bg = st.file_uploader(
                    "Upload Background Image",
                    type=['jpg', 'jpeg', 'png'],
                    help="Recommended: 1920x1080 or 1280x720"
                )
                
                if uploaded_bg:
                    bg_path = f"temp_background_{uploaded_bg.name}"
                    with open(bg_path, 'wb') as f:
                        f.write(uploaded_bg.read())
                    st.session_state.custom_config["background_image"] = bg_path
                    st.session_state.background_file = bg_path
                    st.success("âœ… Background uploaded")
        
        with st.expander("ðŸ”¤ Fonts & Colors", expanded=True):
            # Title
            st.subheader("Title")
            title_font = st.selectbox(
                "Title Font:",
                ["Arial", "Calibri", "Times New Roman", "Georgia", "Verdana", 
                 "Tahoma", "Trebuchet MS", "Comic Sans MS", "Impact", "Montserrat"],
                index=0
            )
            st.session_state.custom_config["title_font_name"] = title_font
            
            title_color = st.color_picker(
                "Title Color",
                value=rgb_to_hex(st.session_state.custom_config["title_color"])
            )
            st.session_state.custom_config["title_color"] = hex_to_rgb(title_color)
            
            # Body
            st.subheader("Body Text")
            body_font = st.selectbox(
                "Body Font:",
                ["Arial", "Calibri", "Times New Roman", "Georgia", "Verdana", 
                 "Tahoma", "Trebuchet MS", "Comic Sans MS", "Montserrat"],
                index=0
            )
            st.session_state.custom_config["font_name"] = body_font
            
            text_color = st.color_picker(
                "Text Color",
                value=rgb_to_hex(st.session_state.custom_config["text_color"])
            )
            st.session_state.custom_config["text_color"] = hex_to_rgb(text_color)
        
        with st.expander("ðŸŽ¯ Style Tags", expanded=False):
            st.info("Customize colors for [vocabulary], [question], [answer], [emphasis] tags")
            
            vocab_color = st.color_picker(
                "[vocabulary] Color",
                value=rgb_to_hex(st.session_state.custom_config["styles"]["vocabulary"]["color"])
            )
            st.session_state.custom_config["styles"]["vocabulary"]["color"] = hex_to_rgb(vocab_color)
            
            question_color = st.color_picker(
                "[question] Color",
                value=rgb_to_hex(st.session_state.custom_config["styles"]["question"]["color"])
            )
            st.session_state.custom_config["styles"]["question"]["color"] = hex_to_rgb(question_color)
            
            answer_color = st.color_picker(
                "[answer] Color",
                value=rgb_to_hex(st.session_state.custom_config["styles"]["answer"]["color"])
            )
            st.session_state.custom_config["styles"]["answer"]["color"] = hex_to_rgb(answer_color)
            
            emphasis_color = st.color_picker(
                "[emphasis] Color",
                value=rgb_to_hex(st.session_state.custom_config["styles"]["emphasis"]["color"])
            )
            st.session_state.custom_config["styles"]["emphasis"]["color"] = hex_to_rgb(emphasis_color)
        
        with st.expander("âš™ï¸ Options", expanded=False):
            enable_numbers = st.checkbox(
                "Show slide numbers",
                value=st.session_state.custom_config.get("enable_slide_numbers", True)
            )
            st.session_state.custom_config["enable_slide_numbers"] = enable_numbers
            
            enable_warnings = st.checkbox(
                "Show overflow warnings",
                value=st.session_state.custom_config.get("enable_overflow_warnings", True)
            )
            st.session_state.custom_config["enable_overflow_warnings"] = enable_warnings
        
        st.markdown("---")
        # AI Generator section
        if AI_AVAILABLE:
            with st.expander("ðŸ¤– AI Content Generator", expanded=False):
                st.markdown("**Generate lessons with AI**")
                
                ai_provider = st.selectbox(
                    "AI Provider:",
                    ["None", "Google Gemini (Free!)", "OpenAI (GPT-4)", "Claude (Anthropic)"]
                )
                
                if ai_provider != "None":
                    api_key = st.text_input(
                        "API Key:",
                        type="password",
                        help="Your API key is stored only for this session"
                    )
                    
                    if ai_provider == "Google Gemini (Free!)":
                        st.info("ðŸ†“ Get free API key: [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)")
                    elif ai_provider == "OpenAI (GPT-4)":
                        st.info("ðŸ”‘ Get API key: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)")
                    elif ai_provider == "Claude (Anthropic)":
                        st.info("ðŸ”‘ Get API key: [console.anthropic.com](https://console.anthropic.com)")
                    
                    if api_key:
                        st.session_state.ai_provider = ai_provider
                        st.session_state.ai_key = api_key
                        st.success("âœ… API key configured")
                    else:
                        st.session_state.ai_provider = None
                        st.session_state.ai_key = None
                else:
                    st.session_state.ai_provider = None
                    st.session_state.ai_key = None
        
        st.markdown("---")
        
        if st.button("ðŸ”„ Reset to Defaults"):
            st.session_state.custom_config = DEFAULT_CONFIG.copy()
            st.rerun()
        
        if st.button("ðŸ“„ Load Sample"):
            st.session_state.content = get_sample_template()
            st.success("Sample loaded!")
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["âœï¸ Editor", "ðŸ“– Quick Reference", "â“ Help"])
    
    with tab1:
        show_editor()
    
    with tab2:
        show_reference()
    
    with tab3:
        show_help_section()


if __name__ == "__main__":
    main()