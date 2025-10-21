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
    """Help & Documentation"""
    st.header("ℹ️ Help & Documentation")

    st.markdown("### 🤖 Use AI to Create Lesson or Training Content")
    st.info("💡 Download the AI instruction file and give it to ChatGPT, Claude, Gemini, etc.")
    st.download_button(
        "📥 Download AI Instruction File",
        get_ai_instructions(),
        file_name="AI_Instructions_Universal_Generator.txt",
        mime="text/plain"
    )

    st.markdown("### Example Lesson Structure")
    st.code("""
Slide 1 – Title & Objectives ([step] animations)
Slide 2 – Discussion ([question] tags)
Slide 3 – Reading & Questions (LeftTop / LeftBottom)
Slide 4 – Vocabulary (Template: vocabulary)
Slide 5 – Concept or Process (4-box layout)
Slide 6 – Practice Activity
Slide 7 – Speaking or Reflection
Slide 8 – Recap & Homework
""", language="text")

    st.markdown("---")
    st.markdown("### Common Questions")
    st.write("""
**How do I start a slide?**
Slide 1
Title: My Slide Title
Content: Main point
arduino
Copy code

**How do I add animations?**
Use `[step]` for sequential points:
Content: [step] First point
Content: [step] Second point

csharp
Copy code

**How do I add images?**
Image: chart.png | width=5 | align=center

python
Copy code
""")

def show_reference():
    """Quick Reference Guide"""
    st.header("📖 Quick Reference")

    st.markdown("### Layout Types")
    st.code("""
Content: Standard layout
Left: For two-column slides
Right: For two-column slides
LeftTop / RightTop / LeftBottom / RightBottom: For 4-box layouts
Notes: For presenter notes
""", language="text")

    st.markdown("### Style Tags")
    st.code("""
[vocabulary] - Highlights key terms
[question]   - Marks discussion prompts
[answer]     - Shows model responses
[emphasis]   - Emphasizes key ideas
[step]       - Adds animation steps
""", language="text")

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
