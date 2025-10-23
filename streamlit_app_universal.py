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
    st.warning(f"⚠️ Core generator not found. Preview and AI features still available.")
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
    st.success("✅ AI Content Generator loaded successfully!")
except ImportError as e:
    # AI features are optional
    PROMPT_TEMPLATES = {}
    st.info("💡 AI features not available. Install packages: pip install google-generativeai openai anthropic")

# Page configuration
st.set_page_config(
    page_title="Universal PowerPoint Generator",
    page_icon="🎨",
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

    # Convert bare [tag] word → [tag]word[/tag]
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
  • Content: single column
  • Left:/Right: two columns  
  • LeftTop/RightTop/
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
Content: • Point to consider 1
Content: • Point to consider 2
Content: • Point to consider 3
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
                <strong style="color: #F57F17;">📝 Teacher Notes:</strong>
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
        st.warning("⚠️ Please enter some content first")
        return
    
    if not GENERATOR_AVAILABLE:
        st.error("⚠️ Generator module not available")
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
        st.warning("⚠️ Please enter some content first")
        return
    
    if not GENERATOR_AVAILABLE:
        st.error("⚠️ Generator module not available")
        return
    
    try:
        with st.spinner("🎨 Generating presentation..."):
            temp_input = "temp_content.txt"
            with open(temp_input, 'w', encoding='utf-8') as f:
                f.write(st.session_state.content)
            
            temp_output = "temp_presentation.pptx"
            slides = parse_content_file(temp_input)
            build_presentation(slides, temp_output, st.session_state.custom_config)
            
            with open(temp_output, 'rb') as f:
                pptx_data = f.read()
            
            st.success("✅ Presentation generated successfully!")
            st.download_button(
                label="📥 Download PowerPoint",
                data=pptx_data,
                file_name="presentation.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
            
            if os.path.exists(temp_input):
                os.remove(temp_input)
            if os.path.exists(temp_output):
                os.remove(temp_output)
            
    except Exception as e:
        st.error(f"❌ Error generating presentation: {str(e)}")
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
            st.error("❌ Please configure AI provider and API key in sidebar")
            return
        
        with st.spinner(f"🤖 {provider} is generating your lesson..."):
            if "Gemini" in provider:
                content, error = generate_with_gemini(prompt, api_key, level, duration)
            elif "OpenAI" in provider:
                content, error = generate_with_openai(prompt, api_key, level, duration)
            elif "Claude" in provider:
                content, error = generate_with_claude(prompt, api_key, level, duration)
            else:
                content, error = None, "Unknown provider"
            
            if error:
                st.error(f"❌ Generation failed: {error}")
                st.info("💡 Tip: Try rephrasing your prompt or check your API key")
            elif content:
                st.session_state.content = content
                st.success("✅ Lesson generated! Content loaded into editor below.")
                st.info("👀 Review the content and click 'Generate PowerPoint' when ready")
                st.rerun()
            else:
                st.error("❌ No content generated. Please try again.")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
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
        with st.expander("🤖 Generate with AI", expanded=False):
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
                if st.button("✨ Generate Lesson", type="primary", disabled=not topic_prompt):
                    if not st.session_state.ai_key:
                        st.error("⚠️ Please add your API key in the sidebar")
                    else:
                        generate_lesson_with_ai(topic_prompt, level, duration)
            
            with col2:
                if st.session_state.get('ai_generating'):
                    st.info("🤖 AI is generating your lesson...")
    
    st.markdown("---")
    
    # File operations
   
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        uploaded_file = st.file_uploader("📂 Upload .txt file", type=['txt'])
        if uploaded_file is not None:
            content = uploaded_file.read().decode('utf-8')
            st.session_state.content = content
            st.success(f"Loaded: {uploaded_file.name}")
    
    with col2:
        if st.session_state.content:
            st.download_button(
                label="💾 Download .txt",
                data=st.session_state.content,
                file_name="lesson_content.txt",
                mime="text/plain"
            )
    
    # Two column layout: Editor + Preview
    editor_col, preview_col = st.columns([1, 1])
    
    with editor_col:
        st.markdown("### ✏️ Edit Content")
        content = st.text_area(
            "Content Editor",
            value=st.session_state.content,
            height=500,
            help="Write your lesson content here",
            label_visibility="collapsed"
        )
        st.session_state.content = content
    
    with preview_col:
        st.markdown("### 👁️ Live Preview")
        
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
                            if st.button("⬅️ Previous"):
                                st.rerun()
                    with nav_col3:
                        if selected < len(slides) - 1:
                            if st.button("Next ➡️"):
                                st.rerun()
                    
                    st.info(f"📊 Total slides: {len(slides)}")
                else:
                    st.warning("No slides found. Start with:\n```\nSlide 1\nTitle: Your Title\nContent: Your content\n```")
            except Exception as e:
                st.error(f"Preview error: {str(e)}")
                st.info("Check your syntax and try again")
        else:
            st.info("👈 Start typing to see preview")
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
        validate_button = st.button("✅ Validate Content", use_container_width=True)
    
    with col2:
        generate_button = st.button("🎨 Generate PowerPoint", 
                                    type="primary", 
                                    use_container_width=True,
                                    disabled=not GENERATOR_AVAILABLE)
    
    with col3:
        clear_button = st.button("🗑️ Clear All", use_container_width=True)
    
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
        st.markdown("### 🔍 Validation Results")
        
        results = st.session_state.validation_results
        
        if results['success']:
            st.success(f"✅ Found {results['slide_count']} slides")
            
            if results['issues']:
                st.warning(f"⚠️ {len(results['issues'])} issues found:")
                for issue in results['issues']:
                    st.write(f"  • {issue}")
            else:
                st.success("✅ No issues found! Ready to generate.")
        else:
            st.error("❌ Validation failed:")
            st.write(results['error'])


# ============================================================================
# QUICK REFERENCE
# ============================================================================

def show_reference():
    """Show quick reference guide"""
    st.header("📖 Quick Reference Guide")
    
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
⚠️  CRITICAL TAG USAGE 
================================================================================

**INLINE TAGS MUST BE EXPLICITLY CLOSED**

The system now requires that all inline style tags wrap ONLY the exact word or 
phrase you want to style. Tags will NO LONGER capture multiple words automatically.

✅ CORRECT - Explicit closing tags:
Content: The student [answer]completed[/answer] the task.
Content: [question]Have you ever traveled abroad?[/question]
Content: He used the [vocabulary]Present Perfect[/vocabulary] tense.
Content: [emphasis]Never forget[/emphasis] to add the final -ed.

❌ INCORRECT - Will only style ONE word:
Content: [answer] completed the task  ← Only "completed" will be styled!
Content: [emphasis] Never forget      ← Only "Never" will be styled!

================================================================================
FORMAT OVERVIEW
================================================================================

1️⃣ Every slide must start with:
   Slide X
   Title: [your slide title]

2️⃣ Content must use one of the following layout types:
   - Single column → Content:
   - Two columns → Left: / Right:
   - Four boxes → LeftTop:, RightTop:, LeftBottom:, RightBottom:

3️⃣ Each slide ends (optionally) with a separator:
   ---

4️⃣ Every slide MUST have:
   - A Title line
   - At least one content section
   - Notes: (teacher instructions, timing, etc.)

5️⃣ Titles must be under 60 characters.

================================================================================
LAYOUT TYPES
================================================================================

✅ **SINGLE COLUMN**
For objectives, introductions, or explanations.

Slide 1
Title: Lesson Objectives
Content: [emphasis]Lesson 1[/emphasis] – Past Simple
Content: [step] Talk about past experiences
Content: [step] Describe completed actions
Notes: Review previous session briefly. 5 mins.

---

✅ **TWO COLUMNS**
For vocabulary, comparisons, or short Q&A.

Slide 2
Title: Vocabulary – Travel Verbs
Left: [vocabulary]book[/vocabulary]
Right: to arrange a ticket, hotel, or flight
Left: [vocabulary]pack[/vocabulary]
Right: to put things in a bag for travel
Notes: Drill pronunciation and example sentences.

---

✅ **FOUR BOXES**
For grammar, structured topics, or examples.

Slide 3
Title: Grammar – Past Simple
LeftTop: [emphasis]FORM[/emphasis]
LeftTop: Subject + Verb (-ed or irregular)
RightTop: [emphasis]USE[/emphasis]
RightTop: Finished actions in finished time
LeftBottom: [emphasis]EXAMPLES[/emphasis]
LeftBottom: • I [answer]went[/answer] to France in 2018.
RightBottom: [emphasis]TIME MARKERS[/emphasis]
RightBottom: • yesterday • last week • in 2010
Notes: Elicit examples. Clarify difference between regular/irregular verbs.

---

✅ **READING COMPREHENSION**
Use LeftTop for passage, LeftBottom for questions.

Slide 4
Title: Reading – Weekend Plans
LeftTop: Last weekend I visited my grandparents. We cooked together and watched a film.
LeftBottom: [question]What did the writer do last weekend?[/question]
LeftBottom: [question]Who did they visit?[/question]
Notes: Read aloud, check comprehension, highlight past tense verbs.

================================================================================
STYLE TAGS - EXPLICIT CLOSING REQUIRED
================================================================================

✅ Supported tags:
[vocabulary]...[/vocabulary]   → new terms
[question]...[/question]       → learner prompts  
[answer]...[/answer]           → model answers
[emphasis]...[/emphasis]       → important points
[step]                         → sequential reveal (no closing tag needed)

================================================================================
INLINE TAG RULES (UPDATED)
================================================================================

**Rule 1: Always use explicit closing tags for words/phrases you want styled**

✅ CORRECT Examples:
Content: The student [answer]completed[/answer] the task.
Content: [question]Have you ever traveled abroad?[/question]
Content: Use the [vocabulary]Present Perfect[/vocabulary] tense.
Content: [emphasis]Never[/emphasis] forget the -ed ending.
Left: [vocabulary]resilient[/vocabulary]
Right: able to recover quickly from difficulties

**Rule 2: Tags wrap the EXACT content to be styled**

✅ Style one word:
[answer]completed[/answer]

✅ Style multiple words:
[vocabulary]Present Perfect[/vocabulary]

✅ Style entire question:
[question]What is your favorite color?[/question]

**Rule 3: Do NOT use open-only tags expecting multi-word capture**

❌ WRONG:
Content: [emphasis] This will not style the whole phrase

✅ CORRECT:
Content: [emphasis]This will style the whole phrase[/emphasis]

**Rule 4: For [step] tags, no closing tag is needed**

✅ CORRECT:
Content: [step] First point
Content: [step] Second point
Content: [step] Third point

**Rule 5: Never double-wrap or repeat tags**

❌ WRONG:
[emphasis][emphasis]word[/emphasis][/emphasis]
[emphasis] word [emphasis]

✅ CORRECT:
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
RightTop: • I [answer]did not go[/answer] to work yesterday.
RightTop: • She [answer]didn't travel[/answer] last month.
LeftBottom: [emphasis]CONTRACTIONS[/emphasis]
LeftBottom: did not = didn't
RightBottom: [emphasis]COMMON ERRORS[/emphasis]
RightBottom: ❌ I didn't went
RightBottom: ✅ I didn't go
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
  • Timing estimate (e.g., "5 minutes")
  • Activity type (e.g., pair work, class discussion)
  • Teaching tips, e.g., "Drill pronunciation", "Monitor accuracy"
  • Optional: image or activity suggestions

Example:
Notes: Pair work 5 minutes. Encourage full sentences. Monitor for correct past tense.

================================================================================
COMMON MISTAKES TO AVOID
================================================================================
❌ Missing "Slide X" or "Title:"
❌ Mixing Left/Right with LeftTop/RightTop on the same slide
❌ Forgetting Notes:
❌ Including image filenames or PowerPoint animation settings
❌ Using markdown symbols (#, **, -, etc.)
❌ Writing too much text per box (keep it concise)
❌ Using open-only tags like [emphasis] without closing them
❌ Expecting [tag] word to style multiple words

================================================================================
OUTPUT STRUCTURE SUMMARY
================================================================================
Slide 1 – Title + Objectives  
Slide 2 – Lead-in Discussion  
Slide 3 – Reading + Questions  
Slide 4 – Vocabulary  
Slide 5 – Grammar Explanation  
Slide 6 – Controlled Practice  
Slide 7 – Speaking/Production  
Slide 8 – Recap + Homework  

================================================================================
TAG USAGE SUMMARY
================================================================================

✅ DO:
- Use explicit closing tags: [tag]content[/tag]
- Wrap exact words/phrases you want styled
- Use [step] without closing tag for animations
- Put Notes: on every slide

❌ DON'T:
- Use open-only tags expecting multi-word capture
- Forget closing tags
- Double-wrap tags
- Mix layout types on same slide

================================================================================
QUALITY CHECKLIST
================================================================================
Before outputting your lesson, verify:

✅ Every slide starts with "Slide X"
✅ Every slide has "Title:"
✅ All inline tags have proper closing tags (except [step])
✅ Every slide has "Notes:"
✅ Slide separator "---" between slides
✅ No markdown formatting (##, **, -, etc.)
✅ Appropriate layout chosen for content type
✅ Text length suitable for slide (not too long)
✅ Grammar and vocabulary appropriate for stated level
✅ Activities match stated duration

================================================================================
END OF INSTRUCTIONS
================================================================================
Start your output immediately with "Slide 1".
Do not include any introductions, explanations, or commentary.
Output ONLY the formatted lesson content.
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

1️⃣ Every slide begins with:
Slide X
Title: [your title]

2️⃣ Use ONE layout per slide:
   • Content: (single column)
   • Left: / Right: (two columns)
   • LeftTop:, RightTop:, LeftBottom:, RightBottom: (four boxes)

3️⃣ Separate slides with ---
4️⃣ Each slide MUST include:
   - A Title
   - At least one content section
   - Notes: (teacher guidance)

5️⃣ Do NOT include explanations, markdown, or image references.
6️⃣ Use • for bullet points, not - or *.
7️⃣ Keep titles under 60 characters.

================================================================================
STYLE TAGS
================================================================================

✅ Supported tags:
[vocabulary]...[/vocabulary]   → new terms
[question]...[/question]       → learner prompts
[answer]...[/answer]           → model answers
[emphasis]...[/emphasis]       → important points
[step]                         → sequential reveal

✅ Inline syntax is REQUIRED:
Each tag must open and close around the exact word or phrase, e.g.:

The student [answer]completed[/answer] the task.
[question]Have you ever traveled abroad?[/question]
He used the [vocabulary]Present Perfect[/vocabulary] tense.
[emphasis]Never forget[/emphasis] to add the final -ed.

❌ Do NOT leave tags unclosed like "[emphasis] word".
❌ Do NOT repeat tags twice around the same word.

✅ If unsure, always output them as closed tags [tag]word[/tag].


================================================================================
LAYOUT EXAMPLES
================================================================================

SINGLE COLUMN
-------------
Slide 1
Title: Objectives
Content: [emphasis]Lesson 1[/emphasis] — Past Simple
Content: [step] Describe completed actions
Content: [step] Talk about life experiences
Notes: Review previous session. 5 mins.

---

TWO COLUMNS
------------
Slide 2
Title: Vocabulary – Work Verbs
Left: [vocabulary]manage[/vocabulary]
Right: to be responsible for a team or project
Left: [vocabulary]attend[/vocabulary]
Right: to go to a meeting or event
Notes: Check pronunciation. Ask for examples.

---

FOUR BOXES
-----------
Slide 3
Title: Grammar – Past Simple
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
❌ Markdown (##, **, -, etc.)
❌ Image or animation instructions
❌ Mixing layout types
❌ Empty slides

================================================================================
END
================================================================================
Start your output immediately with "Slide 1".
"""


def show_help_section():
    """Show standardized help section - SHARED ACROSS BOTH VERSIONS"""
    import streamlit as st
    
    st.header("ℹ️ Help & Documentation")
    
    # AI Instructions Download
    st.markdown("### 🤖 Use AI to Create Lesson Content")
    
    st.info("💡 **Tip:** Let AI do the work! Download the instruction file, give it to any AI (ChatGPT, Claude, etc.) with your lesson requirements, and it will generate properly formatted content.")
    
    st.download_button(
        label="📥 Download AI Instruction File",
        data=get_ai_instructions(),
        file_name="AI_Instructions_PowerPoint_Generator.txt",
        mime="text/plain",
        help="Download this file to give to AI (ChatGPT, Claude, etc.)"
    )
    
    st.markdown("### 📝 Sample AI Prompts")
    
    with st.expander("🗣️ Conversation Practice Lesson"):
        st.code("""I need to create an English lesson using the PowerPoint Generator format.

[Attach or paste the AI_Instructions_PowerPoint_Generator.txt file]

Please create a lesson with these specifications:
- Topic: Conversation practice - Making small talk at networking events
- Level: B1 (Intermediate)
- Duration: 60 minutes
- Focus: Ice breakers, follow-up questions, showing interest
- Include: Vocabulary, example dialogues, practice activities
- 8-10 slides following the structure in the instructions

Generate the complete content file in the exact format specified.""", language="text")
    
    with st.expander("💼 Business English Lesson"):
        st.code("""I need to create an English lesson using the PowerPoint Generator format.

[Attach or paste the AI_Instructions_PowerPoint_Generator.txt file]

Please create a lesson with these specifications:
- Topic: Writing professional emails - Making requests
- Level: B2 (Upper Intermediate)
- Duration: 60 minutes
- Focus: Formal language, polite requests, appropriate tone
- Include: Email structure, key phrases, practice writing activity
- 8-10 slides following the structure in the instructions

Generate the complete content file in the exact format specified.""", language="text")
    
    with st.expander("🔬 Technical/Specialist Language"):
        st.code("""I need to create an English lesson using the PowerPoint Generator format.

[Attach or paste the AI_Instructions_PowerPoint_Generator.txt file]

Please create a lesson with these specifications:
- Topic: IT Architecture - Describing cloud infrastructure
- Level: B2-C1 (Business English for Technical Architects)
- Duration: 60 minutes
- Focus: Technical vocabulary, explaining systems, comparing solutions
- Include: Case study, technical terms, practice describing projects
- 8-10 slides following the structure in the instructions

Generate the complete content file in the exact format specified.""", language="text")
    
    with st.expander("📰 News Article Lesson"):
        st.code("""I need to create an English lesson using the PowerPoint Generator format.

[Attach or paste the AI_Instructions_PowerPoint_Generator.txt file]

Please create a lesson based on this news article:
[Paste the article text or URL]

Specifications:
- Level: B1 (Intermediate)
- Duration: 60 minutes
- Include: Simplified reading passage (200 words), comprehension questions, vocabulary, discussion
- 8-10 slides following the structure in the instructions

Generate the complete content file in the exact format specified.""", language="text")
    
    with st.expander("📚 Grammar Focus Lesson"):
        st.code("""I need to create an English lesson using the PowerPoint Generator format.

[Attach or paste the AI_Instructions_PowerPoint_Generator.txt file]

Please create a lesson with these specifications:
- Topic: Past Simple vs Present Perfect
- Level: B1 (Intermediate)
- Duration: 60 minutes
- Focus: Form, usage differences, time expressions, practice
- Include: Rule explanation, examples, controlled practice, freer practice
- 8-10 slides following the structure in the instructions

Generate the complete content file in the exact format specified.""", language="text")
    
    st.markdown("---")
    
    st.markdown("### 🎨 Adding Images & Animations")
    
    st.info("""
    **Best Practice:** Add images and animations AFTER generating your PowerPoint.
    
    This gives you more control and makes it easier to find the perfect visuals.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📷 Adding Images in PowerPoint")
        st.write("""
        1. **Open** your generated presentation
        2. **Go to** Insert > Pictures
        3. **Choose from:**
           - This Device (your files)
           - Stock Images (built-in)
           - Online Pictures (Bing search)
        4. **Resize & position** as needed
        
        **Recommended Stock Image Sites:**
        - 🔸 [Unsplash](https://unsplash.com) - High quality, free
        - 🔸 [Pexels](https://pexels.com) - Diverse photos & videos
        - 🔸 [Pixabay](https://pixabay.com) - Photos, vectors, illustrations
        - 🔸 PowerPoint's built-in stock images
        """)
    
    with col2:
        st.markdown("#### ✨ Adding Animations in PowerPoint")
        st.write("""
        1. **Select** the text or object
        2. **Go to** Animations tab
        3. **Choose** an animation effect
        4. **Set** timing and order
        
        **Popular Choices:**
        - 🔸 Fade/Appear - subtle reveals
        - 🔸 Fly In - dynamic entry
        - 🔸 Wipe - directional reveal
        - 🔸 Animation Pane - manage all animations
        
        **Note:** The `[step]` tag in your content creates basic text reveals automatically.
        """)
    
    st.markdown("---")
    
    st.markdown("### Getting Started")
    st.write("""
    **Option 1: Use AI to Generate Content** ⭐ Recommended
    1. **Download** the AI instruction file above
    2. **Give it to AI** (ChatGPT, Claude, Gemini, etc.) with your lesson specifications
    3. **Copy** the generated content
    4. **Paste** into the editor or upload as .txt file
    5. **Validate** and **Generate**
    6. **Add images & animations** in PowerPoint
    
    **Option 2: Write Content Manually**
    1. **Write or upload** your lesson content using the generator syntax
    2. **Validate** to check for errors
    3. **Generate** to create your PowerPoint presentation
    4. **Add images & animations** in PowerPoint
    5. **Download** and use in your lesson!
    """)
    
    st.markdown("### Common Questions")
    
    with st.expander("❓ How do I create a slide?"):
        st.write("""
        Every slide must start with:
        ```
        Slide 1
        Title: Your Title
        ```
        Then add content using Content:, Left:, Right:, etc.
        Separate slides with `---`
        """)
    
    with st.expander("❓ Should I include image references in my content?"):
        st.write("""
        **No!** It's much easier to add images directly in PowerPoint after generating.
        
        This way you can:
        - Browse and preview images easily
        - Resize and position them perfectly
        - Use PowerPoint's built-in stock images
        - Make changes without regenerating
        """)
    
    with st.expander("❓ How do animations work?"):
        st.write("""
        **Basic animations:** Use the `[step]` tag in your content for automatic text reveals.
        
        **Advanced animations:** Add these in PowerPoint after generating for full control.
        
        Example in content:
        ```
        Content: [step] First point
        Content: [step] Second point
        Content: [step] Third point
        ```
        """)
    
    with st.expander("❓ What if my text is too long?"):
        st.write("""
        The generator automatically reduces font size for long text:
        - 300+ characters → 18pt
        - 500+ characters → 16pt
        - 700+ characters → 14pt
        
        You'll see overflow warnings during validation.
        """)
    
    with st.expander("❓ Can I use this for any subject?"):
        st.write("""
        **Yes!** While designed for language teaching, the generator works for:
        - Any educational subject
        - Training presentations
        - Workshop materials
        - Corporate training
        - Academic lectures
        
        Just focus on clear text content and add subject-specific images in PowerPoint.
        """)
    
    st.markdown("### Example Lesson Structure")
    
    st.code("""
Slide 1 - Title & Objectives (with [step] animations)
Slide 2 - Lead-in Discussion (with [question] tags)
Slide 3 - Reading Passage + Questions (LeftTop/LeftBottom)
Slide 4 - Vocabulary (Two-column or four-box layout)
Slide 5 - Main Content/Explanation (Choose appropriate layout)
Slide 6 - Practice Exercise
Slide 7 - Speaking/Production Activity
Slide 8 - Recap & Homework

Then add relevant images and extra animations in PowerPoint!
    """, language="text")


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application"""
    
    # Header
    st.markdown('<h1 class="main-header">🎨 Universal PowerPoint Generator</h1>', unsafe_allow_html=True)
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
        st.header("🎨 Customization")
        
        with st.expander("📐 Slide Design", expanded=True):
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
                    st.success("✅ Background uploaded")
        
        with st.expander("🔤 Fonts & Colors", expanded=True):
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
        
        with st.expander("🎯 Style Tags", expanded=False):
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
        
        with st.expander("⚙️ Options", expanded=False):
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
            with st.expander("🤖 AI Content Generator", expanded=False):
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
                        st.info("🆓 Get free API key: [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)")
                    elif ai_provider == "OpenAI (GPT-4)":
                        st.info("🔑 Get API key: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)")
                    elif ai_provider == "Claude (Anthropic)":
                        st.info("🔑 Get API key: [console.anthropic.com](https://console.anthropic.com)")
                    
                    if api_key:
                        st.session_state.ai_provider = ai_provider
                        st.session_state.ai_key = api_key
                        st.success("✅ API key configured")
                    else:
                        st.session_state.ai_provider = None
                        st.session_state.ai_key = None
                else:
                    st.session_state.ai_provider = None
                    st.session_state.ai_key = None
        
        st.markdown("---")
        
        if st.button("🔄 Reset to Defaults"):
            st.session_state.custom_config = DEFAULT_CONFIG.copy()
            st.rerun()
        
        if st.button("📄 Load Sample"):
            st.session_state.content = get_sample_template()
            st.success("Sample loaded!")
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["✏️ Editor", "📖 Quick Reference", "❓ Help"])
    
    with tab1:
        show_editor()
    
    with tab2:
        show_reference()
    
    with tab3:
        show_help_section()


if __name__ == "__main__":
    main()








