"""
Universal PowerPoint Generator - Web App
=========================================
Fully customizable presentation generator for educators, trainers, and professionals.
"""

import streamlit as st
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Import the universal generator
# ---------------------------------------------------------------------------
try:
    from generate_presentation_universal import (
        merge_config, parse_content_file, build_presentation,
        validate_slide, DEFAULT_CONFIG
    )
    GENERATOR_AVAILABLE = True
except ImportError:
    GENERATOR_AVAILABLE = False
    st.error("⚠️ Generator module not found. Make sure generate_presentation_universal.py is present.")

# ---------------------------------------------------------------------------
# Streamlit page config and basic styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Universal PowerPoint Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Unified visual style
st.markdown("""
    <style>
    h2, h3 {
        font-family: 'Montserrat', sans-serif;
        font-weight: 600;
    }
    .stCodeBlock {
        font-size: 0.9rem;
    }
    .main-header {
        font-weight: bold;
    }
    .stButton>button {
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------
def rgb_to_hex(rgb):
    """Convert RGB list to hex color"""
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

def hex_to_rgb(hex_color):
    """Convert hex color to RGB list"""
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]

# ---------------------------------------------------------------------------
# Sample data and references
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------------------------
def main():
    """Main Streamlit app"""
    st.markdown('<h1 class="main-header">🎨 Universal PowerPoint Generator</h1>', unsafe_allow_html=True)
    st.markdown("**Create customized educational or professional presentations easily**")

    # Session state setup
    if "content" not in st.session_state:
        st.session_state.content = ""
    if "validation_results" not in st.session_state:
        st.session_state.validation_results = None
    if "custom_config" not in st.session_state:
        st.session_state.custom_config = DEFAULT_CONFIG.copy()

    # Sidebar UI ------------------------------------------------------------
    with st.sidebar:
        st.header("🎨 Customization")

        with st.expander("📐 Slide Design", expanded=True):
            bg_option = st.radio("Background Type:", ["Solid Color", "Upload Image"])
            if bg_option == "Solid Color":
                bg_color = st.color_picker(
                    "Background Color",
                    value=rgb_to_hex(st.session_state.custom_config["background_color"])
                )
                st.session_state.custom_config["background_color"] = hex_to_rgb(bg_color)
                st.session_state.custom_config["background_image"] = None
            else:
                uploaded_bg = st.file_uploader("Upload Background Image", type=["jpg", "jpeg", "png"])
                if uploaded_bg:
                    bg_path = f"temp_bg_{uploaded_bg.name}"
                    with open(bg_path, "wb") as f:
                        f.write(uploaded_bg.read())
                    st.session_state.custom_config["background_image"] = bg_path
                    st.success("✅ Background uploaded successfully")

        with st.expander("🔤 Fonts & Colors", expanded=True):
            st.subheader("Title Font & Color")
            title_font = st.selectbox("Title Font:", [
                "Arial", "Calibri", "Times New Roman", "Georgia", "Verdana",
                "Tahoma", "Trebuchet MS", "Comic Sans MS", "Impact", "Montserrat"
            ])
            st.session_state.custom_config["title_font_name"] = title_font

            title_color = st.color_picker(
                "Title Color",
                value=rgb_to_hex(st.session_state.custom_config["title_color"])
            )
            st.session_state.custom_config["title_color"] = hex_to_rgb(title_color)

            st.subheader("Body Font & Color")
            body_font = st.selectbox("Body Font:", [
                "Arial", "Calibri", "Times New Roman", "Georgia", "Verdana",
                "Tahoma", "Trebuchet MS", "Comic Sans MS", "Montserrat"
            ])
            st.session_state.custom_config["font_name"] = body_font

            text_color = st.color_picker(
                "Text Color",
                value=rgb_to_hex(st.session_state.custom_config["text_color"])
            )
            st.session_state.custom_config["text_color"] = hex_to_rgb(text_color)

        with st.expander("🎯 Style Tags"):
            st.info("Customize colors for [vocabulary], [question], [answer], [emphasis] tags")
            for tag in ["vocabulary", "question", "answer", "emphasis"]:
                color = st.color_picker(
                    f"[{tag}] Color",
                    value=rgb_to_hex(st.session_state.custom_config["styles"][tag]["color"])
                )
                st.session_state.custom_config["styles"][tag]["color"] = hex_to_rgb(color)

        with st.expander("⚙️ Options"):
            st.session_state.custom_config["enable_slide_numbers"] = st.checkbox(
                "Show slide numbers", value=True
            )
            st.session_state.custom_config["enable_overflow_warnings"] = st.checkbox(
                "Show overflow warnings", value=True
            )

        st.markdown("---")
        if st.button("🔄 Reset to Defaults"):
            st.session_state.custom_config = DEFAULT_CONFIG.copy()
            st.experimental_rerun()
        if st.button("📄 Load Sample Template"):
            st.session_state.content = get_sample_template()
            st.success("Sample content loaded!")

    # Tabs -----------------------------------------------------------------
    tab1, tab2, tab3 = st.tabs(["✏️ Editor", "📖 Quick Reference", "❓ Help"])
    with tab1:
        show_editor()
    with tab2:
        show_reference()
    with tab3:
        show_help()

# ---------------------------------------------------------------------------
# Editor + Generator
# ---------------------------------------------------------------------------
def show_editor():
    st.header("✏️ Content Editor")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        uploaded = st.file_uploader("📂 Upload .txt file", type=["txt"])
        if uploaded:
            st.session_state.content = uploaded.read().decode("utf-8")
            st.success(f"Loaded: {uploaded.name}")

    with col2:
        if st.session_state.content:
            st.download_button(
                "💾 Download .txt",
                data=st.session_state.content,
                file_name="lesson_content.txt",
                mime="text/plain"
            )

    st.text_area(
        "Content Editor",
        value=st.session_state.content,
        height=400,
        label_visibility="collapsed",
        key="content_area"
    )
    st.session_state.content = st.session_state.content_area

    col1, col2, col3 = st.columns(3)
    validate_btn = col1.button("✅ Validate Content")
    generate_btn = col2.button(
        "🎨 Generate PowerPoint", type="primary", disabled=not GENERATOR_AVAILABLE
    )
    clear_btn = col3.button("🗑️ Clear All")

    if validate_btn:
        validate_content()
    if generate_btn:
        generate_presentation()
    if clear_btn:
        st.session_state.content = ""
        st.session_state.validation_results = None
        st.experimental_rerun()

    if st.session_state.validation_results:
        results = st.session_state.validation_results
        st.markdown("---")
        st.subheader("🔍 Validation Results")
        if results["success"]:
            st.success(f"✅ Found {results['slide_count']} slides")
            if results["issues"]:
                st.warning(f"⚠️ {len(results['issues'])} issue(s) found:")
                for issue in results["issues"]:
                    st.write(f"• {issue}")
            else:
                st.success("✅ No issues found! Ready to generate.")
        else:
            st.error(f"❌ Validation failed: {results['error']}")

def validate_content():
    """Validate content file"""
    if not st.session_state.content.strip():
        st.warning("Please enter or upload content first.")
        return
    if not GENERATOR_AVAILABLE:
        st.error("Generator module not available.")
        return
    try:
        tmp = "temp_validation.txt"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(st.session_state.content)
        slides = parse_content_file(tmp)
        issues = []
        for i, slide in enumerate(slides, 1):
            issues.extend(validate_slide(slide, i, st.session_state.custom_config))
        st.session_state.validation_results = {
            "success": True,
            "slide_count": len(slides),
            "issues": issues
        }
        os.remove(tmp)
    except Exception as e:
        st.session_state.validation_results = {"success": False, "error": str(e)}

def generate_presentation():
    """Generate PPTX"""
    if not st.session_state.content.strip():
        st.warning("Please enter or upload content first.")
        return
    if not GENERATOR_AVAILABLE:
        st.error("Generator module not available.")
        return
    try:
        with st.spinner("🎨 Generating presentation..."):
            inp, outp = "temp_in.txt", "temp_out.pptx"
            with open(inp, "w", encoding="utf-8") as f:
                f.write(st.session_state.content)
            slides = parse_content_file(inp)
            build_presentation(slides, outp, st.session_state.custom_config)
            with open(outp, "rb") as f:
                pptx = f.read()
            st.success("✅ Presentation generated successfully!")
            st.download_button(
                "📥 Download PowerPoint",
                pptx,
                file_name="presentation.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
            os.remove(inp)
            os.remove(outp)
    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.exception(e)

# ---------------------------------------------------------------------------
# HELP & REFERENCE SECTIONS
# ---------------------------------------------------------------------------
def get_ai_instructions():
    """Return AI instructions"""
    return """================================================================================
AI INSTRUCTIONS: Universal PowerPoint Generator Format
================================================================================
(See repository README for complete formatting guide.)
================================================================================
"""

def show_help():
    """Show Help & Documentation for the Universal PowerPoint Generator"""
    st.header("ℹ️ Help & Documentation")

    # --- AI Integration Section ---
    st.markdown("### 🤖 Use AI to Create Lesson or Training Content")
    st.info(
        "💡 **Tip:** Let AI do the work! Download the instruction file, give it to any AI "
        "(ChatGPT, Claude, Gemini, etc.) with your lesson requirements, "
        "and it will generate properly formatted content."
    )

    st.download_button(
        label="📥 Download AI Instruction File",
        data=get_ai_instructions(),
        file_name="AI_Instructions_Universal_Generator.txt",
        mime="text/plain",
        help="Download this file to give to AI (ChatGPT, Claude, etc.)"
    )

    # --- Sample AI Prompts ---
    st.markdown("### 📝 Sample AI Prompts")

    with st.expander("🗣️ Conversation Practice Lesson"):
        st.code("""I need to create a lesson using the Universal PowerPoint Generator format.

[Attach or paste the AI_Instructions_Universal_Generator.txt file]

Please create a lesson with these specifications:
- Topic: Conversation practice - Making small talk at networking events
- Level: B1 (Intermediate)
- Duration: 60 minutes
- Focus: Ice breakers, follow-up questions, showing interest
- Include: Vocabulary, example dialogues, practice activities
- 8–10 slides following the structure in the instructions

Generate the complete content file in the exact format specified.""", language="text")

    with st.expander("💼 Business English Lesson"):
        st.code("""I need to create a lesson using the Universal PowerPoint Generator format.

[Attach or paste the AI_Instructions_Universal_Generator.txt file]

Please create a lesson with these specifications:
- Topic: Writing professional emails - Making requests
- Level: B2 (Upper Intermediate)
- Duration: 60 minutes
- Focus: Formal language, polite requests, appropriate tone
- Include: Email structure, key phrases, and a writing practice activity
- 8–10 slides following the structure in the instructions

Generate the complete content file in the exact format specified.""", language="text")

    with st.expander("🔬 Technical / Specialist Language"):
        st.code("""I need to create a lesson using the Universal PowerPoint Generator format.

[Attach or paste the AI_Instructions_Universal_Generator.txt file]

Please create a lesson with these specifications:
- Topic: IT Architecture - Describing cloud infrastructure
- Level: B2–C1 (Business English for Technical Professionals)
- Duration: 60 minutes
- Focus: Technical vocabulary, explaining systems, comparing solutions
- Include: Case study, technical terms, practice describing projects
- 8–10 slides following the structure in the instructions

Generate the complete content file in the exact format specified.""", language="text")

    with st.expander("📰 News Article Lesson"):
        st.code("""I need to create a lesson using the Universal PowerPoint Generator format.

[Attach or paste the AI_Instructions_Universal_Generator.txt file]

Please create a lesson based on this news article:
[Paste the article text or URL]

Specifications:
- Level: B1 (Intermediate)
- Duration: 60 minutes
- Include: Simplified reading passage (200 words), comprehension questions, vocabulary, discussion
- 8–10 slides following the structure in the instructions

Generate the complete content file in the exact format specified.""", language="text")

    with st.expander("📚 Grammar Focus Lesson"):
        st.code("""I need to create a lesson using the Universal PowerPoint Generator format.

[Attach or paste the AI_Instructions_Universal_Generator.txt file]

Please create a lesson with these specifications:
- Topic: Past Simple vs Present Perfect
- Level: B1 (Intermediate)
- Duration: 60 minutes
- Focus: Form, usage differences, time expressions, practice
- Include: Rule explanation, examples, controlled practice, freer practice
- 8–10 slides following the structure in the instructions

Generate the complete content file in the exact format specified.""", language="text")

    st.markdown("---")

    # --- Getting Started ---
    st.markdown("### Getting Started")

    st.write("""
**Option 1: Use AI to Generate Content**
1. **Download** the AI instruction file above  
2. **Give it to AI** (ChatGPT, Claude, Gemini, etc.) with your lesson specifications  
3. **Copy** the generated content  
4. **Paste** into the editor or upload as `.txt` file  
5. **Validate** and **Generate**

**Option 2: Write Content Manually**
1. **Write or upload** your lesson content using the Universal generator syntax  
2. **Validate** to check for errors  
3. **Generate** to create your PowerPoint presentation  
4. **Download** and use it in your session!
""")

    # --- Common Questions ---
    st.markdown("### Common Questions")

    with st.expander("❓ How do I create a slide?"):
        st.write("""
Every slide must start with:
Slide 1
Title: Your Title

csharp
Copy code
Then add content using:
Content: ...
Left: ...
Right: ...
Notes: ...

python
Copy code
Separate slides with `---`
""")

    with st.expander("❓ What if my text is too long?"):
        st.write("""
The generator automatically reduces font size for long text:

- 300+ characters → 18pt  
- 500+ characters → 16pt  
- 700+ characters → 14pt  

You'll see overflow warnings during validation.
""")

    with st.expander("❓ How do I add animations?"):
        st.write("""
Use `[step]` before each line you want to animate:
Content: [step] First point
Content: [step] Second point
Content: [step] Third point

python
Copy code
Each `[step]` creates a separate element for easy animation.
""")

    with st.expander("❓ Can I use images?"):
        st.write("""
Yes! Upload images to the same folder and reference them like this:
Image: diagram.png | width=5 | align=center

pgsql
Copy code
Supported parameters: `width`, `left`, `top`, `align`.
You can also add or replace images later in PowerPoint or Google Slides (including stock images).
""")

    with st.expander("❓ Where is my background template?"):
        st.write("""
If you are using a custom background image, ensure that it is uploaded in the same directory as this app. 
Alternatively, you can select a solid color or upload your own background in the sidebar.
""")

    st.markdown("### Example Lesson Structure")
    st.code("""
Slide 1 - Title & Objectives (with [step] animations)
Slide 2 - Lead-in Discussion (with [question] tags)
Slide 3 - Reading Passage + Questions (LeftTop / LeftBottom)
Slide 4 - Vocabulary (Template: vocabulary)
Slide 5 - Grammar or Concept Explanation (4-box layout)
Slide 6 - Practice Activity
Slide 7 - Speaking or Reflection
Slide 8 - Recap & Homework
""", language="text")

    st.markdown("---")
    st.markdown("💡 **Note:** You can further refine your presentation after export — add animations, transitions, and stock images directly inside PowerPoint or Google Slides.")
