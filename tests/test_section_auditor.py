from src.models import DocumentAST, HeadingNode, ParagraphNode
from src.section_auditor import audit_missing_sections


def test_audit_missing_sections():
    # Only Aim and Theory provided; Missing Code, Output, and Result
    ast = DocumentAST(
        nodes=[
            HeadingNode(text="AIM", level=1),
            ParagraphNode(text="To study SJF algorithm."),
            HeadingNode(text="THEORY", level=1),
            ParagraphNode(text="Theoretical notes."),
        ]
    )

    warnings = audit_missing_sections(ast)
    assert len(warnings) > 0
    # Check that warnings mention missing sections
    joined = " ".join(warnings)
    assert "IMPLEMENTATION / CODE" in joined
    assert "OUTPUT" in joined
    assert "RESULT / CONCLUSION" in joined

    # Verify that the auditor did NOT alter the nodes (no fabrication)
    assert len(ast.nodes) == 4

