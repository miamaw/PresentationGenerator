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
    """Return complete AI instruction file content"""
    return """================================================================================
AI INSTRUCTIONS: Educational PowerPoint Generator Content Format
================================================================================

PURPOSE: You are creating lesson content for the Educational PowerPoint Generator.
This file explains the EXACT format required for the content to work properly.

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
Template:       Apply predefined template (vocabulary, reading, comparison)
Image:          Insert image (format: Image: filename.jpg | width=5 | align=center)

================================================================================
LAYOUT SELECTION LOGIC
================================================================================

USE Content: FOR:
- Simple slides with one main message
- Title slides with objectives
- Instructions
- Single-topic explanations

USE Left: and Right: FOR:
- Vocabulary (word | definition)
- Comparisons (before | after)
- Advantages vs Disadvantages
- Theory vs Practice

USE LeftTop:, RightTop:, LeftBottom:, RightBottom: FOR:
- Four related concepts (4 project phases, 4 skills)
- Grammar explanations with examples and practice
- Pros/cons with solutions/alternatives

USE LeftTop: (passage) and LeftBottom: (questions) FOR:
- Reading comprehension
- Case studies with questions
- Longer texts with follow-up questions

================================================================================
STYLE TAGS - USE THESE FOR FORMATTING
================================================================================

[vocabulary]    Green, bold, 24pt - Use for NEW vocabulary terms
[question]      Purple, 20pt - Use for discussion questions
[answer]        Gray, italic, 18pt - Use for model answers
[emphasis]      Red, bold, 22pt - Use for key takeaways
[step]          Creates animations - Use for sequential reveals

EXAMPLES:
Content: [vocabulary] resilience - the ability to recover from failures
Content: [question] What challenges do you face in your role?
Content: [answer] Common challenges include time management and priorities
Content: [emphasis] Remember: Always validate before submitting!
Content: [step] First, identify the problem
Content: [step] Then, analyze possible solutions
Content: [step] Finally, implement and monitor

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

IMPORTANT: Long text automatically reduces font size, but there are limits!

================================================================================
LESSON STRUCTURE TEMPLATE
================================================================================

A well-structured lesson should follow this pattern:

Slide 1: Title + Objectives
- Use [emphasis] for lesson number/name
- Use [step] for each learning objective (3-4 max)
- Add Notes: with timing and warm-up question

Slide 2: Lead-in / Discussion
- Use [question] for discussion prompts
- Add bullet points with "Think about:"
- Add Notes: with interaction instructions

Slide 3: Reading / Case Study
- Use LeftTop: for passage (150-250 words)
- Use LeftBottom: for comprehension questions (3-4)
- Add Notes: with reading strategy

Slide 4: Vocabulary
- Option A: Use Template: vocabulary
- Option B: Use Left: (term) and Right: (definition)
- Use [vocabulary] tag on terms
- Add Notes: with pronunciation tips

Slide 5: Grammar / Language Focus
- Use four-box layout for rules, examples, practice, notes
- LeftTop: [emphasis] Rule/Form with explanation
- RightTop: [emphasis] Practice with exercises
- LeftBottom: [emphasis] Common Errors
- RightBottom: [emphasis] Usage Notes

Slide 6: Practice Activity
- Use Content: with [emphasis] for task title
- Use [step] for sequential instructions
- Add Notes: with timing and monitoring tips

Slide 7: Speaking / Production
- Use [question] for prompts
- Provide structure/scaffolding
- Add Notes: with grouping suggestions

Slide 8: Recap + Reflection
- Use [emphasis] for "Today we covered:"
- Use checkmarks (✓) for completed items
- Use [question] for reflection questions
- Add Notes: with homework assignment

================================================================================
EXAMPLE COMPLETE SLIDE
================================================================================

Slide 1
Title: Professional Email Writing
Content: [emphasis] Lesson 1
Content: Business Communication Skills
Content: 
Content: Today's Focus:
Content: [step] Email structure and conventions
Content: [step] Professional language and tone
Content: [step] Common business phrases
Notes: Warm-up about email challenges. 5 minutes.

---

Slide 2
Title: Lead-in Discussion
Content: [question] How many emails do you write per week?
Content: [question] What makes a professional email effective?
Content: 
Content: Think about:
Content: • Clarity and conciseness
Content: • Appropriate tone
Content: • Professional formatting
Notes: Pair discussion 3 minutes. Elicit responses.

---

================================================================================
TEACHER NOTES - ALWAYS INCLUDE
================================================================================

Every slide should have Notes: with:
- Timing estimate (e.g., "5 minutes")
- Interaction type (pair work, whole class, individual)
- Key instructions for teacher
- Common errors to watch for
- Extension activities if time permits

EXAMPLE:
Notes: Elicit answers first. Drill pronunciation. CCQ: "Can something resilient break easily?" (No). Give 2 min for pair discussion. Monitor for past tense errors. 8-10 minutes total.

================================================================================
COMMON MISTAKES TO AVOID
================================================================================

❌ Forgetting "Slide X" at the start
❌ Missing "Title:" on any slide
❌ Using wrong section names (e.g., "LeftSide:" instead of "Left:")
❌ Too much text in four-box layouts (>150 chars per box)
❌ Not using style tags ([vocabulary], [question], etc.)
❌ Forgetting teacher notes
❌ Mixing layouts incorrectly

================================================================================
CONTENT GENERATION CHECKLIST
================================================================================

Before submitting content, verify:
□ Every slide starts with "Slide X"
□ Every slide has "Title: [text]"
□ Appropriate layout chosen for content type
□ [vocabulary] tags used for new terms
□ [question] tags used for discussion prompts
□ [emphasis] tags used for key points
□ [step] tags used for sequential content
□ Teacher notes included on every slide
□ Content length appropriate (not too long)
□ Slides separated with "---"
□ 8-10 slides total per lesson

================================================================================
LEVEL-SPECIFIC GUIDELINES
================================================================================

A1-A2 (Beginner):
- Simple vocabulary and short sentences
- More images and visual support
- 6-8 slides per lesson

B1-B2 (Intermediate):
- Moderate complexity vocabulary
- Longer reading passages (150-200 words)
- 8-10 slides per lesson

C1-C2 (Advanced):
- Advanced vocabulary and idioms
- Complex texts (200-250 words)
- 10-12 slides per lesson

================================================================================
OUTPUT FORMAT
================================================================================

Your output should be plain text starting with:

# Lesson Name
# Level: XX | Duration: XX minutes

Then proceed with slides as shown in examples above.

================================================================================
END OF INSTRUCTIONS
================================================================================
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
        file_name="AI_Instructions_EducationalPPT_Generator.txt",
        mime="text/plain",
        help="Download this file to give to AI (ChatGPT, Claude, etc.)"
    )
    
    st.markdown("### 📝 Sample AI Prompts")
    
    with st.expander("🗣️ Conversation Practice Lesson"):
        st.code("""I need to create an English lesson using the Educational PowerPoint Generator format.

