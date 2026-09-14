import pytest
from src.heading_detector import classify_heading_line, extract_sections_heuristically


def test_classify_heading_patterns():
    # 1. Uppercase with colon
    res = classify_heading_line("THEORY:")
    assert res is not None
    assert res[0] == "THEORY"
    assert res[1] == 1

    # 2. Markdown heading
    res = classify_heading_line("## Methodology")
    assert res is not None
    assert res[0] == "Methodology"
    assert res[1] == 2

    # 3. Markdown Bold heading (user's specific requirement)
    res = classify_heading_line("**Theory**")
    assert res is not None
    assert res[0] == "Theory"
    assert res[1] == 1

    res = classify_heading_line("**3. Algorithm:**")
    assert res is not None
    assert res[0] == "3. Algorithm"
    assert res[1] == 1

    # 4. Numbered heading
    res = classify_heading_line("1.1 Background Study")
    assert res is not None
    assert res[1] == 2


def test_extract_sections_heuristically():
    sample_text = (
        "**Aim**\n"
        "To implement SJF scheduling algorithm.\n\n"
        "**Theory**\n"
        "Shortest Job First selects the waiting process with smallest burst time.\n\n"
        "**Implementation**\n"
        "#include <stdio.h>\n"
        "int main() { return 0; }\n\n"
        "**Output**\n"
        "[screenshot]\n\n"
        "**Result**\n"
        "Completed successfully."
    )

    sections = extract_sections_heuristically(sample_text)
    assert len(sections) == 5
    headings = [s["heading"] for s in sections]
    assert headings == ["Aim", "Theory", "Implementation", "Output", "Result"]
    assert "SJF" in sections[0]["content"]
    assert "#include" in sections[2]["content"]

