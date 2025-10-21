"""
Universal PowerPoint Generator
================================
Generic, customizable presentation generator for educators
No branding - fully customizable fonts, colors, and backgrounds
"""

import sys
import os
import json
import re
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR


# === DEFAULT CONFIG ===
DEFAULT_CONFIG = {
    "background_image": None,  # Can be None for solid color
    "background_color": [255, 255, 255],  # White
    "title_color": [0, 0, 0],  # Black
    "text_color": [64, 64, 64],  # Dark gray
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


def merge_config(user_config, defaults=DEFAULT_CONFIG):
    """Merge user config with defaults"""
    config = defaults.copy()
    if user_config:
        config.update(user_config)
        # Merge nested styles
        if "styles" in user_config:
            config["styles"] = {**defaults["styles"], **user_config["styles"]}
    return config


# === OVERFLOW DETECTION ===
def check_text_overflow(text, font_size, width_inches, height_inches):
    """Estimates if text will overflow"""
    if hasattr(width_inches, 'inches'):
        width_inches = width_inches.inches
    if hasattr(height_inches, 'inches'):
        height_inches = height_inches.inches
    
    chars_per_inch = 72 / font_size * 2.5
    chars_per_line = int(width_inches * chars_per_inch)
    
    words = text.split()
    current_line_length = 0
    lines_needed = 1
    
    for word in words:
        word_length = len(word) + 1
        if current_line_length + word_length > chars_per_line:
            lines_needed += 1
            current_line_length = word_length
        else:
            current_line_length += word_length
    
    line_height = font_size / 72 * 1.3
    lines_available = int(height_inches / line_height)
    
    will_overflow = lines_needed > lines_available
    return will_overflow, lines_needed, lines_available


# === LIST DETECTION ===
def is_list_content(lines):
    """Detect if content should be formatted as a list"""
    if not lines:
        return False
    
    bullet_patterns = [r'^\s*[•\-\*]', r'^\s*\d+\.', r'^\s*[a-z]\)', r'^\s*[A-Z]\.']
    matching = sum(1 for line in lines if any(re.match(p, line) for p in bullet_patterns))
    return matching >= len(lines) * 0.5


def clean_bullet_marker(text):
    """Remove common bullet markers from text"""
    text = re.sub(r'^\s*[•\-\*]\s*', '', text)
    text = re.sub(r'^\s*\d+\.\s*', '', text)
    text = re.sub(r'^\s*[a-z]\)\s*', '', text)
    return text


# === QUESTION SPLITTING ===
def split_questions(text):
    """Robustly split multiple questions"""
    questions = re.split(r'\?\s*(?=\d+\.|\b[A-Z])', text)
    result = []
    
    for q in questions:
        q = q.strip()
        if q:
            if not q.endswith('?'):
                q += '?'
            result.append(q)
    
    return result if result else [text]


# === STYLE APPLICATION ===
def apply_style(paragraph, style_name, config):
    """Apply predefined style to a paragraph"""
    styles = config.get("styles", {})
    
    if style_name in styles:
        style = styles[style_name]
        paragraph.font.size = Pt(style.get("font_size", 22))
        
        if "color" in style:
            color = style["color"]
            paragraph.font.color.rgb = RGBColor(*color)
        
        paragraph.font.bold = style.get("bold", False)
        paragraph.font.italic = style.get("italic", False)


def parse_styled_text(text):
    """Parse text with inline style markers"""
    match = re.match(r'^\[(\w+)\]\s*(.+)', text)
    if match:
        return match.group(1), match.group(2)
    return None, text


# === MATH/SPECIAL CHARACTERS ===
def process_math(text):
    """Convert simple math notation to Unicode symbols"""
    superscripts = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', 
                    '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'}
    text = re.sub(r'\^(\d)', lambda m: superscripts.get(m.group(1), m.group(1)), text)
    
    subscripts = {'0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
                  '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉'}
    text = re.sub(r'_(\d)', lambda m: subscripts.get(m.group(1), m.group(1)), text)
    
    replacements = {
        '<=': '≤', '>=': '≥', '!=': '≠', '~=': '≈',
        'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ',
        'pi': 'π', 'theta': 'θ', 'sigma': 'σ'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


# === VALIDATION ===
def validate_slide(slide_data, slide_num, config):
    """Validate slide data"""
    issues = []
    
    if not slide_data["title"]:
        issues.append(f"Slide {slide_num}: Missing title")
    elif len(slide_data["title"]) > 100:
        issues.append(f"Slide {slide_num}: Title very long ({len(slide_data['title'])} chars)")
    
    has_content = any([
        slide_data["content"], slide_data["left"], slide_data["right"],
        slide_data["left_top"], slide_data["right_top"],
        slide_data["left_bottom"], slide_data["right_bottom"]
    ])
    
    if not has_content:
        issues.append(f"Slide {slide_num}: No content defined")
    
    return issues


# === ADD TEXTBOX ===
def add_textbox(slide, left, top, width, height, lines, font_size=22, label=None, 
                config=None, v_align=MSO_ANCHOR.TOP):
    """Enhanced textbox with overflow detection, list formatting, and styling"""
    if not lines:
        return None
    
    if config is None:
        config = DEFAULT_CONFIG
    
    joined = " ".join(lines)
    joined = process_math(joined)
    text_length = len(joined)
    
    # Overflow detection
    if config.get("enable_overflow_warnings", True):
        try:
            w = width.inches if hasattr(width, 'inches') else width
            h = height.inches if hasattr(height, 'inches') else height
            overflow, needed, available = check_text_overflow(joined, font_size, w, h)
            if overflow:
                print(f"⚠️  Potential overflow in '{label}': needs {needed} lines, has {available}")
        except Exception:
            pass
    
    # Auto font-size for long text
    if text_length > 300:
        font_size = min(font_size, 18)
    if text_length > 500:
        font_size = min(font_size, 16)
    if text_length > 700:
        font_size = min(font_size, 14)
    if text_length > 1000:
        font_size = min(font_size, 12)
    
    # Handle [step] animations
    step_lines = [l for l in lines if "[step]" in l.lower()]
    if step_lines:
        return add_step_textboxes(slide, left, top, width, lines, font_size, label, config)
    
    # Detect list formatting
    is_list = is_list_content(lines)
    
    # Create textbox
    box = slide.shapes.add_textbox(left, top, width, height)
    if label:
        box.name = label
    
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = v_align
    
    # Add content
    first = True
    for item in lines:
        if not item.strip():
            continue
        
        style, text = parse_styled_text(item)
        text = process_math(text)
        
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        
        if is_list:
            text = clean_bullet_marker(text)
            p.level = 0
            p.text = text
        else:
            p.text = text
        
        p.font.name = config["font_name"]
        if style:
            apply_style(p, style, config)
        else:
            p.font.size = Pt(font_size)
            p.font.color.rgb = RGBColor(*config["text_color"])
        
        if text_length > 300:
            p.space_after = Pt(3)
        else:
            p.space_after = Pt(6)
    
    return box


def add_step_textboxes(slide, left, top, width, lines, font_size, label, config):
    """Create separate textboxes for each [step] line"""
    top_offset = top
    boxes = []
    
    for i, item in enumerate(lines):
        if not item.strip():
            continue
        
        text = re.sub(r'\[step\]\s*', '', item, flags=re.IGNORECASE)
        text = process_math(text)
        style, text = parse_styled_text(text)
        
        box = slide.shapes.add_textbox(left, top_offset, width, Inches(0.6))
        if label:
            box.name = f"{label}_Step{i+1}"
        
        tf = box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.name = config["font_name"]
        
        if style:
            apply_style(p, style, config)
        else:
            p.font.size = Pt(font_size)
            p.font.color.rgb = RGBColor(*config["text_color"])
        
        boxes.append(box)
        top_offset += Inches(0.65)
    
    return boxes


# === ADD SLIDE NUMBER ===
def add_slide_number(slide, slide_num, total_slides, config):
    """Add slide number footer"""
    footer_text = f"{slide_num} / {total_slides}"
    
    footer = slide.shapes.add_textbox(
        Inches(config["slide_width"] - 1.5),
        Inches(config["slide_height"] - 0.5),
        Inches(1),
        Inches(0.3)
    )
    
    tf = footer.text_frame
    p = tf.paragraphs[0]
    p.text = footer_text
    p.font.size = Pt(12)
    p.font.color.rgb = RGBColor(128, 128, 128)
    p.alignment = PP_ALIGN.RIGHT


# === PARSER ===
def parse_content_file(filename):
    """Parse content file"""
    slides = []
    current = {
        "title": "", "content": [], "notes": [],
        "left": [], "right": [],
        "left_top": [], "right_top": [],
        "left_bottom": [], "right_bottom": [],
        "template": None
    }
    section = None

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip()
            
            if not line or line == "---":
                continue

            if line.startswith("Slide "):
                if current["title"]:
                    slides.append(current)
                    current = {
                        "title": "", "content": [], "notes": [],
                        "left": [], "right": [],
                        "left_top": [], "right_top": [],
                        "left_bottom": [], "right_bottom": [],
                        "template": None
                    }
                section = None
                continue

            if line.startswith("Template:"):
                current["template"] = line.replace("Template:", "").strip()
                continue

            if line.startswith("Title:"):
                current["title"] = line.replace("Title:", "").strip()
                section = None
                continue
            elif line.startswith("Content:"):
                section = "content"
                text = line.replace("Content:", "").strip()
            elif line.startswith("Left:"):
                section = "left"
                text = line.replace("Left:", "").strip()
            elif line.startswith("Right:"):
                section = "right"
                text = line.replace("Right:", "").strip()
            elif line.startswith("LeftTop:"):
                section = "left_top"
                text = line.replace("LeftTop:", "").strip()
            elif line.startswith("RightTop:"):
                section = "right_top"
                text = line.replace("RightTop:", "").strip()
            elif line.startswith("LeftBottom:"):
                section = "left_bottom"
                text = line.replace("LeftBottom:", "").strip()
                if any(q in text for q in ["1.", "2.", "3."]):
                    questions = split_questions(text)
                    current["left_bottom"].extend(questions)
                    continue
            elif line.startswith("RightBottom:"):
                section = "right_bottom"
                text = line.replace("RightBottom:", "").strip()
            elif line.startswith("Notes:"):
                section = "notes"
                text = line.replace("Notes:", "").strip()
            else:
                text = line

            if section in current and text:
                current[section].append(text)

        if current["title"]:
            slides.append(current)

    return slides


# === BUILD PRESENTATION ===
def build_presentation(slides, output_name, config=None):
    """Build presentation with custom styling"""
    if config is None:
        config = DEFAULT_CONFIG
    
    prs = Presentation()
    prs.slide_width = Inches(config["slide_width"])
    prs.slide_height = Inches(config["slide_height"])
    
    SLIDE_WIDTH = prs.slide_width
    SLIDE_HEIGHT = prs.slide_height
    TITLE_LEFT = Inches(1.5)
    TITLE_TOP = Inches(0.6)
    CONTENT_LEFT = Inches(1.5)
    CONTENT_TOP = Inches(1.5)
    CONTENT_WIDTH = Inches(10.5)
    CONTENT_HEIGHT = Inches(5.0)
    COLUMN_GAP = Inches(0.4)
    ROW_GAP = Inches(0.3)
    COLUMN_WIDTH = (CONTENT_WIDTH - COLUMN_GAP) / 2
    
    total_slides = len(slides)
    
    for idx, s in enumerate(slides, start=1):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        
        # Background
        if config.get("background_image") and os.path.exists(config["background_image"]):
            slide.shapes.add_picture(config["background_image"], 0, 0,
                                    width=SLIDE_WIDTH, height=SLIDE_HEIGHT)
        else:
            # Solid color background
            background = slide.background
            fill = background.fill
            fill.solid()
            fill.fore_color.rgb = RGBColor(*config.get("background_color", [255, 255, 255]))
        
        # Title
        title_box = slide.shapes.add_textbox(TITLE_LEFT, TITLE_TOP, CONTENT_WIDTH, Inches(0.8))
        tf = title_box.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = s["title"]
        p.font.name = config.get("title_font_name", config["font_name"])
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = RGBColor(*config["title_color"])
        
        # Layout logic
        if s["left_top"] and s["left_bottom"] and not (s["right_top"] or s["right_bottom"]):
            # Reading slide
            reading_height = CONTENT_HEIGHT * 0.65
            questions_height = CONTENT_HEIGHT * 0.35 - ROW_GAP
            
            add_textbox(slide, CONTENT_LEFT, CONTENT_TOP,
                       CONTENT_WIDTH, reading_height, s["left_top"], 
                       label="ReadingText", config=config, v_align=MSO_ANCHOR.TOP)
            add_textbox(slide, CONTENT_LEFT, CONTENT_TOP + reading_height + ROW_GAP,
                       CONTENT_WIDTH, questions_height, s["left_bottom"], 
                       label="ReadingQuestions", config=config, v_align=MSO_ANCHOR.TOP)
        
        elif any([s["left_top"], s["right_top"], s["left_bottom"], s["right_bottom"]]):
            # 4-box slide
            half_height = (CONTENT_HEIGHT - ROW_GAP) / 2
            box_font_size = 18
            
            add_textbox(slide, CONTENT_LEFT, CONTENT_TOP,
                       COLUMN_WIDTH, half_height, s["left_top"], 
                       font_size=box_font_size, label="LeftTop", config=config)
            add_textbox(slide, CONTENT_LEFT + COLUMN_WIDTH + COLUMN_GAP, CONTENT_TOP,
                       COLUMN_WIDTH, half_height, s["right_top"], 
                       font_size=box_font_size, label="RightTop", config=config)
            add_textbox(slide, CONTENT_LEFT, CONTENT_TOP + half_height + ROW_GAP,
                       COLUMN_WIDTH, half_height, s["left_bottom"], 
                       font_size=box_font_size, label="LeftBottom", config=config)
            add_textbox(slide, CONTENT_LEFT + COLUMN_WIDTH + COLUMN_GAP,
                       CONTENT_TOP + half_height + ROW_GAP,
                       COLUMN_WIDTH, half_height, s["right_bottom"], 
                       font_size=box_font_size, label="RightBottom", config=config)
        
        elif s["left"] or s["right"]:
            # Two-column layout
            add_textbox(slide, CONTENT_LEFT, CONTENT_TOP,
                       COLUMN_WIDTH, CONTENT_HEIGHT, s["left"], 
                       label="Left", config=config)
            add_textbox(slide, CONTENT_LEFT + COLUMN_WIDTH + COLUMN_GAP, CONTENT_TOP,
                       COLUMN_WIDTH, CONTENT_HEIGHT, s["right"], 
                       label="Right", config=config)
        
        else:
            # Single-column content
            add_textbox(slide, CONTENT_LEFT, CONTENT_TOP,
                       CONTENT_WIDTH, CONTENT_HEIGHT, s["content"], 
                       label="Content", config=config)
        
        # Add slide numbers
        if config.get("enable_slide_numbers", True):
            add_slide_number(slide, idx, total_slides, config)
        
        # Notes
        if s["notes"]:
            notes_slide = slide.notes_slide
            notes_tf = notes_slide.notes_text_frame
            for note in s["notes"]:
                notes_tf.add_paragraph().text = f"• {note}"
    
    prs.save(output_name)
    print(f"✅ Presentation created: {output_name}")


# === MAIN ===
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_presentation_universal.py <content.txt> [config.json]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    config_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    config = DEFAULT_CONFIG
    if config_file and os.path.exists(config_file):
        with open(config_file, 'r') as f:
            user_config = json.load(f)
            config = merge_config(user_config)
    
    slides = parse_content_file(input_file)
    
    base_name = input_file.replace(".txt", "")
    output_name = base_name + "_presentation.pptx"
    
    build_presentation(slides, output_name, config)
