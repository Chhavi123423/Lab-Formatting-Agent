import io
from PIL import Image
from src.screenshot_processor import process_screenshot_embed


def test_process_screenshot_embed():
    # Create a 1200x800 test image in memory
    img = Image.new("RGB", (1200, 800), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    out_bytes, w, h = process_screenshot_embed(raw_bytes, max_width_inches=5.5)
    assert len(out_bytes) > 0
    assert w <= 5.5
    # Aspect ratio check: 800/1200 = ~0.666
    expected_h = round(w * (800 / 1200), 2)
    assert round(h, 2) == expected_h

