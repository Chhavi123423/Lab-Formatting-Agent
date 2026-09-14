import io
from docx import Document
from src.preprocessor import clean_input_text
from src.heading_detector import extract_sections_heuristically
from src.content_detector import build_document_ast
from src.profiles import get_university_practical_profile
from src.formatting_planner import create_formatting_plan
from src.docx_generator import generate_docx_from_plan
from src.validator import validate_generated_docx


def test_lowercase_input_formats_to_uppercase_and_inline():
    # User provides lowercase headings and separate lines for heading and content
    raw_lowercase_text = (
        "experiment-3\n\n"
        "aim:\n"
        "write a C++ program to check whether a given string is grammar or not.\n\n"
        "theory:\n"
        "a grammar in formal language theory is a set of production rules.\n\n"
        "code:\n"
        "#include <iostream>\n"
        "int main() { return 0; }\n\n"
        "output:\n"
        "Enter a string: aaabbb\n\n"
        "result:\n"
        "verified successfully."
    )

    cleaned = clean_input_text(raw_lowercase_text)
    sections = extract_sections_heuristically(cleaned)
    
    ast = build_document_ast(
        raw_sections=sections,
        subject_name="CD PRACTICAL FILE",
        subject_code="CIC-351",
        student_name="Chhavi Choudhary",
        roll_number="19",
        class_section="IT-2",
        raw_input_text=cleaned
    )

    profile = get_university_practical_profile()
    plan = create_formatting_plan(ast, custom_profile=profile)
    docx_bytes = generate_docx_from_plan(plan)

    doc = Document(io.BytesIO(docx_bytes))
    body_texts = [p.text for p in doc.paragraphs]

    # 1. Verify title is uppercase EXPERIMENT-3
    assert any("EXPERIMENT-3" in t for t in body_texts)

    # 2. Verify AIM is uppercase "AIM:" and formatted INLINE with its content
    aim_p = next((t for t in body_texts if "AIM:" in t), None)
    assert aim_p is not None, "AIM: heading not found"
    assert "write a C++ program" in aim_p, "AIM content should be inline on the same paragraph"
    assert not any(t.strip() == "aim:" or t.strip() == "aim: " for t in body_texts)

    # 3. Verify THEORY is uppercase "THEORY:" and formatted INLINE with its content
    theory_p = next((t for t in body_texts if "THEORY:" in t), None)
    assert theory_p is not None, "THEORY: heading not found"
    assert "a grammar in formal language" in theory_p, "THEORY content should be inline on the same paragraph"

    # 4. Verify CODE is uppercase "CODE:"
    assert any("CODE:" in t for t in body_texts)

    # 5. Verify RESULT is uppercase "RESULT:"
    assert any("RESULT:" in t for t in body_texts)

    # Validation should pass
    val_res = validate_generated_docx(docx_bytes, ast)
    assert val_res.status == "PASS"
