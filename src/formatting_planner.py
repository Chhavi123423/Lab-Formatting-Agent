from typing import Dict, Any, List
from src.models import (
    DocumentAST, FormattingPlan, HeadingNode, ParagraphNode, CodeBlockNode, ListNode, ImageNode, TableNode
)
from src.profiles.lab_profile import get_canonical_lab_profile

# Lazy import to avoid circular — only used when table nodes arrive
_TablePlaceholder = None
def _get_table_placeholder():
    global _TablePlaceholder
    if _TablePlaceholder is None:
        try:
            from src.preview_renderer import _TablePlaceholder as TP
            _TablePlaceholder = TP
        except ImportError:
            pass
    return _TablePlaceholder


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
        title_text = ast.title
        if typo.get("title", {}).get("uppercase", True):
            title_text = title_text.upper()
        planned_nodes.append({
            "type": "title",
            "text": title_text,
            "style": typo["title"]
        })

    idx = 0
    total_nodes = len(ast.nodes)
    while idx < total_nodes:
        node = ast.nodes[idx]
        if isinstance(node, HeadingNode):
            level_key = f"h{min(max(node.level, 1), 3)}"
            heading_text = node.text.strip()
            if typo.get(level_key, {}).get("uppercase", True):
                heading_text = heading_text.upper()

            is_inline = node.is_inline or (node.text.upper().strip() in inline_headings)
            inline_text = node.inline_text

            # If the profile defines this heading as inline, but inline_text is empty,
            # absorb the immediately following ParagraphNode onto the same line!
            if is_inline and not inline_text and (idx + 1 < total_nodes):
                next_node = ast.nodes[idx + 1]
                if isinstance(next_node, ParagraphNode):
                    inline_text = next_node.text
                    idx += 1  # Skip the absorbed paragraph node

            planned_nodes.append({
                "type": "heading",
                "text": heading_text,
                "level": node.level,
                "is_inline": is_inline,
                "inline_text": inline_text,
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
        elif isinstance(node, TableNode):
            planned_nodes.append({
                "type": "table",
                "headers": node.headers,
                "rows": node.rows,
                "caption": node.caption,
                "style": typo.get("body", {}),
            })
        else:
            # Handle TablePlaceholder nodes from the workspace builder
            TP = _get_table_placeholder()
            if TP is not None and isinstance(node, TP):
                planned_nodes.append({
                    "type": "table",
                    "headers": node.headers,
                    "rows": node.rows,
                    "caption": node.caption,
                    "style": typo.get("body", {}),
                })
        idx += 1

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
        enrollment_number=ast.enrollment_number,
        class_section=ast.class_section,
        nodes=planned_nodes
    )
