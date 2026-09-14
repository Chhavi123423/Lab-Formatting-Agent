import pytest
from src.content_detector import is_code_block, parse_list_items, build_document_ast
from src.models import HeadingNode, ParagraphNode, CodeBlockNode, ListNode


def test_is_code_block_c():
    c_code = (
        "#include <stdio.h>\n"
        "int main() {\n"
        "    int bt[5] = {1, 2, 3};\n"
        "    printf(\"Hello\");\n"
        "    return 0;\n"
        "}"
    )
    is_code, lang = is_code_block(c_code)
    assert is_code is True
    assert lang == "c"


def test_is_code_block_python():
    py_code = (
        "def sjf_schedule(processes):\n"
        "    sorted_proc = sorted(processes, key=lambda x: x[1])\n"
        "    return sorted_proc"
    )
    is_code, lang = is_code_block(py_code)
    assert is_code is True
    assert lang == "python"


def test_parse_list_items():
    ordered_text = "1. Start\n2. Sort processes\n3. Calculate waiting time\n4. Stop"
    is_list, is_ordered, items = parse_list_items(ordered_text)
    assert is_list is True
    assert is_ordered is True
    assert len(items) == 4
    assert items[0] == "Start"

    bullet_text = "- First item\n- Second item\n- Third item"
    is_list, is_ordered, items = parse_list_items(bullet_text)
    assert is_list is True
    assert is_ordered is False
    assert len(items) == 3


def test_build_document_ast():
    sections = [
        {"heading": "AIM", "level": 1, "content": "To implement SJF scheduling."},
        {"heading": "ALGORITHM", "level": 1, "content": "1. Initialize variables\n2. Sort\n3. Output"},
        {"heading": "CODE", "level": 1, "content": "#include <stdio.h>\nint main() { return 0; }"},
    ]
    ast = build_document_ast(sections, student_name="Alice", roll_number="123")
    assert ast.student_name == "Alice"
    assert ast.roll_number == "123"

    node_types = [n.node_type for n in ast.nodes]
    assert "heading" in node_types
    assert "paragraph" in node_types
    assert "list" in node_types
    assert "code_block" in node_types

