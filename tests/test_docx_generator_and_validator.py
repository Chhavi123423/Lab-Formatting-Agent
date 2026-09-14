import pytest
from src.preprocessor import clean_input_text
from src.heading_detector import extract_sections_heuristically
from src.content_detector import build_document_ast
from src.formatting_planner import create_formatting_plan
from src.docx_generator import generate_docx_from_plan
from src.validator import validate_generated_docx
from src.corrector import run_one_pass_correction
from src.models import HeadingNode


def test_full_pipeline_generation_and_validation():
    sample_text = (
        "TITLE:\n"
        "Implementation of SJF CPU Scheduling\n\n"
        "AIM:\n"
        "To write a C program implementing SJF scheduling.\n\n"
        "THEORY:\n"
        "Shortest Job First is a non-preemptive algorithm.\n\n"
        "IMPLEMENTATION:\n"
        "#include <stdio.h>\n"
        "int main() {\n"
        "    printf(\"SJF Execution\\n\");\n"
        "    return 0;\n"
        "}\n\n"
        "RESULT:\n"
        "SJF scheduling was successfully verified."
    )

    cleaned = clean_input_text(sample_text)
    sections = extract_sections_heuristically(cleaned)
    ast = build_document_ast(sections, student_name="Bob", roll_number="CS101", raw_input_text=cleaned)
    plan = create_formatting_plan(ast)
    docx_bytes = generate_docx_from_plan(plan)

    assert len(docx_bytes) > 1000  # valid docx file generated

    # Validate output
    val_res = validate_generated_docx(docx_bytes, ast)
    assert val_res.status == "PASS"
    assert len(val_res.issues) == 0


def test_correction_loop_on_heading_skip():
    # Construct an AST with a skipped heading level (H1 -> H3)
    ast = build_document_ast(
        sections=[
            {"heading": "EXPERIMENT 1", "level": 1, "content": "Intro"},
            {"heading": "DEEP DETAILS", "level": 3, "content": "Skipped H2"},
        ],
        student_name="Charlie",
        roll_number="CS102",
        raw_input_text="EXPERIMENT 1\nIntro\nDEEP DETAILS\nSkipped H2"
    )

    plan = create_formatting_plan(ast)
    docx_bytes = generate_docx_from_plan(plan)

    # First validation should detect the heading hierarchy issue
    val_res = validate_generated_docx(docx_bytes, ast)
    assert val_res.status == "FAIL"
    assert any(i.rule_name == "Heading Hierarchy" for i in val_res.issues)

    # Run one-pass correction
    corrected_docx, final_val = run_one_pass_correction(docx_bytes, val_res, ast, plan)
    assert final_val.correction_attempted is True
    assert final_val.status == "PASS"

