import io
from typing import Optional, Tuple
from PIL import Image
from src.config import GEMINI_API_KEY


def process_screenshot_embed(image_bytes: bytes, max_width_inches: float = 5.5) -> Tuple[bytes, float, float]:
    """
    Validates and computes proportional dimensions for embedding an image.
    Returns: (image_bytes, target_width_inches, target_height_inches)
    """
    img = Image.open(io.BytesIO(image_bytes))
    width_px, height_px = img.size

    # Assuming standard 96 DPI for screen images
    aspect_ratio = height_px / max(width_px, 1)

    target_width = min(max_width_inches, width_px / 96.0)
    # Ensure it doesn't get ridiculously small
    if target_width < 3.0 and width_px > 300:
        target_width = max_width_inches

    target_height = target_width * aspect_ratio

    # Re-save as PNG or JPEG in clean bytes buffer
    output_buf = io.BytesIO()
    img_format = img.format if img.format in ["PNG", "JPEG"] else "PNG"
    img.save(output_buf, format=img_format)
    return output_buf.getvalue(), target_width, target_height


def extract_text_from_screenshot_read_mode(image_bytes: bytes, api_key: Optional[str] = None) -> Tuple[bool, str, str]:
    """
    Extracts text from a terminal/console screenshot using Google Gemini Vision API.
    Returns: (success: bool, extracted_text: str, status_or_warning_message: str)
    """
    import os
    effective_key = api_key or os.getenv("GEMINI_API_KEY", "") or GEMINI_API_KEY

    if not effective_key:
        return (
            False,
            "",
            "Gemini API key is not configured. Falling back to Embed Mode."
        )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=effective_key)
        
        # Load image with PIL
        pil_img = Image.open(io.BytesIO(image_bytes))

        prompt = (
            "You are an exact terminal and console output transcriber.\n"
            "Extract the verbatim text, terminal commands, tabular output, and prompts shown in this screenshot.\n"
            "Output ONLY the exact transcribed text without markdown code blocks, without greetings, and without commentary."
        )

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[pil_img, prompt],
        )

        if response and response.text and response.text.strip():
            return True, response.text.strip(), "Text successfully extracted from screenshot."
        else:
            return False, "", "Vision model could not read text from screenshot. Falling back to Embed Mode."

    except Exception as e:
        return False, "", f"Vision API extraction encountered an error ({str(e)}). Falling back to Embed Mode."

