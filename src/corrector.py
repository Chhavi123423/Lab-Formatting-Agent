from typing import Tuple
from src.models import DocumentAST, FormattingPlan, ValidationResult, HeadingNode
from src.docx_generator import generate_docx_from_plan
from src.validator import validate_generated_docx
from src.formatting_planner import create_formatting_plan


def run_one_pass_correction(
    docx_bytes: bytes,
    validation_result: ValidationResult,
    ast: DocumentAST,
    plan: FormattingPlan
) -> Tuple[bytes, ValidationResult]:
    """
    Executes exactly one automatic correction pass if validation failed on formatting rules.
    Does NOT modify user academic content.
    Returns: (corrected_docx_bytes, final_validation_result)
    """
    if validation_result.status == "PASS":
        return docx_bytes, validation_result

    # Clone plan page config and typography
    fixed_plan = plan.model_copy(deep=True)
    corrected_any = False

    for issue in validation_result.issues:
        # 1. Correct Margins
        if issue.rule_name == "Margins":
            fixed_plan.page_config["margin_top_inches"] = 1.0
            fixed_plan.page_config["margin_bottom_inches"] = 1.0
            fixed_plan.page_config["margin_left_inches"] = 1.0
            fixed_plan.page_config["margin_right_inches"] = 1.0
            corrected_any = True

        # 2. Correct Heading Hierarchy
        if issue.rule_name == "Heading Hierarchy":
            # Fix skipped heading levels in AST
            prev_level = 1
            for node in ast.nodes:
                if isinstance(node, HeadingNode):
                    if node.level > prev_level + 1:
                        node.level = prev_level + 1
                    prev_level = node.level
            # Regenerate plan with adjusted heading levels
            fixed_plan = create_formatting_plan(ast)
            corrected_any = True

        # 3. Correct Code Styling
        if issue.rule_name in ["Code Styling", "Code Font"]:
            fixed_plan.typography["code"]["font"] = "Consolas"
            fixed_plan.typography["code"]["size_pt"] = 9.5
            fixed_plan.typography["code"]["bg_color_hex"] = "F4F4F4"
            for n in fixed_plan.nodes:
                if n.get("type") == "code_block":
                    n["style"]["font"] = "Consolas"
                    n["style"]["bg_color_hex"] = "F4F4F4"
            corrected_any = True

    if not corrected_any:
        # Issue cannot be automatically corrected by formatting engine
        validation_result.correction_attempted = True
        validation_result.correction_succeeded = False
        return docx_bytes, validation_result

    # Re-generate DOCX with corrected plan
    new_docx_bytes = generate_docx_from_plan(fixed_plan)

    # Re-validate DOCX
    new_validation = validate_generated_docx(new_docx_bytes, ast)
    new_validation.correction_attempted = True
    new_validation.correction_succeeded = (new_validation.status == "PASS")

    return new_docx_bytes, new_validation

