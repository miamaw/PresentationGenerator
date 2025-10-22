"""
Slide Preview Generator
=======================
Creates visual thumbnails of slides with correct colors, fonts, and backgrounds
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.figure import Figure
from PIL import Image
import io
import textwrap


def hex_to_rgb_norm(hex_color):
    """Convert hex to normalized RGB (0-1 range) for matplotlib"""
    if isinstance(hex_color, list):
        return [c/255 for c in hex_color]
    hex_color = hex_color.lstrip('#')
    rgb = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
    return [c/255 for c in rgb]


def parse_styled_text_preview(text):
    """Extract style and clean text for preview"""
    import re
    match = re.match(r'^\[(\w+)\]\s*(.+)', text)
    if match:
        return match.group(1), match.group(2)
    return None, text


def get_style_color(style, config):
    """Get color for a style tag"""
    styles = config.get("styles", {})
    if style in styles:
        return hex_to_rgb_norm(styles[style].get("color", [64, 64, 64]))
    return hex_to_rgb_norm(config.get("text_color", [64, 64, 64]))


def wrap_text(text, width=50):
    """Wrap text to specified width"""
    return '\n'.join(textwrap.wrap(text, width=width))


def create_slide_preview(slide_data, config, width=800, height=450):
    """
    Create a visual preview of a slide
    Returns: PIL Image
    """
    # Create figure with correct aspect ratio
    dpi = 100
    fig = Figure(figsize=(width/dpi, height/dpi), dpi=dpi)
    ax = fig.add_subplot(111)
    
    # Remove axes
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7.5)
    ax.axis('off')
    
    # Background
    bg_color = hex_to_rgb_norm(config.get("background_color", [255, 255, 255]))
    
    if config.get("background_image"):
        # Try to load background image
        try:
            bg_img = Image.open(config["background_image"])
            ax.imshow(bg_img, extent=[0, 10, 0, 7.5], aspect='auto', zorder=0)
        except:
            # Fallback to solid color
            rect = patches.Rectangle((0, 0), 10, 7.5, 
                                     facecolor=bg_color, 
                                     edgecolor='none', zorder=0)
            ax.add_patch(rect)
    else:
        # Solid color background
        rect = patches.Rectangle((0, 0), 10, 7.5, 
                                 facecolor=bg_color, 
                                 edgecolor='none', zorder=0)
        ax.add_patch(rect)
    
    # Title
    title_color = hex_to_rgb_norm(config.get("title_color", [0, 0, 0]))
    title_font = config.get("title_font_name", config.get("font_name", "Arial"))
    
    ax.text(1.5, 6.5, slide_data.get("title", "Untitled"), 
            fontsize=20, fontweight='bold', 
            color=title_color,
            fontfamily=title_font.lower() if title_font.lower() in ['serif', 'sans-serif', 'monospace'] else 'sans-serif',
            verticalalignment='top',
            zorder=2)
    
    # Content area
    content_left = 1.5
    content_top = 5.8
    content_width = 7
    text_color = hex_to_rgb_norm(config.get("text_color", [64, 64, 64]))
    body_font = config.get("font_name", "Arial")
    
    # Determine layout and render content
    if slide_data.get("left_top") and slide_data.get("left_bottom") and not slide_data.get("right_top"):
        # Reading layout (stacked)
        render_reading_layout(ax, slide_data, config, content_left, content_top)
    
    elif any([slide_data.get("left_top"), slide_data.get("right_top"), 
              slide_data.get("left_bottom"), slide_data.get("right_bottom")]):
        # 4-box layout
        render_four_box_layout(ax, slide_data, config, content_left, content_top)
    
    elif slide_data.get("left") or slide_data.get("right"):
        # Two-column layout
        render_two_column_layout(ax, slide_data, config, content_left, content_top)
    
    else:
        # Single column
        render_single_column(ax, slide_data, config, content_left, content_top)
    
    # Slide number (if enabled)
    if config.get("enable_slide_numbers", True):
        ax.text(9.5, 0.3, "1 / X", 
                fontsize=8, color=[0.5, 0.5, 0.5],
                horizontalalignment='right',
                zorder=2)
    
    # Convert to image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', 
                facecolor=bg_color, edgecolor='none')
    buf.seek(0)
    img = Image.open(buf)
    plt.close(fig)
    
    return img


def render_single_column(ax, slide_data, config, left, top):
    """Render single column content"""
    text_color = hex_to_rgb_norm(config.get("text_color", [64, 64, 64]))
    y_pos = top
    
    for line in slide_data.get("content", [])[:8]:  # Limit to 8 lines for preview
        if not line.strip():
            continue
        
        # Check for [step] marker
        line = line.replace("[step]", "").strip()
        
        # Parse style
        style, text = parse_styled_text_preview(line)
        color = get_style_color(style, config) if style else text_color
        
        # Wrap and truncate
        text = wrap_text(text, width=70)
        if len(text) > 100:
            text = text[:100] + "..."
        
        ax.text(left, y_pos, f"• {text}", 
                fontsize=9, color=color,
                verticalalignment='top',
                zorder=2)
        y_pos -= 0.5


def render_two_column_layout(ax, slide_data, config, left, top):
    """Render two-column layout"""
    text_color = hex_to_rgb_norm(config.get("text_color", [64, 64, 64]))
    col_width = 3.5
    gap = 0.3
    
    # Left column
    y_pos = top
    for line in slide_data.get("left", [])[:6]:
        if not line.strip():
            continue
        
        style, text = parse_styled_text_preview(line)
        color = get_style_color(style, config) if style else text_color
        text = wrap_text(text, width=35)
        
        ax.text(left, y_pos, text, 
                fontsize=9, color=color,
                verticalalignment='top',
                zorder=2)
        y_pos -= 0.5
    
    # Right column
    y_pos = top
    right_left = left + col_width + gap
    for line in slide_data.get("right", [])[:6]:
        if not line.strip():
            continue
        
        style, text = parse_styled_text_preview(line)
        color = get_style_color(style, config) if style else text_color
        text = wrap_text(text, width=35)
        
        ax.text(right_left, y_pos, text, 
                fontsize=9, color=color,
                verticalalignment='top',
                zorder=2)
        y_pos -= 0.5


def render_four_box_layout(ax, slide_data, config, left, top):
    """Render 4-box layout"""
    text_color = hex_to_rgb_norm(config.get("text_color", [64, 64, 64]))
    box_width = 3.5
    box_height = 2.3
    gap = 0.3
    
    boxes = [
        (left, top, slide_data.get("left_top", [])),
        (left + box_width + gap, top, slide_data.get("right_top", [])),
        (left, top - box_height - gap, slide_data.get("left_bottom", [])),
        (left + box_width + gap, top - box_height - gap, slide_data.get("right_bottom", []))
    ]
    
    for box_left, box_top, content in boxes:
        y_pos = box_top
        for line in content[:4]:  # Limit to 4 lines per box
            if not line.strip():
                continue
            
            style, text = parse_styled_text_preview(line)
            color = get_style_color(style, config) if style else text_color
            text = wrap_text(text, width=30)
            if len(text) > 80:
                text = text[:80] + "..."
            
            ax.text(box_left, y_pos, text, 
                    fontsize=8, color=color,
                    verticalalignment='top',
                    zorder=2)
            y_pos -= 0.4


def render_reading_layout(ax, slide_data, config, left, top):
    """Render reading comprehension layout"""
    text_color = hex_to_rgb_norm(config.get("text_color", [64, 64, 64]))
    
    # Reading passage (top 65%)
    passage_height = 3.5
    y_pos = top
    
    passage_text = " ".join(slide_data.get("left_top", []))
    wrapped_passage = wrap_text(passage_text, width=80)
    
    # Show first 200 chars
    if len(wrapped_passage) > 200:
        wrapped_passage = wrapped_passage[:200] + "..."
    
    ax.text(left, y_pos, wrapped_passage, 
            fontsize=8, color=text_color,
            verticalalignment='top',
            zorder=2)
    
    # Questions (bottom 35%)
    y_pos = top - passage_height - 0.5
    
    for i, question in enumerate(slide_data.get("left_bottom", [])[:3], 1):
        q_text = question.strip()
        if not q_text.startswith(str(i)):
            q_text = f"{i}. {q_text}"
        
        q_text = wrap_text(q_text, width=80)
        
        ax.text(left, y_pos, q_text, 
                fontsize=8, 
                color=get_style_color("question", config),
                verticalalignment='top',
                zorder=2)
        y_pos -= 0.5


def create_thumbnail_grid(slides, config, cols=3):
    """
    Create a grid of slide thumbnails
    Returns: PIL Image
    """
    if not slides:
        return None
    
    thumb_width = 320
    thumb_height = 180
    padding = 10
    
    rows = (len(slides) + cols - 1) // cols
    
    # Create composite image
    grid_width = cols * thumb_width + (cols + 1) * padding
    grid_height = rows * thumb_height + (rows + 1) * padding
    
    grid_img = Image.new('RGB', (grid_width, grid_height), color=(240, 240, 240))
    
    for idx, slide in enumerate(slides[:12]):  # Max 12 thumbnails
        row = idx // cols
        col = idx % cols
        
        x = col * thumb_width + (col + 1) * padding
        y = row * thumb_height + (row + 1) * padding
        
        # Generate thumbnail
        thumb = create_slide_preview(slide, config, width=thumb_width, height=thumb_height)
        grid_img.paste(thumb, (x, y))
    
    return grid_img