"""
Universal PowerPoint Generator - Web App
=========================================
Fully customizable presentation generator for educators
"""

import streamlit as st
import os
import io
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

# Page configuration
st.set_page_config(
    page_title="Universal PowerPoint Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Unified visual style for help/reference sections
st.markdown("""
    <style>
    h2, h3 {
        font-family: 'Montserrat', sans-serif;
        font-weight: 600;
    }
    .stCodeBlock {
        font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)

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
                    # Save uploaded file
                    bg_path = f"temp_background_{uploaded_bg.name}"
                    with open(bg_path, 'wb') as f:
                        f.write(uploaded_bg.read())
                    st.session_state.custom_config["background_image"] = bg_path
                    st.session_state.background_file = bg_path
                    st.success("✅ Background uploaded")
        
        with st.expander("🔤 Fonts & Colors", expanded=True):
            # Title font and color
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
            
            # Body font and color
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


def show_editor():
    """Show the main editor interface"""
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
    
    # Text editor
    st.markdown("### Edit Your Content")
    content = st.text_area(
        "Content Editor",
        value=st.session_state.content,
        height=400,
        help="Write your lesson content here",
        label_visibility="collapsed"
    )
    st.session_state.content = content
    
    # Action buttons
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


def get_ai_instructions():
    """Return complete AI instruction file content for Universal Generator"""
    return """================================================================================
AI INSTRUCTIONS: Universal PowerPoint Generator Content Format
================================================================================

PURPOSE:
You are creating lesson, training, or presentation content for the Universal PowerPoint Generator.
This file explains the exact text format required for the generator to build slides.

================================================================================
CRITICAL RULES
================================================================================
1. Each slide starts with "Slide X" (X = any number)
2. Each slide must have "Title: [text]"
3. Use "Content:", "Left:", "Right:", etc. for layout
4. Separate slides with "---"
5. Lines beginning with "#" are comments (ignored)

================================================================================
CONTENT SECTIONS
================================================================================
Content:        Single-column content
Left:           Left column in two-column layout
Right:          Right column in two-column layout
LeftTop:        Top-left box (4-box layout)
RightTop:       Top-right box
LeftBottom:     Bottom-left box
RightBottom:    Bottom-right box
Notes:          Speaker or teacher notes
Template:       Optional predefined layout (vocabulary, reading, comparison)
Image:          Insert image (Image: filename.jpg | width=5 | align=center)

================================================================================
STYLE TAGS
================================================================================
[vocabulary]    Highlight new or important terms
[question]      Discussion or comprehension questions
[answer]        Model answers or explanations
[emphasis]      Important points or takeaways
[step]          Sequential animation steps

================================================================================
EXAMPLES
================================================================================
Slide 1
Title: Introducing the Topic
Content: [emphasis] Lesson 1
Content: Welcome to today's session!
Content: [step] Objective 1
Content: [step] Objective 2
Notes: Brief intro and objectives overview.

---
Slide 2
Title: Discussion
Content: [question] What challenges have you faced?
Content: [answer] Managing time effectively.
Notes: 5-minute group discussion.

---

================================================================================
LENGTH GUIDELINES
================================================================================
Title:             ≤ 60 characters
Single Column:     ≤ 500 characters
Two Columns:       ≤ 300 characters each
Four Boxes:        ≤ 150 characters each
Reading Passage:   800–1000 characters
Questions:         3–5 max per slide

================================================================================
STRUCTURE TEMPLATE
================================================================================
Slide 1: Title + Objectives ([step] animations)
Slide 2: Lead-in / Discussion
Slide 3: Reading + Questions
Slide 4: Vocabulary (Template: vocabulary)
Slide 5: Explanation / Grammar / Concept
Slide 6: Practice Activity
Slide 7: Speaking / Production Task
Slide 8: Recap & Reflection

================================================================================
NOTES
================================================================================
Each slide should include Notes: for timing, instructions, and feedback tips.

================================================================================
COMMON MISTAKES TO AVOID
================================================================================
❌ Missing "Slide X"
❌ Missing "Title:"
❌ Wrong section names (use Left:, Right:, etc.)
❌ Too much text per box
❌ Forgetting Notes:
❌ Skipping [vocabulary]/[question]/[emphasis] tags

================================================================================
END OF INSTRUCTIONS
================================================================================
"""


def show_help():
    """Show Help & Documentation for Universal Generator"""
    st.header("ℹ️ Help & Documentation")

    # --- AI Integration Section ---
    st.markdown("### 🤖 Use AI to Create Lesson or Training Content")
    st.info("💡 **Tip:** Download the AI instruction file and give it to ChatGPT, Claude, Gemini, or any AI model to auto-generate properly formatted content.")

    st.download_button(
        label="📥 Download AI Instruction File",
        data=get_ai_instructions(),
        file_name="AI_Instructions_Universal_Generator.txt",
        mime="text/plain",
        help="Give this to any AI to generate formatted content automatically."
    )

    st.markdown("### 📝 Sample AI Prompts")

    with st.expander("🗣️ Conversation / Soft Skills Lesson"):
        st.code("""I need to create a lesson using the Universal PowerPoint Generator format.

[Attach or paste the AI_Instructions_Universal_Generator.txt file]

Please create a lesson with these specs:
- Topic: Making small talk in professional settings
- Level: Intermediate (B1)
- Duration: 60 minutes
- Include: Vocabulary, short reading, discussion questions, practice tasks
- 8–10 slides following the structure in the instructions.""", language="text")

    with st.expander("💼 Business or Technical Training"):
        st.code("""I need to create a business English training lesson using the Universal PowerPoint Generator format.

[Attach or paste the AI_Instructions_Universal_Generator.txt file]

Specs:
- Topic: Presenting a technical solution
- Audience: IT professionals
- Duration: 60 minutes
- Focus: Clear explanations, sequencing language, vocabulary
- 8–10 slides, following the format.""", language="text")

    with st.expander("📚 Academic or Skills-Based Lesson"):
        st.code("""Please create an academic skills lesson using the Universal PowerPoint Generator format.

[Attach or paste the AI_Instructions_Universal_Generator.txt file]

Specs:
- Topic: Writing clear topic sentences
- Level: Upper Intermediate
- Duration: 45 minutes
- Focus: Structure, examples, analysis
- 6–8 slides including objectives, examples, and exercises.""", language="text")

    st.markdown("---")

    # --- How-To Section ---
    st.markdown("### Getting Started")
    st.write("""
**Option 1: Use AI**
1. Download the AI instruction file above  
2. Give it to ChatGPT or another AI model with your topic and level  
3. Copy the AI-generated text into this app  
4. Validate and generate your PowerPoint  

**Option 2: Write Manually**
1. Use 'Slide X' and the section keywords (`Content:`, `Left:`, etc.)  
2. Validate to check for structure issues  
3. Generate and download your custom slides  
""")

    # --- Common Questions ---
    st.markdown("### Common Questions")

    with st.expander("❓ How do I start a new slide?"):
        st.write("""
Each slide starts with:
Slide 1
Title: Your title here

pgsql
Copy code
Add your content below and separate slides with `---`.
""")

    with st.expander("❓ How do I add animations?"):
        st.write("""
Use `[step]` before each animated line:
Content: [step] First point
Content: [step] Second point

python
Copy code
Each step becomes a separate shape for simple animations.
""")

    with st.expander("❓ What if my text is long?"):
        st.write("""
The generator auto-adjusts font size:
- 300+ characters → 18pt  
- 500+ → 16pt  
- 700+ → 14pt  
Overflow warnings appear during validation.
""")

    with st.expander("❓ Can I include images?"):
        st.write("""
Yes. Add them like this:
Image: chart.png | width=5 | align=center

rust
Copy code
Supported: JPG, PNG. Upload them to the same folder before generating.
""")

    st.markdown("### Example Lesson Structure")
    st.code("""
Slide 1 – Title & Objectives ([step] animations)
Slide 2 – Discussion ([question] tags)
Slide 3 – Reading & Questions (LeftTop / LeftBottom)
Slide 4 – Vocabulary (Template: vocabulary)
Slide 5 – Concept Explanation (4-box layout)
Slide 6 – Practice Activity
Slide 7 – Speaking or Reflection
Slide 8 – Recap & Homework
""", language="text")


def show_reference():
    """Show quick reference guide for the Universal Generator"""
    st.header("📖 Quick Reference Guide")

    st.markdown("### Basic Syntax")
    st.code("""
Slide 1
Title: Your Slide Title
Content: Your content here
Content: [step] Animated point
Notes: Speaker or teacher notes
---
    """, language="text")

    st.markdown("### Layout Types")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Single Column:**")
        st.code("""
Content: Main point
Content: Another point
        """, language="text")

        st.markdown("**Two Columns:**")
        st.code("""
Left: Left content
Right: Right content
        """, language="text")

    with col2:
        st.markdown("**Four Boxes (Grid Layout):**")
        st.code("""
LeftTop: Concept 1
RightTop: Concept 2
LeftBottom: Concept 3
RightBottom: Concept 4
        """, language="text")

        st.markdown("**Reading or Case Study Layout:**")
        st.code("""
LeftTop: Reading passage text...
LeftBottom: 1. Question one?
LeftBottom: 2. Question two?
        """, language="text")

    st.markdown("---")

    st.markdown("### Style Tags")

    tags = {
        "[vocabulary]": "Highlights new or important terms",
        "[question]": "Marks discussion or comprehension questions",
        "[answer]": "Shows model answers or examples",
        "[emphasis]": "Draws attention to key ideas or important phrases",
        "[step]": "Creates animation steps (reveals content sequentially)"
    }

    for tag, desc in tags.items():
        st.markdown(f"**{tag}** — {desc}")

    st.markdown("---")

    st.markdown("### Example Layouts")

    st.markdown("**Single Column Example:**")
    st.code("""
Slide 1
Title: Course Introduction
Content: [emphasis] Welcome to the session
Content: [step] Today we will cover objectives and key outcomes.
Notes: Start with introductions and expectations.
---
    """, language="text")

    st.markdown("**Two-Column Example (Vocabulary / Comparison):**")
    st.code("""
Slide 2
Title: Key Terms
Left: [vocabulary] efficiency
Right: Ability to achieve results with minimal waste
Left: [vocabulary] reliability
Right: Consistent performance under different conditions
Notes: Ask participants to provide examples.
---
    """, language="text")

    st.markdown("**Reading Example:**")
    st.code("""
Slide 3
Title: Case Study – Sustainable Solutions
LeftTop: The company implemented a new system reducing energy use by 40%...
LeftBottom: 1. What problem did the company face?
LeftBottom: 2. What solution did they choose?
LeftBottom: 3. What were the results?
Notes: Allow 5 minutes for reading and pair discussion.
---
    """, language="text")

    st.markdown("---")

    st.markdown("### Special Features")
    st.code("""
# Comments (ignored by generator)
Image: chart.png | width=5 | align=center
Template: vocabulary
Math: x^2, H_2O, >=, pi
    """, language="text")

    st.markdown("### Best Practices")
    st.write("""
- ✅ Keep slide titles short (under ~60 characters)  
- ✅ Use `[step]` for 3–5 sequential points per slide  
- ✅ Include **Notes:** for timing, instructions, or questions  
- ✅ Split long content into multiple slides  
- ✅ Validate before generating  
- ❌ Don’t mix layouts on one slide (e.g., LeftTop with Right only)
""")

    st.markdown("---")

    st.markdown("### Example Lesson Flow")
    st.code("""
Slide 1 – Title & Objectives ([step] animations)
Slide 2 – Lead-in Discussion ([question] tags)
Slide 3 – Reading or Case Study (LeftTop / LeftBottom)
Slide 4 – Vocabulary (Template: vocabulary)
Slide 5 – Grammar, Process, or Explanation (4-box layout)
Slide 6 – Practice Task ([emphasis] + [step])
Slide 7 – Speaking or Reflection
Slide 8 – Recap & Homework
    """, language="text")

