from typing import Dict, Any, List
from src.models import (
    DocumentAST, FormattingPlan, HeadingNode, ParagraphNode, CodeBlockNode, ListNode, ImageNode
)
from src.profiles.lab_profile import get_canonical_lab_profile


def create_formatting_plan(ast: DocumentAST, custom_profile: Dict[str, Any] = None) -> FormattingPlan:
    """
    Transforms the Document AST into an explicit, deterministic FormattingPlan.
    The generator simply executes this plan without making styling decisions.
    """
    profile = custom_profile or get_canonical_lab_profile()
    typo = profile["typography"]
    page = profile["page"]
    profile_name = profile.get("profile_name", "CANONICAL_LAB_PROFILE_V1")
    inline_headings = [h.upper() for h in profile.get("inline_headings", [])]

    planned_nodes: List[Dict[str, Any]] = []

    # If document has a title, insert a Title element at the beginning
    if ast.title:
        planned_nodes.append({
            "type": "title",
            "text": ast.title,
            "style": typo["title"]
        })

    for node in ast.nodes:
        if isinstance(node, HeadingNode):
            level_key = f"h{min(max(node.level, 1), 3)}"
            is_inline = node.is_inline or (node.text.upper() in inline_headings)
            planned_nodes.append({
                "type": "heading",
                "text": node.text,
                "level": node.level,
                "is_inline": is_inline,
                "inline_text": node.inline_text,
                "style": typo[level_key],
                "body_style": typo["body"],
            })
        elif isinstance(node, ParagraphNode):
            planned_nodes.append({
                "type": "paragraph",
                "text": node.text,
                "style": typo["body"]
            })
        elif isinstance(node, CodeBlockNode):
            planned_nodes.append({
                "type": "code_block",
                "code": node.code,
                "language": node.language,
                "style": typo["code"]
            })
        elif isinstance(node, ListNode):
            planned_nodes.append({
                "type": "list",
                "items": node.items,
                "is_ordered": node.is_ordered,
                "style": typo["body"]
            })
        elif isinstance(node, ImageNode):
            planned_nodes.append({
                "type": "image",
                "image_bytes": node.image_bytes,
                "caption": node.caption,
                "mode": node.mode,
                "style": typo["image"]
            })

    return FormattingPlan(
        profile_name=profile_name,
        page_config=page,
        typography=typo,
        header_config=typo.get("header", {}),
        footer_config=typo.get("footer", {}),
        subject_name=ast.subject_name,
        subject_code=ast.subject_code,
        student_name=ast.student_name,
        roll_number=ast.roll_number,
        class_section=ast.class_section,
        nodes=planned_nodes
    )
