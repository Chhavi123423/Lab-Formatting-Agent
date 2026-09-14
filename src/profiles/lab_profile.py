from typing import Dict, Any
from src.config import DEFAULT_PAGE_CONFIG, DEFAULT_TYPOGRAPHY


def get_canonical_lab_profile() -> Dict[str, Any]:
    """
    Returns the canonical lab formatting specification.
    Defines appearance parameters only, NOT content sequence.
    """
    return {
        "profile_name": "CANONICAL_LAB_PROFILE_V1",
        "page": {
            "size": "A4",
            "width_inches": DEFAULT_PAGE_CONFIG["page_width_inches"],
            "height_inches": DEFAULT_PAGE_CONFIG["page_height_inches"],
            "margin_top_inches": DEFAULT_PAGE_CONFIG["margin_top_inches"],
            "margin_bottom_inches": DEFAULT_PAGE_CONFIG["margin_bottom_inches"],
            "margin_left_inches": DEFAULT_PAGE_CONFIG["margin_left_inches"],
            "margin_right_inches": DEFAULT_PAGE_CONFIG["margin_right_inches"],
        },
        "typography": {
            "title": {
                "font": "Calibri",
                "size_pt": 18,
                "bold": True,
                "color_rgb": (31, 78, 121),
                "alignment": "CENTER",
                "space_before_pt": 0,
                "space_after_pt": 14,
            },
            "h1": {
                "font": DEFAULT_TYPOGRAPHY["h1_font"],
                "size_pt": DEFAULT_TYPOGRAPHY["h1_size_pt"],
                "bold": DEFAULT_TYPOGRAPHY["h1_bold"],
                "color_rgb": DEFAULT_TYPOGRAPHY["h1_color_rgb"],
                "space_before_pt": DEFAULT_TYPOGRAPHY["h1_space_before_pt"],
                "space_after_pt": DEFAULT_TYPOGRAPHY["h1_space_after_pt"],
                "keep_with_next": True,
            },
            "h2": {
                "font": DEFAULT_TYPOGRAPHY["h2_font"],
                "size_pt": DEFAULT_TYPOGRAPHY["h2_size_pt"],
                "bold": DEFAULT_TYPOGRAPHY["h2_bold"],
                "color_rgb": DEFAULT_TYPOGRAPHY["h2_color_rgb"],
                "space_before_pt": DEFAULT_TYPOGRAPHY["h2_space_before_pt"],
                "space_after_pt": DEFAULT_TYPOGRAPHY["h2_space_after_pt"],
                "keep_with_next": True,
            },
            "h3": {
                "font": DEFAULT_TYPOGRAPHY["h3_font"],
                "size_pt": DEFAULT_TYPOGRAPHY["h3_size_pt"],
                "bold": DEFAULT_TYPOGRAPHY["h3_bold"],
                "italic": DEFAULT_TYPOGRAPHY["h3_italic"],
                "color_rgb": DEFAULT_TYPOGRAPHY["h3_color_rgb"],
                "space_before_pt": DEFAULT_TYPOGRAPHY["h3_space_before_pt"],
                "space_after_pt": DEFAULT_TYPOGRAPHY["h3_space_after_pt"],
                "keep_with_next": True,
            },
            "body": {
                "font": DEFAULT_TYPOGRAPHY["body_font"],
                "size_pt": DEFAULT_TYPOGRAPHY["body_size_pt"],
                "line_spacing": DEFAULT_TYPOGRAPHY["body_line_spacing"],
                "space_after_pt": DEFAULT_TYPOGRAPHY["body_space_after_pt"],
                "color_rgb": (0, 0, 0),
            },
            "code": {
                "font": DEFAULT_TYPOGRAPHY["code_font"],
                "size_pt": DEFAULT_TYPOGRAPHY["code_size_pt"],
                "line_spacing": DEFAULT_TYPOGRAPHY["code_line_spacing"],
                "space_after_pt": DEFAULT_TYPOGRAPHY["code_space_after_pt"],
                "bg_color_hex": DEFAULT_TYPOGRAPHY["code_bg_color_hex"],
                "border_color_hex": "D3D3D3",
            },
            "image": {
                "alignment": "CENTER",
                "max_width_inches": DEFAULT_TYPOGRAPHY["max_image_width_inches"],
                "space_before_pt": 6,
                "space_after_pt": 6,
                "caption_font": "Calibri",
                "caption_size_pt": 9.5,
                "caption_italic": True,
            },
            "header": {
                "font": "Calibri",
                "size_pt": 9,
                "color_rgb": (120, 120, 120),
            },
            "footer": {
                "font": "Calibri",
                "size_pt": 9,
                "color_rgb": (120, 120, 120),
            }
        }
    }

