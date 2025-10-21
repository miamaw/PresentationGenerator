"""
Universal PowerPoint Generator - Web App
=========================================
Fully customizable presentation generator for educators
With integrated live preview and comprehensive help
"""

import streamlit as st
import os
import io
import re
from pathlib import Path

# Import the universal generator
try:
    from generate_presentation_universal import (
        merge_config, parse_content_file, build_presentation,
        validate_slide, DEFAULT_CONFIG
    )
    GENERATOR_AVAILABLE = True
except ImportError:
    GENERATOR_AVAILABLE = False
    st.error("⚠️ Generator module not found.")
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


def format_text_with_tags(text):
    """Format text with style tags for preview"""
    # Remove [step] tags for preview
    text = re.sub(r'\[step\]\s*', '', text)
    
    # Apply styling
    if '[vocabulary]' in text:
        text = text.replace('[vocabulary]', '')
        return f'<span style="color: #2E7D32; font-weight: bold;">🔹 {text}</span>'
    elif '[question]' in text:
        text = text.replace('[question]', '')
        return f'<span style="color: #7B1FA2; font-weight: 500;">❓ {text}</span>'
    elif '[answer]' in text:
        text = text.replace('[answer]', '')
        return f'<span style="color: #757575; font-style: italic;">💡 {text}</span>'
    elif '[emphasis]' in text:
        text = text.replace('[emphasis]', '')
        return f'<span style="color: #C62828; font-weight: bold;">⭐ {text}</span>'
    
    return text


