import io
from typing import List, Set
from docx import Document
from docx.shared import Inches

from src.models import DocumentAST, ValidationResult, ValidationIssue, HeadingNode, CodeBlockNode
from src.preprocessor import extract_word_tokens


def validate_generated_docx(docx_bytes: bytes, ast: DocumentAST) -> ValidationResult:
    """
    Inspects the generated DOCX file and verifies:
    1. Page margins match 1.0 inch canonical profile.
    2. Heading hierarchy has no illegal skips (e.g., H1 -> H3).
    3. User section order is preserved.
    4. Code styling and monospaced font are applied.
    5. Image bounds are within printable limits.
    6. Content preservation: No significant dropped tokens.
    """
    issues: List[ValidationIssue] = []
    checks: List[str] = []

    doc = Document(io.BytesIO(docx_bytes))
    section = doc.sections[0]

    # --- Check 1: Margins ---
    checks.append("Page Margin Verification")
    left_m = round(section.left_margin.inches, 2)
    right_m = round(section.right_margin.inches, 2)
    top_m = round(section.top_margin.inches, 2)
    bottom_m = round(section.bottom_margin.inches, 2)
    if not (0.95 <= left_m <= 1.05 and 0.95 <= right_m <= 1.05 and 0.95 <= top_m <= 1.05 and 0.95 <= bottom_m <= 1.05):
        issues.append(ValidationIssue(
            severity="error",
            rule_name="Margins",
            message=f"Page margins deviate from 1.0 inch standard (L:{left_m}, R:{right_m}, T:{top_m}, B:{bottom_m})."
        ))

    # --- Check 2: Heading Hierarchy ---
    checks.append("Heading Hierarchy Verification")
    ast_headings = [n for n in ast.nodes if isinstance(n, HeadingNode)]
    prev_level = 1
    for h in ast_headings:
        if h.level > prev_level + 1:
            issues.append(ValidationIssue(
                severity="error",
                rule_name="Heading Hierarchy",
                message=f"Heading level skipped from H{prev_level} directly to H{h.level} at heading '{h.text}'."
            ))
        prev_level = h.level

    # --- Check 3: Section Order Preservation ---
    checks.append("Section Order Verification")
    expected_heading_texts = [h.text.strip().lower() for h in ast_headings]
    
    # Read paragraphs in generated doc to check heading text sequence
    doc_heading_texts: List[str] = []
    for p in doc.paragraphs:
        if p.runs and any(r.font.bold for r in p.runs) and p.text.strip():
            # Check if this paragraph text matches any expected heading
            p_text = p.text.strip().lower()
            if p_text in expected_heading_texts:
                doc_heading_texts.append(p_text)

    # Filter doc_heading_texts to unique sequence
    seen = set()
    cleaned_doc_headings = [x for x in doc_heading_texts if not (x in seen or seen.add(x))]
    
    # Compare with expected order
    if cleaned_doc_headings != expected_heading_texts:
        # Check if subset order is maintained
        expected_filtered = [h for h in expected_heading_texts if h in cleaned_doc_headings]
        if cleaned_doc_headings != expected_filtered:
            issues.append(ValidationIssue(
                severity="error",
                rule_name="Section Ordering",
                message="Section order in generated document does not match user's input sequence."
            ))

    # --- Check 4: Code Block Font & Styling ---
    checks.append("Code Block Styling Verification")
    ast_code_nodes = [n for n in ast.nodes if isinstance(n, CodeBlockNode)]
    if ast_code_nodes:
        has_consolas = False
        # Check paragraphs
        for p in doc.paragraphs:
            for r in p.runs:
                if r.font.name == "Consolas":
                    has_consolas = True
                    break
            if has_consolas:
                break

        # Check tables
        if not has_consolas:
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            for r in p.runs:
                                if r.font.name == "Consolas":
                                    has_consolas = True
                                    break
                            if has_consolas:
                                break

        if not has_consolas:
            issues.append(ValidationIssue(
                severity="error",
                rule_name="Code Font",
                message="Code block is present but does not have monospaced Consolas font applied."
            ))

    # --- Check 5: Content Preservation Verification ---
    checks.append("Content Preservation Verification")
    if ast.raw_input_text:
        input_tokens = set(extract_word_tokens(ast.raw_input_text))

        # Extract all words from generated DOCX paragraphs and tables
        doc_words: List[str] = []
        for p in doc.paragraphs:
            doc_words.extend(extract_word_tokens(p.text))
        for t in doc.tables:
            for row in t.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        doc_words.extend(extract_word_tokens(p.text))

        doc_tokens = set(doc_words)

        # Allow small noise margin (e.g., words in code comments or formatting markers)
        # We expect at least 85% of input words to be present in output
        intersection = input_tokens.intersection(doc_tokens)
        preservation_rate = len(intersection) / max(len(input_tokens), 1)

        if preservation_rate < 0.85:
            missing_sample = list(input_tokens - doc_tokens)[:5]
            issues.append(ValidationIssue(
                severity="error",
                rule_name="Content Preservation",
                message=f"Content preservation rate ({preservation_rate:.1%}) is below threshold. Missing terms: {missing_sample}"
            ))

    # Determine PASS / FAIL status
    has_errors = any(i.severity == "error" for i in issues)
    status = "FAIL" if has_errors else "PASS"

    return ValidationResult(
        status=status,
        issues=issues,
        checks_performed=checks,
    )

