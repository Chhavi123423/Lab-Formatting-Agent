from src.preprocessor import clean_input_text, extract_word_tokens


def test_clean_input_text():
    raw = "Line 1   \r\n\r\n\r\n\r\n\r\nLine 2 with spaces   \r\n    indented line\n"
    cleaned = clean_input_text(raw)
    assert "\r" not in cleaned
    assert "Line 1\n\nLine 2 with spaces\n    indented line" == cleaned


def test_extract_word_tokens():
    text = "Shortest Job First (SJF) is an algorithm in which the process..."
    tokens = extract_word_tokens(text)
    assert "shortest" in tokens
    assert "sjf" in tokens
    assert "algorithm" in tokens

