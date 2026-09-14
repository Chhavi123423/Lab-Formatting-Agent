import io
from PIL import Image
from src.style_extractor import normalize_extracted_profile, extract_formatting_rules_from_sample


def test_normalize_extracted_profile():
    raw_ai_output = {
        "profile_name": "TEST_COLLEGE_FORMAT",
        "font_family": "Arial",
        "primary_color_rgb": [50, 50, 50],
        "header": {
            "layout": "TWO_COLUMN_SPLIT",
            "left_text": "OPERATING SYSTEMS",
            "right_text": "CS-401"
        },
        "footer": {
            "layout": "STUDENT_STAMP",
            "position": "BOTTOM_LEFT"
        },
        "inline_headings": ["AIM", "THEORY"],
        "block_headings": ["CODE", "OUTPUT"],
        "code_style": {"boxed": False}
    }

    norm = normalize_extracted_profile(raw_ai_output)
    assert norm["profile_name"] == "TEST_COLLEGE_FORMAT"
    assert norm["typography"]["font_family"] == "Arial"
    assert norm["typography"]["primary_color_rgb"] == (50, 50, 50)
    assert norm["typography"]["header"]["layout"] == "TWO_COLUMN_SPLIT"
    assert norm["typography"]["code"]["boxed"] is False
    assert "AIM" in norm["inline_headings"]
    assert "CODE" in norm["block_headings"]


def test_extract_formatting_rules_fallback():
    # If no API key or invalid image bytes, should return graceful fallback
    fake_bytes = b"not_an_image"
    success, profile, msg = extract_formatting_rules_from_sample(fake_bytes, "test.png")
    assert profile is not None
    assert "typography" in profile
    assert "page" in profile