def show_slide_preview(slide, slide_num):
    """Display a single slide preview"""
    
    # Determine layout
    has_content = len(slide['content']) > 0
    has_two_col = len(slide['left']) > 0 or len(slide['right']) > 0
    has_four_box = any([
        len(slide['lefttop']) > 0,
        len(slide['righttop']) > 0,
        len(slide['leftbottom']) > 0,
        len(slide['rightbottom']) > 0
    ])
    
    # Preview container with slide-like appearance
    st.markdown(f"""
        <div style="
            border: 2px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 300px;
        ">
            <div style="
                background: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                <h3 style="color: #1976D2; margin-bottom: 20px; border-bottom: 2px solid #1976D2; padding-bottom: 10px;">
                    {slide['title'] if slide['title'] else 'Untitled Slide'}
                </h3>
    """, unsafe_allow_html=True)
    
    # Single column content
    if has_content:
        st.markdown('<div style="margin: 15px 0;">', unsafe_allow_html=True)
        for item in slide['content']:
            if item:
                formatted = format_text_with_tags(item)
                st.markdown(f'<p style="margin: 8px 0; line-height: 1.6;">{formatted}</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Two column layout
    elif has_two_col:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div style="padding-right: 10px;">', unsafe_allow_html=True)
            for item in slide['left']:
                if item:
                    formatted = format_text_with_tags(item)
                    st.markdown(f'<p style="margin: 8px 0;">{formatted}</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div style="padding-left: 10px; border-left: 2px solid #eee;">', unsafe_allow_html=True)
            for item in slide['right']:
                if item:
                    formatted = format_text_with_tags(item)
                    st.markdown(f'<p style="margin: 8px 0;">{formatted}</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Four box layout
    elif has_four_box:
        col1, col2 = st.columns(2)
        
        with col1:
            if slide['lefttop']:
                st.markdown('<div style="border: 1px solid #ddd; padding: 10px; margin: 5px; border-radius: 5px; background: #f9f9f9;">', unsafe_allow_html=True)
                for item in slide['lefttop']:
                    if item:
                        formatted = format_text_with_tags(item)
                        st.markdown(f'<p style="margin: 5px 0; font-size: 0.9em;">{formatted}</p>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            if slide['leftbottom']:
                st.markdown('<div style="border: 1px solid #ddd; padding: 10px; margin: 5px; border-radius: 5px; background: #f9f9f9;">', unsafe_allow_html=True)
                for item in slide['leftbottom']:
                    if item:
                        formatted = format_text_with_tags(item)
                        st.markdown(f'<p style="margin: 5px 0; font-size: 0.9em;">{formatted}</p>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            if slide['righttop']:
                st.markdown('<div style="border: 1px solid #ddd; padding: 10px; margin: 5px; border-radius: 5px; background: #f9f9f9;">', unsafe_allow_html=True)
                for item in slide['righttop']:
                    if item:
                        formatted = format_text_with_tags(item)
                        st.markdown(f'<p style="margin: 5px 0; font-size: 0.9em;">{formatted}</p>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            if slide['rightbottom']:
                st.markdown('<div style="border: 1px solid #ddd; padding: 10px; margin: 5px; border-radius: 5px; background: #f9f9f9;">', unsafe_allow_html=True)
                for item in slide['rightbottom']:
                    if item:
                        formatted = format_text_with_tags(item)
                        st.markdown(f'<p style="margin: 5px 0; font-size: 0.9em;">{formatted}</p>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Show notes if present
    if slide['notes']:
        st.markdown('''
            <div style="
                margin-top: 15px; 
                padding: 10px; 
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
    
    # Close containers
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Slide number badge
    st.markdown(f'''
        <div style="text-align: right; margin-top: 5px;">
            <span style="
                background: #1976D2;
                color: white;
                padding: 3px 10px;
                border-radius: 12px;
                font-size: 0.85em;
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
# EDITOR WITH PREVIEW
# ============================================================================

def show_editor():
    """Enhanced editor with live preview panel"""
    st.header("Content Editor")
    
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
                    show_slide_preview(slides[selected], selected + 1)
                    
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


# ============================================================================
# HELP SECTION
# ============================================================================

def get_ai_instructions():
    """Return complete AI instruction file content"""
    return """================================================================================
AI INSTRUCTIONS: PowerPoint Generator Content Format
================================================================================

PURPOSE: You are creating lesson content for the PowerPoint Generator.
This file explains the EXACT format required for the content to work properly.

CRITICAL FORMATTING RULES:
1. EVERY slide must start with "Slide X" (where X is any number)
2. EVERY slide must have "Title: [text]"
3. Content is organized in sections: Content:, Left:, Right:, etc.
4. Use "---" to separate slides (optional but recommended)
5. Lines starting with "#" are comments (ignored)

CONTENT SECTIONS:
Content:        Single column content
Left:           Left column in two-column layout
Right:          Right column in two-column layout
LeftTop:        Top-left box in four-box layout
RightTop:       Top-right box in four-box layout
LeftBottom:     Bottom-left box in four-box layout
RightBottom:    Bottom-right box in four-box layout
Notes:          Teacher notes (not visible on slides)

STYLE TAGS:
[vocabulary]    Bold text - for NEW vocabulary terms
[question]      Styled text - for discussion questions
[answer]        Italic text - for model answers
[emphasis]      Bold text - for key takeaways
[step]          Creates animations - for sequential reveals

CONTENT LENGTH GUIDELINES:
- Slide Titles: Max 60 characters
- Single Column: Up to 500 characters per slide
- Two Columns: Up to 300 characters per column
- Four Boxes: Up to 150 characters per box
- Reading Passages: 800-1000 characters

EXAMPLE SLIDE:
Slide 1
Title: Professional Email Writing
Content: [emphasis] Lesson 1
Content: Business Communication Skills
Content: 
Content: Today's Focus:
Content: [step] Email structure and conventions
Content: [step] Professional language and tone
Notes: Warm-up about email challenges. 5 minutes.
---

IMPORTANT: Generate clean text-based slides. Add images later in PowerPoint.
"""


def show_help():
    """Show help and documentation"""
    st.header("ℹ️ Help & Documentation")
    
    # AI Instructions Download
    st.markdown("### 🤖 Use AI to Create Lesson Content")
    
    st.info("💡 **Tip:** Let AI do the work! Download the instruction file, give it to any AI (ChatGPT, Claude, etc.) with your lesson requirements, and it will generate properly formatted content.")
    
    st.download_button(
        label="📥 Download AI Instruction File",
        data=get_ai_instructions(),
        file_name="AI_Instructions_PowerPoint_Generator.txt",
        mime="text/plain",
        help="Download this file to give to AI"
    )
    
    st.markdown("### 📝 Sample AI Prompts")
    
    with st.expander("🗣️ Conversation Practice Lesson"):
        st.code("""I need to create an English lesson using the PowerPoint Generator format.

[Attach the AI instruction file]

Please create a lesson with these specifications:
- Topic: Conversation practice - Making small talk at networking events
- Level: B1 (Intermediate)
- Duration: 60 minutes
- Focus: Ice breakers, follow-up questions, showing interest
- Include: Vocabulary, example dialogues, practice activities
- 8-10 slides following the structure

Generate the complete content file in the exact format specified.""", language="text")
    
    with st.expander("💼 Business English Lesson"):
        st.code("""I need to create an English lesson.

[Attach the AI instruction file]

Specifications:
- Topic: Writing professional emails - Making requests
- Level: B2 (Upper Intermediate)
- Duration: 60 minutes
- 8-10 slides

Generate in the exact format specified.""", language="text")
    
    st.markdown("---")
    st.markdown("### 🎨 Adding Images & Animations")
    
    st.info("**Best Practice:** Add images and animations AFTER generating your presentation for more control.")
    
    img_tab1, img_tab2 = st.tabs(["📊 Google Slides", "📊 PowerPoint"])
    
    with img_tab1:
        st.markdown("#### Adding Images in Google Slides")
        st.write("""
        1. **Insert** > **Image** > **Search the web** or **Upload from computer**
        2. Resize and position as needed
        
        **Free Stock Images:**
        - [Unsplash](https://unsplash.com)
        - [Pexels](https://pexels.com)
        - [Pixabay](https://pixabay.com)
        """)
        
        st.markdown("#### Adding Animations")
        st.write("""
        1. Select text box or object
        2. **Insert** > **Animation**
        3. Choose: Fade in, Fly in, Zoom
        4. Set timing (On click, After previous)
        """)
    
    with img_tab2:
        st.markdown("#### Adding Images in PowerPoint")
        st.write("""
        1. **Insert** > **Pictures** > Choose source
        2. Resize and position
        
        **Free Stock Images:**
        - [Unsplash](https://unsplash.com)
        - [Pexels](https://pexels.com)
        - PowerPoint's built-in stock images
        """)
        
        st.markdown("#### Adding Animations")
        st.write("""
        1. Select text or object
        2. **Animations** tab
        3. Choose effect
        4. Set timing and order
        """)
    
    st.markdown("---")
    st.markdown("### Getting Started")
    st.write("""
    **Option 1: Use AI** ⭐ Recommended
    1. Download AI instruction file
    2. Give to ChatGPT/Claude with specifications
    3. Copy generated content
    4. Paste into editor
    5. Generate PowerPoint
    6. Add images in PowerPoint
    
    **Option 2: Write Manually**
    1. Write content using the syntax
    2. Validate to check for errors
    3. Generate PowerPoint
    4. Add images in PowerPoint
    """)
    
    st.markdown("### Common Questions")
    
    with st.expander("❓ How do I create a slide?"):
        st.code("Slide 1\nTitle: Your Title\nContent: Your content", language="text")
    
    with st.expander("❓ How do animations work?"):
        st.write("Use `[step]` for basic reveals, add advanced animations in PowerPoint after.")
    
    with st.expander("❓ What if text is too long?"):
        st.write("Generator auto-reduces font size. You'll see overflow warnings during validation.")


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
        show_help()


if __name__ == "__main__":
    main()
