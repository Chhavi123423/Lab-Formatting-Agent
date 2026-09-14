import re
from typing import List


def clean_input_text(raw_text: str) -> str:
    """
    Cleans and normalizes user input text without altering the semantic content.
    - Normalizes carriage returns (\r\n -> \n, \r -> \n)
    - Strips trailing whitespace from each line while strictly preserving indentation
    - Collapses 3 or more consecutive newlines into 2
    - Strips leading and trailing blank lines from the overall document
    """
    if not raw_text:
        return ""

    # Normalize line endings
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")

    # Clean each line's trailing whitespace, but preserve leading indentation (crucial for code)
    lines = [line.rstrip() for line in text.split("\n")]

    reconstructed = "\n".join(lines)

    # Collapse 3 or more newlines down to 2
    reconstructed = re.sub(r"\n{3,}", "\n\n", reconstructed)

    return reconstructed.strip()


def extract_word_tokens(text: str) -> List[str]:
    """
    Extracts all alphanumeric words in lowercase for content preservation validation.
    Ignores punctuation and casing differences.
    """
    return re.findall(r"\b\w+\b", text.lower())

