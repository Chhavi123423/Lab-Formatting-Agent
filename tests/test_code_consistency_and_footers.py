import io
from docx import Document
from src.preprocessor import clean_input_text
from src.heading_detector import extract_sections_heuristically
from src.content_detector import build_document_ast
from src.profiles import get_university_practical_profile
from src.formatting_planner import create_formatting_plan
from src.docx_generator import generate_docx_from_plan


def test_code_font_consistency_with_blank_lines():
    # Code with blank lines between functions and loops
    raw_text = (
        "EXPERIMENT-1\n\n"
        "AIM: Test code font consistency\n\n"
        "CODE:\n"
        "#include <iostream>\n\n"
        "int main() {\n"
        "    int a = 10;\n\n"
        "    if (a > 5) {\n"
        "        cout << \"Greater\";\n"
        "    }\n\n"
        "    return 0;\n"
        "}\n\n"
        "OUTPUT:\n"
        "Greater"
    )

    cleaned = clean_input_text(raw_text)
    sections = extract_sections_heuristically(cleaned)
    ast = build_document_ast(sections, raw_input_text=cleaned)

    profile = get_university_practical_profile()
    plan = create_formatting_plan(ast, custom_profile=profile)
    docx_bytes = generate_docx_from_plan(plan)

    doc = Document(io.BytesIO(docx_bytes))

    # Collect all paragraphs that are part of the code
    # Verify that lines containing "int main", "if (a > 5)", "return 0" ALL have Consolas font
    code_runs = []
    for p in doc.paragraphs:
        if any(keyword in p.text for keyword in ["#include", "int main", "int a = 10", "return 0"]):
            for r in p.runs:
                code_runs.append((p.text, r.font.name))

    assert len(code_runs) > 0
    for text_sample, font_name in code_runs:
        assert font_name == "Consolas", f"Font for '{text_sample}' was '{font_name}', expected 'Consolas'!"


def test_flexible_footer_options():
    raw_text = "EXPERIMENT-1\n\nAIM: Testing footers\n\nRESULT: Done"
    cleaned = clean_input_text(raw_text)
    sections = extract_sections_heuristically(cleaned)
    ast = build_document_ast(sections, student_name="Test Student", roll_number="99")

    # 1. Test Page Number footer
    prof_pg = get_university_practical_profile()
    prof_pg["typography"]["footer"]["layout"] = "PAGE_NUMBER"
    plan_pg = create_formatting_plan(ast, custom_profile=prof_pg)
    docx_pg = generate_docx_from_plan(plan_pg)
    doc_pg = Document(io.BytesIO(docx_pg))
    footer_text = " ".join(p.text for p in doc_pg.sections[0].footer.paragraphs)
    assert "Page" in footer_text

    # 2. Test Custom Text footer
    prof_custom = get_university_practical_profile()
    prof_custom["typography"]["footer"]["layout"] = "CUSTOM_TEXT"
    prof_custom["typography"]["footer"]["text"] = "Department of IT — 2026"
    plan_custom = create_formatting_plan(ast, custom_profile=prof_custom)
    docx_custom = generate_docx_from_plan(plan_custom)
    doc_custom = Document(io.BytesIO(docx_custom))
    footer_custom_text = " ".join(p.text for p in doc_custom.sections[0].footer.paragraphs)
    assert "Department of IT — 2026" in footer_custom_text
