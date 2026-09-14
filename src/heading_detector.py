import re
import os
from typing import List, Dict, Any, Tuple, Optional
from src.config import CANONICAL_LAB_SECTIONS, GEMINI_API_KEY


# Regex patterns for heading detection
RE_MD_HEADING = re.compile(r"^(#{1,6})\s+(.+)$")
RE_BOLD_HEADING = re.compile(r"^(\*\*|__)([\w\s\.\-:]+)\1:?$")
RE_COLON_HEADING = re.compile(r"^([A-Za-z0-9\s\.\-_/]+):$")
RE_NUMBERED_HEADING = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+([A-Za-z\s\.\-_/]+):?$")
RE_EXPERIMENT_TITLE = re.compile(r"^(EXPERIMENT|LAB|PRACTICAL)[\s\-:]*(\d+.*)?$", re.IGNORECASE)

# Inline heading pattern: e.g. "AIM: Write a C++ program..." or "THEORY: A grammar..." or "**AIM:** ..."
RE_INLINE_HEADING = re.compile(r"^(\*{0,2})([A-Za-z0-9\s\.\-_/]+)\1\s*:\s*(.+)$")

# Standard known keywords in uppercase for quick matching
KNOWN_KEYWORDS = {kw.upper() for kw in CANONICAL_LAB_SECTIONS} | {
    "INTRODUCTION", "BACKGROUND", "METHODOLOGY", "SYSTEM ARCHITECTURE",
    "DESIGN", "MODULE DESIGN", "RESULTS", "DISCUSSION", "EXPERIMENT",
    "PROCEDURE", "VIVA QUESTIONS", "REFERENCES"
}


def classify_heading_line(line: str) -> Optional[Tuple[str, int, float, str]]:
    """
    Checks if a single line is a heading (either standalone or inline).
    Returns: (cleaned_heading_text, heading_level, confidence_score, inline_content) or None.
    Level: 1 for H1, 2 for H2, 3 for H3.
    inline_content: Non-empty if heading and content share the same line (e.g., AIM: Write a C++ program...).
    """
    stripped = line.strip()
    if not stripped:
        return None

    # 1. Experiment Title (e.g., "EXPERIMENT-3", "EXPERIMENT 1")
    exp_match = RE_EXPERIMENT_TITLE.match(stripped)
    if exp_match:
        return stripped, 1, 1.0, ""

    # 2. Markdown heading (# H1, ## H2, ### H3)
    md_match = RE_MD_HEADING.match(stripped)
    if md_match:
        hashes, title = md_match.groups()
        level = min(len(hashes), 3)
        return title.strip().rstrip(":"), level, 1.0, ""

    # 3. Markdown Bold Heading (**Theory**, **3. Algorithm:**, etc.)
    bold_match = RE_BOLD_HEADING.match(stripped)
    if bold_match:
        _, inner = bold_match.groups()
        clean_inner = inner.strip().rstrip(":")
        num_match = RE_NUMBERED_HEADING.match(clean_inner)
        if num_match:
            num_str = num_match.group(1)
            level = min(num_str.count(".") + 1, 3)
            return clean_inner, level, 0.95, ""
        return clean_inner, 1, 0.95, ""

    # 4. Numbered headings (e.g., "1. Introduction", "2.1 Frontend Architecture")
    num_match = RE_NUMBERED_HEADING.match(stripped)
    if num_match and len(stripped) < 100:
        num_str, title = num_match.groups()
        level = min(num_str.count(".") + 1, 3)
        return stripped.rstrip(":"), level, 0.90, ""

    # 5. Uppercase or Title line ending with colon (e.g., "THEORY:", "CODE:", "OUTPUT:")
    colon_match = RE_COLON_HEADING.match(stripped)
    if colon_match:
        cand = colon_match.group(1).strip()
        cand_upper = cand.upper()
        if cand_upper in KNOWN_KEYWORDS:
            return cand, 1, 1.0, ""
        if cand.isupper() and len(cand) < 50:
            return cand, 1, 0.85, ""
        if cand.istitle() and len(cand.split()) <= 5:
            return cand, 1, 0.80, ""

    # 6. Inline Heading with content on the same line (e.g. "AIM: Write a C++ program...", "THEORY: A grammar...")
    inline_match = RE_INLINE_HEADING.match(stripped)
    if inline_match:
        _, cand, content = inline_match.groups()
        cand_clean = cand.strip().strip("*_").strip()
        cand_upper = cand_clean.upper()
        if cand_upper in KNOWN_KEYWORDS:
            return cand_clean, 1, 1.0, content.strip()

    # 7. Exact match to known keyword standalone line without colon (e.g., "Theory", "AIM", "ALGORITHM")
    stripped_upper = stripped.upper()
    if stripped_upper in KNOWN_KEYWORDS and len(stripped.split()) <= 3:
        return stripped, 1, 0.90, ""

    return None


