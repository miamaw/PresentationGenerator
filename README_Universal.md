# Universal PowerPoint Generator

A fully customizable web-based tool for creating educational presentations. No branding - make it your own!

## 🎨 Features

### Full Customization
- ✅ **Choose your fonts** - Title and body text
- ✅ **Custom colors** - Titles, text, and style tags
- ✅ **Upload backgrounds** - Your own images
- ✅ **Solid color backgrounds** - Any color you want
- ✅ **Style tag colors** - Customize [vocabulary], [question], [answer], [emphasis]

### Powerful Functionality
- Multiple slide layouts (single column, two columns, four boxes, reading comprehension)
- Automatic list formatting
- Math symbol support (x^2, H_2O, ≥, π, etc.)
- Smart font sizing for long text
- Slide numbering
- Teacher notes
- Step-by-step animations with [step] tag

### Easy to Use
- Web-based - works on any device
- No installation required for end users
- Visual customization controls
- Real-time preview
- Validation before generation

---

## 🚀 Quick Start

### Local Installation

1. **Install requirements:**
```bash
pip install streamlit python-pptx Pillow
```

2. **Run the app:**
```bash
streamlit run streamlit_app_universal.py
```

3. **Open browser** - automatically opens at `http://localhost:8501`

### Cloud Deployment (Streamlit Cloud)

1. Upload these files to GitHub:
   - `streamlit_app_universal.py`
   - `generate_presentation_universal.py`
   - `requirements.txt`

2. Deploy at https://share.streamlit.io

3. Get your permanent URL!

---

## 📖 How to Use

### Step 1: Customize Design
Open the sidebar and customize:
- **Background:** Choose solid color or upload image
- **Fonts:** Select title and body fonts
- **Colors:** Pick colors for titles and text
- **Style Tags:** Customize colors for special formatting

### Step 2: Create Content
Write your lesson using the simple syntax:
```
Slide 1
Title: My Lesson
Content: [emphasis] Main Topic
Content: [step] First point
Content: [step] Second point
---
```

### Step 3: Generate
- Click "Validate" to check for errors
- Click "Generate PowerPoint"
- Download your custom presentation!

---

## 📝 Content Syntax

### Basic Structure
```
Slide 1
Title: Slide Title
Content: Your content here
Notes: Teacher notes
---
```

### Layouts

**Single Column:**
```
Content: Main point
Content: Another point
```

**Two Columns:**
```
Left: Left content
Right: Right content
```

**Four Boxes:**
```
LeftTop: Top left
RightTop: Top right
LeftBottom: Bottom left
RightBottom: Bottom right
```

**Reading Comprehension:**
```
LeftTop: Reading passage here...
LeftBottom: 1. Question one?
LeftBottom: 2. Question two?
```

### Style Tags

- `[vocabulary]` - Vocabulary terms (customizable color)
- `[question]` - Discussion questions (customizable color)
- `[answer]` - Model answers (customizable color)
- `[emphasis]` - Important points (customizable color)
- `[step]` - Sequential animations

### Example
```
Slide 1
Title: Professional Communication
Content: [emphasis] Lesson 1
Content: 
Content: Learning Objectives:
Content: [step] Write professional emails
Content: [step] Use formal language
Content: [step] Structure messages clearly
Notes: Warm-up discussion. 5 minutes.
---

Slide 2
Title: Key Vocabulary
Left: [vocabulary] formal
Right: Following official rules or customs
Left: [vocabulary] concise
Right: Giving information clearly with few words
Notes: Drill pronunciation.
---
```

---

## 🎨 Customization Guide

### Background Images
- **Recommended size:** 1920x1080 or 1280x720
- **Format:** JPG, PNG
- **Upload:** Use the sidebar uploader

### Fonts
Available fonts:
- Arial
- Calibri
- Times New Roman
- Georgia
- Verdana
- Tahoma
- Trebuchet MS
- Comic Sans MS
- Impact
- Montserrat

### Color Schemes

**Professional:**
- Title: #000066 (dark blue)
- Text: #333333 (dark gray)
- Background: #FFFFFF (white)

**Vibrant:**
- Title: #FF6B35 (orange)
- Text: #004E89 (blue)
- Background: #F7F7F7 (light gray)

**Minimalist:**
- Title: #000000 (black)
- Text: #4A4A4A (medium gray)
- Background: #FFFFFF (white)

**Dark Mode:**
- Title: #FFD700 (gold)
- Text: #E0E0E0 (light gray)
- Background: #2C2C2C (dark gray)

---

## 🛠️ Technical Details

### Requirements
- Python 3.8+
- streamlit>=1.28.0
- python-pptx>=0.6.21
- Pillow>=10.0.0

### File Structure
```
universal-generator/
├── streamlit_app_universal.py (web interface)
├── generate_presentation_universal.py (generator engine)
├── requirements.txt (dependencies)
└── README.md (this file)
```

### Configuration
Settings are stored in session state during use:
- Fonts
- Colors
- Background choice
- Options (slide numbers, warnings)

---

## 🎯 Use Cases

### Education
- Language lessons
- Science presentations
- Math tutorials
- History lessons
- Any subject!

### Business Training
- Onboarding materials
- Product training
- Sales presentations
- Internal communications

### Workshops & Seminars
- Training materials
- Conference presentations
- Workshop handouts
- Seminar slides

---

## 💡 Tips

### Content Length
- Slide titles: Max 60 characters
- Single column: Up to 500 characters
- Two columns: Up to 300 characters per column
- Four boxes: Up to 150 characters per box
- Reading passages: 800-1000 characters

### Best Practices
1. ✅ Keep titles short and clear
2. ✅ Use [step] for sequential reveals (max 5-7 per slide)
3. ✅ Use style tags consistently
4. ✅ Validate before generating
5. ✅ Test your color scheme for readability

### Accessibility
- Ensure good contrast between text and background
- Use readable fonts (avoid overly decorative fonts for body text)
- Keep font sizes appropriate (auto-sizing helps with this)
- Consider colorblind-friendly palettes

---

## 🐛 Troubleshooting

**"Generator module not found"**
→ Ensure `generate_presentation_universal.py` is in the same directory

**"Background image not loading"**
→ Check file format (JPG, PNG only) and try re-uploading

**"Text overlapping"**
→ Reduce content length or split into multiple slides

**"Colors not applying"**
→ Make sure you're using the style tags correctly: `[vocabulary]`, `[question]`, etc.

---

## 📜 License

MIT License - Free to use, modify, and distribute for any purpose.

---

## 🙏 Credits

Created for educators worldwide. No branding, no restrictions - make it yours!

**Version 1.0** | 2025