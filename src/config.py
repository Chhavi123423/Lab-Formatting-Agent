import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root if it exists
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Default Canonical Page and Typography Configuration
DEFAULT_PAGE_CONFIG = {
    "page_size": "A4",
    "page_width_inches": 8.27,
    "page_height_inches": 11.69,
    "margin_top_inches": 1.0,
    "margin_bottom_inches": 1.0,
    "margin_left_inches": 1.0,
    "margin_right_inches": 1.0,
}

DEFAULT_TYPOGRAPHY = {
    "body_font": "Calibri",
    "body_size_pt": 11,
    "body_line_spacing": 1.15,
    "body_space_after_pt": 6,
    "h1_font": "Calibri",
    "h1_size_pt": 14,
    "h1_bold": True,
    "h1_color_rgb": (31, 78, 121),  # Academic navy blue
    "h1_space_before_pt": 12,
    "h1_space_after_pt": 6,
    "h2_font": "Calibri",
    "h2_size_pt": 12,
    "h2_bold": True,
    "h2_color_rgb": (0, 0, 0),
    "h2_space_before_pt": 8,
    "h2_space_after_pt": 4,
    "h3_font": "Calibri",
    "h3_size_pt": 11,
    "h3_bold": True,
    "h3_italic": True,
    "h3_color_rgb": (0, 0, 0),
    "h3_space_before_pt": 6,
    "h3_space_after_pt": 2,
    "code_font": "Consolas",
    "code_size_pt": 9.5,
    "code_line_spacing": 1.0,
    "code_space_after_pt": 4,
    "code_bg_color_hex": "F2F2F2",
    "max_image_width_inches": 5.5,
}

CANONICAL_LAB_SECTIONS = [
    "TITLE",
    "AIM",
    "OBJECTIVE",
    "THEORY",
    "ALGORITHM",
    "IMPLEMENTATION",
    "CODE",
    "OUTPUT",
    "RESULT",
    "CONCLUSION"
]

