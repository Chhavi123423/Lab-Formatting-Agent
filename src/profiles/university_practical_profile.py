from typing import Dict, Any
from src.config import DEFAULT_PAGE_CONFIG


def get_university_practical_profile() -> Dict[str, Any]:
    """
    Returns the formatting profile matching University Practical Files
    (e.g., CIC-351 / B.Tech practical lab file standards).
    - Font: Times New Roman
    - Color: Monochrome Black (RGB 0, 0, 0)
    - Header: Split 2-column (Subject Name Left, Subject Code Right)
    - Title: Centered, Bold, Uppercase (e.g. EXPERIMENT-3)
    - Inline Headings: AIM: and THEORY: on the same paragraph as the text
    - Block Headings: CODE: and OUTPUT: on separate lines
    - Footer / Stamp: Bottom-left student details (Name, Class, Roll No)
    """
    return {
        "profile_name": "UNIVERSITY_PRACTICAL_PROFILE",
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
            "font_family": "Times New Roman",
            "primary_color_rgb": (0, 0, 0),
            "title": {
                "font": "Times New Roman",
                "size_pt": 14,
                "bold": True,
                "uppercase": True,
                "color_rgb": (0, 0, 0),
                "alignment": "CENTER",
                "space_before_pt": 6,
                "space_after_pt": 12,
            },
            "h1": {
                "font": "Times New Roman",
                "size_pt": 12,
                "bold": True,
                "uppercase": True,
                "color_rgb": (0, 0, 0),
                "space_before_pt": 8,
                "space_after_pt": 4,
                "keep_with_next": True,
            },
            "h2": {
                "font": "Times New Roman",
                "size_pt": 12,
                "bold": True,
                "uppercase": True,
                "color_rgb": (0, 0, 0),
                "space_before_pt": 6,
                "space_after_pt": 3,
                "keep_with_next": True,
            },
            "h3": {
                "font": "Times New Roman",
                "size_pt": 12,
                "bold": True,
                "italic": True,
                "uppercase": True,
                "color_rgb": (0, 0, 0),
                "space_before_pt": 4,
                "space_after_pt": 2,
                "keep_with_next": True,
            },
            "body": {
                "font": "Times New Roman",
                "size_pt": 12,
                "line_spacing": 1.15,
                "space_after_pt": 6,
                "color_rgb": (0, 0, 0),
            },
            "code": {
                "font": "Consolas",
                "size_pt": 10,
                "line_spacing": 1.0,
                "space_after_pt": 4,
                "bg_color_hex": "FFFFFF",  # Clean unshaded code block as seen in sample
                "border_color_hex": "E0E0E0",
                "boxed": False,
            },
            "image": {
                "alignment": "CENTER",
                "max_width_inches": 5.5,
                "space_before_pt": 6,
                "space_after_pt": 6,
                "caption_font": "Times New Roman",
                "caption_size_pt": 10,
                "caption_italic": True,
            },
            "header": {
                "layout": "TWO_COLUMN_SPLIT",
                "font": "Times New Roman",
                "size_pt": 11,
                "color_rgb": (0, 0, 0),
            },
            "footer": {
                "layout": "STUDENT_STAMP",
                "position": "BOTTOM_LEFT",
                "font": "Times New Roman",
                "size_pt": 11,
                "color_rgb": (0, 0, 0),
            }
        },
        "inline_headings": ["AIM", "THEORY"],
        "block_headings": ["CODE", "IMPLEMENTATION", "OUTPUT", "RESULT", "CONCLUSION"]
    }

