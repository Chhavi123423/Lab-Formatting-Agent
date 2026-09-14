import io
import json
import os
import re
from typing import Dict, Any, Tuple, Optional
from PIL import Image
from src.config import GEMINI_API_KEY, DEFAULT_PAGE_CONFIG
from src.profiles.university_practical_profile import get_university_practical_profile


def convert_file_to_pil_image(file_bytes: bytes, filename: str) -> Image.Image:
    """Converts uploaded file (PDF or Image) to a PIL Image (page 1 if PDF)."""
    fn_lower = filename.lower()
    if fn_lower.endswith(".pdf"):
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(file_bytes)
        page = pdf[0]
        bitmap = page.render(scale=2.0)
        return bitmap.to_pil()
    else:
        return Image.open(io.BytesIO(file_bytes))


def normalize_extracted_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures the extracted JSON has all required canonical profile keys and defaults."""
    font_fam = data.get("font_family", "Times New Roman")
    primary_rgb = tuple(data.get("primary_color_rgb", [0, 0, 0]))
    header_info = data.get("header", {})
    footer_info = data.get("footer", {})
    code_info = data.get("code_style", {})

    inline_headings = data.get("inline_headings", ["AIM", "THEORY"])
    block_headings = data.get("block_headings", ["CODE", "IMPLEMENTATION", "OUTPUT", "RESULT"])

    return {
        "profile_name": data.get("profile_name", "AI_EXTRACTED_PROFILE"),
        "page": {
            "size": "A4",
            "width_inches": DEFAULT_PAGE_CONFIG["page_width_inches"],
            "height_inches": DEFAULT_PAGE_CONFIG["page_height_inches"],
            "margin_top_inches": 1.0,
            "margin_bottom_inches": 1.0,
            "margin_left_inches": 1.0,
            "margin_right_inches": 1.0,
        },
        "typography": {
            "font_family": font_fam,
            "primary_color_rgb": primary_rgb,
            "title": {
                "font": font_fam,
                "size_pt": 14,
                "bold": True,
                "uppercase": True,
                "color_rgb": primary_rgb,
                "alignment": "CENTER",
                "space_before_pt": 6,
                "space_after_pt": 12,
            },
            "h1": {
                "font": font_fam,
                "size_pt": 12,
                "bold": True,
                "uppercase": True,
                "color_rgb": primary_rgb,
                "space_before_pt": 8,
                "space_after_pt": 4,
                "keep_with_next": True,
            },
            "h2": {
                "font": font_fam,
                "size_pt": 12,
                "bold": True,
                "uppercase": True,
                "color_rgb": primary_rgb,
                "space_before_pt": 6,
                "space_after_pt": 3,
                "keep_with_next": True,
            },
            "h3": {
                "font": font_fam,
                "size_pt": 12,
                "bold": True,
                "italic": True,
                "uppercase": True,
                "color_rgb": primary_rgb,
                "space_before_pt": 4,
                "space_after_pt": 2,
                "keep_with_next": True,
            },
            "body": {
                "font": font_fam,
                "size_pt": 12,
                "line_spacing": 1.15,
                "space_after_pt": 6,
                "color_rgb": primary_rgb,
            },
            "code": {
                "font": "Consolas",
                "size_pt": 10,
                "line_spacing": 1.0,
                "space_after_pt": 4,
                "bg_color_hex": "FFFFFF" if not code_info.get("boxed", False) else "F4F4F4",
                "border_color_hex": "E0E0E0",
                "boxed": code_info.get("boxed", False),
            },
            "image": {
                "alignment": "CENTER",
                "max_width_inches": 5.5,
                "space_before_pt": 6,
                "space_after_pt": 6,
                "caption_font": font_fam,
                "caption_size_pt": 10,
                "caption_italic": True,
            },
            "header": {
                "layout": header_info.get("layout", "TWO_COLUMN_SPLIT"),
                "font": font_fam,
                "size_pt": 11,
                "color_rgb": primary_rgb,
                "left_text": header_info.get("left_text", ""),
                "right_text": header_info.get("right_text", ""),
            },
            "footer": {
                "layout": footer_info.get("layout", "STUDENT_STAMP"),
                "position": footer_info.get("position", "BOTTOM_LEFT"),
                "font": font_fam,
                "size_pt": 10.5,
                "color_rgb": primary_rgb,
            }
        },
        "inline_headings": [h.upper() for h in inline_headings],
        "block_headings": [h.upper() for h in block_headings]
    }


def extract_formatting_rules_from_sample(
    file_bytes: bytes,
    filename: str,
    api_key: Optional[str] = None
) -> Tuple[bool, Dict[str, Any], str]:
    """
    Analyzes an uploaded reference lab file page (PDF/Image) using Gemini Vision AI.
    Extracts the document formatting rules (fonts, header, footer, inline headings).
    Returns: (success: bool, formatting_profile: dict, status_message: str)
    """
    effective_key = api_key or os.getenv("GEMINI_API_KEY", "") or GEMINI_API_KEY

    if not effective_key:
        fallback = get_university_practical_profile()
        return (
            False,
            fallback,
            "Gemini API key is not configured. Falling back to default University Practical File rules."
        )

    try:
        pil_image = convert_file_to_pil_image(file_bytes, filename)
    except Exception as e:
        fallback = get_university_practical_profile()
        return (
            False,
            fallback,
            f"Could not load reference file: {str(e)}. Using default University Practical File rules."
        )

    prompt = (
        "You are an expert typography and document layout analyst.\n"
        "Analyze this sample experiment/lab file page and extract its formatting rules into strict JSON.\n\n"
        "Rules to extract:\n"
        "1. font_family: e.g. 'Times New Roman' or 'Calibri' or 'Arial'\n"
        "2. primary_color_rgb: RGB list e.g. [0, 0, 0] for black\n"
        "3. header: {\n"
        "     'layout': 'TWO_COLUMN_SPLIT' (if left title and right subject code exist) or 'CENTERED' or 'NONE',\n"
        "     'left_text': sample text detected on the left header (if any),\n"
        "     'right_text': sample text detected on the right header (if any)\n"
        "   }\n"
        "4. footer: {\n"
        "     'layout': 'STUDENT_STAMP' (if student name, class, roll no block exists) or 'PAGE_NUMBER' or 'NONE',\n"
        "     'position': 'BOTTOM_LEFT' or 'BOTTOM_CENTER' or 'BOTTOM_RIGHT'\n"
        "   }\n"
        "5. inline_headings: list of headings whose content starts on the SAME line as the bold heading label (e.g. ['AIM', 'THEORY'])\n"
        "6. block_headings: list of headings on their own line above code or text (e.g. ['CODE', 'OUTPUT', 'RESULT'])\n"
        "7. code_style: {'boxed': true or false}\n\n"
        "Return ONLY the JSON object with no markdown fences, no conversational text."
    )

    try:
        from google import genai
        client = genai.Client(api_key=effective_key)

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[pil_image, prompt],
        )

        if response and response.text:
            cleaned = re.sub(r"^```(?:json)?\n|\n```$", "", response.text.strip())
            data = json.loads(cleaned)
            normalized = normalize_extracted_profile(data)
            return (
                True,
                normalized,
                f"Successfully extracted formatting rules! (Font: {normalized['typography']['font_family']}, "
                f"Header: {normalized['typography']['header']['layout']}, "
                f"Inline Headings: {', '.join(normalized['inline_headings'])})"
            )
        else:
            fallback = get_university_practical_profile()
            return (
                False,
                fallback,
                "Vision model did not return formatting parameters. Using standard University Practical rules."
            )

    except Exception as e:
        fallback = get_university_practical_profile()
        return (
            False,
            fallback,
            f"Vision AI analysis failed ({str(e)}). Using standard University Practical rules."
        )