[Attach or paste the AI_Instructions_EducationalPPT_Generator.txt file]

Please create a lesson with these specifications:
- Topic: Conversation practice - Making small talk at networking events
- Level: B1 (Intermediate)
- Duration: 60 minutes
- Focus: Ice breakers, follow-up questions, showing interest
- Include: Vocabulary, example dialogues, practice activities
- 8-10 slides following the structure in the instructions

Generate the complete content file in the exact format specified.""", language="text")
    
    with st.expander("💼 Business English Lesson"):
        st.code("""I need to create an English lesson using the Educational PowerPoint Generator format.

[Attach or paste the AI_Instructions_EducationalPPT_Generator.txt file]

Please create a lesson with these specifications:
- Topic: Writing professional emails - Making requests
- Level: B2 (Upper Intermediate)
- Duration: 60 minutes
- Focus: Formal language, polite requests, appropriate tone
- Include: Email structure, key phrases, practice writing activity
- 8-10 slides following the structure in the instructions

Generate the complete content file in the exact format specified.""", language="text")
    
    with st.expander("🔬 Technical/Specialist Language"):
        st.code("""I need to create an English lesson using the Educational PowerPoint Generator format.

[Attach or paste the AI_Instructions_EducationalPPT_Generator.txt file]

Please create a lesson with these specifications:
- Topic: IT Architecture - Describing cloud infrastructure
- Level: B2-C1 (Business English for Technical Architects)
- Duration: 60 minutes
- Focus: Technical vocabulary, explaining systems, comparing solutions
- Include: Case study, technical terms, practice describing projects
- 8-10 slides following the structure in the instructions

Generate the complete content file in the exact format specified.""", language="text")
    
    with st.expander("📰 News Article Lesson"):
        st.code("""I need to create an English lesson using the Educational PowerPoint Generator format.

[Attach or paste the AI_Instructions_EducationalPPT_Generator.txt file]

Please create a lesson based on this news article:
[Paste the article text or URL]

Specifications:
- Level: B1 (Intermediate)
- Duration: 60 minutes
- Include: Simplified reading passage (200 words), comprehension questions, vocabulary, discussion
- 8-10 slides following the structure in the instructions

Generate the complete content file in the exact format specified.""", language="text")
    
    with st.expander("📚 Grammar Focus Lesson"):
        st.code("""I need to create an English lesson using the Educational PowerPoint Generator format.

[Attach or paste the AI_Instructions_EducationalPPT_Generator.txt file]

Please create a lesson with these specifications:
- Topic: Past Simple vs Present Perfect
- Level: B1 (Intermediate)
- Duration: 60 minutes
- Focus: Form, usage differences, time expressions, practice
- Include: Rule explanation, examples, controlled practice, freer practice
- 8-10 slides following the structure in the instructions

Generate the complete content file in the exact format specified.""", language="text")
    
    st.markdown("---")
    st.markdown("### Getting Started")
    st.write("""
    **Option 1: Use AI to Generate Content**
    1. **Download** the AI instruction file above
    2. **Give it to AI** (ChatGPT, Claude, Gemini, etc.) with your lesson specifications
    3. **Copy** the generated content
    4. **Paste** into the editor or upload as .txt file
    5. **Validate** and **Generate**
    
    **Option 2: Write Content Manually**
    1. **Write or upload** your lesson content using Educational PowerPoint generator syntax
    2. **Validate** to check for errors
    3. **Generate** to create your PowerPoint presentation
    4. **Download** and use in your lesson!
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
        ```
        Content: [step] First point
        Content: [step] Second point
        Content: [step] Third point
        ```
        Each step creates a separate shape for easy animation.
        """)
    
    with st.expander("❓ Can I use images?"):
        st.write("""
        Yes! Upload images to the same folder and reference them:
        ```
        Image: diagram.png | width=5 | align=center
        ```
        Supported parameters: width, left, top, align
        """)
    

    
    st.markdown("### Example Lesson Structure")
    
    st.code("""
Slide 1 - Title & Objectives (with [step] animations)
Slide 2 - Lead-in Discussion (with [question] tags)
Slide 3 - Reading Passage + Questions (LeftTop/LeftBottom)
Slide 4 - Vocabulary (Template: vocabulary)
Slide 5 - Grammar Explanation (4-box layout)
Slide 6 - Practice Exercise
Slide 7 - Speaking Activity
Slide 8 - Recap & Homework
    """, language="text")