def extract_sections_heuristically(text: str) -> List[Dict[str, Any]]:
    """
    Extracts ordered sections and their raw text content using heuristic rules.
    Preserves inline headings vs block headings.
    """
    lines = text.split("\n")
    sections: List[Dict[str, Any]] = []

    current_section: Optional[Dict[str, Any]] = None
    accumulated_lines: List[str] = []

    for idx, line in enumerate(lines):
        heading_info = classify_heading_line(line)

        is_isolated = True
        if heading_info:
            title, level, confidence, inline_content = heading_info
            # Check context if confidence < 0.9
            if confidence < 0.90:
                has_prev = idx > 0 and lines[idx - 1].strip() != ""
                has_next = idx < len(lines) - 1 and lines[idx + 1].strip() != ""
                if has_prev and has_next:
                    is_isolated = False

        if heading_info and is_isolated:
            title, level, confidence, inline_content = heading_info

            # Finalize previous section
            if current_section is not None:
                current_section["content"] = "\n".join(accumulated_lines).strip()
                sections.append(current_section)
                accumulated_lines = []

            is_inline = bool(inline_content)
            if inline_content:
                accumulated_lines.append(inline_content)

            current_section = {
                "heading": title,
                "level": level,
                "confidence": confidence,
                "is_inline": is_inline,
                "content": "",
            }
        else:
            accumulated_lines.append(line)

    # Append the last section or unsectioned text
    if current_section is not None:
        current_section["content"] = "\n".join(accumulated_lines).strip()
        sections.append(current_section)
    elif accumulated_lines and "\n".join(accumulated_lines).strip():
        sections.append({
            "heading": "LAB WORK",
            "level": 1,
            "confidence": 0.5,
            "is_inline": False,
            "content": "\n".join(accumulated_lines).strip(),
        })

    return sections


def extract_sections_with_llm_fallback(text: str) -> List[Dict[str, Any]]:
    """
    Runs heuristic extraction with LLM fallback for ambiguous text.
    """
    heuristic_sections = extract_sections_heuristically(text)
    if not heuristic_sections:
        return heuristic_sections

    avg_confidence = sum(s.get("confidence", 1.0) for s in heuristic_sections) / len(heuristic_sections)
    if avg_confidence >= 0.8 or not GEMINI_API_KEY:
        return heuristic_sections

    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = (
            "Analyze this lab document text and output a JSON list of sections with their title and level (1 for main heading, 2 for subheading).\n"
            "Format: [{\"heading\": \"TITLE\", \"level\": 1, \"content\": \"...\"}]\n"
            "DO NOT change any words of the content. Strictly preserve user words.\n\n"
            f"TEXT:\n{text[:4000]}"
        )
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )
        if response.text:
            import json
            clean_resp = re.sub(r"^```(?:json)?\n|\n```$", "", response.text.strip())
            data = json.loads(clean_resp)
            if isinstance(data, list) and len(data) > 0 and "heading" in data[0]:
                for item in data:
                    item["confidence"] = 1.0
                return data
    except Exception:
        pass

    return heuristic_sections
