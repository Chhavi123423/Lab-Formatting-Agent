"""
preview_renderer.py — Generates an HTML in-browser preview of the report
and also converts the session-state report into a DocumentAST for the
python-docx pipeline.

Content is never rewritten or supplemented.
"""
import html
from typing import Dict, Any, List, Optional
import base64

from src.models import (
    DocumentAST, HeadingNode, ParagraphNode, CodeBlockNode, ListNode, ImageNode, TableNode
)


def _esc(text: str) -> str:
    return html.escape(str(text))


def render_preview_html(report: Dict[str, Any]) -> str:
    """
    Build an HTML string that looks like a Word document page.
    Used for the in-app preview pane.
    """
    meta = report.get("meta", {})
    sections = report.get("sections", [])

    parts = ['<div class="preview-doc">']

    # Header metadata
    header_lines = []
    if meta.get("subject"):
        header_lines.append(f'<span style="float:left;font-weight:bold">{_esc(meta["subject"])}</span>')
    if meta.get("subject_code"):
        header_lines.append(f'<span style="float:right;font-weight:bold">{_esc(meta["subject_code"])}</span>')
    if header_lines:
        parts.append(f'<div style="overflow:auto;border-bottom:1px solid #999;padding-bottom:6px;margin-bottom:16px">{"".join(header_lines)}</div>')

    # Title
    title = meta.get("title") or meta.get("experiment_title") or ""
    if meta.get("experiment_no"):
        title = f"EXPERIMENT-{_esc(meta['experiment_no'])}  {_esc(title)}"
    else:
        title = _esc(title)
    if title.strip():
        parts.append(f'<h1>{title.strip()}</h1>')

    # Student stamp
    stamp_parts = []
    if meta.get("student_name"):    stamp_parts.append(f"Name: {_esc(meta['student_name'])}")
    if meta.get("class_section"):   stamp_parts.append(f"Class: {_esc(meta['class_section'])}")
    if meta.get("roll_number"):     stamp_parts.append(f"Roll No: {_esc(meta['roll_number'])}")
    if meta.get("faculty_name"):    stamp_parts.append(f"Faculty: {_esc(meta['faculty_name'])}")
    if meta.get("submission_date"): stamp_parts.append(f"Date: {_esc(meta['submission_date'])}")
    if stamp_parts:
        parts.append(f'<p style="text-align:right;font-size:10pt;color:#555;">{" &nbsp;|&nbsp; ".join(stamp_parts)}</p>')
        parts.append('<hr style="margin:10px 0 20px;"/>')

    # Sections
    for sec in sections:
        name = _esc(sec.get("name", ""))
        blocks = sec.get("blocks", [])
        if not name and not blocks:
            continue
        parts.append(f'<h2>{name}</h2>')
        for blk in blocks:
            btype = blk.get("type", "")
            if btype == "text":
                content = blk.get("content", "")
                if content.strip():
                    # Split on double newlines → paragraphs
                    for para in content.split("\n\n"):
                        if para.strip():
                            # Single-newline → line break inside paragraph
                            lines = [_esc(l) for l in para.split("\n")]
                            parts.append(f'<p>{"<br>".join(lines)}</p>')
            elif btype == "code":
                content = blk.get("content", "")
                lang = blk.get("language", "")
                lang_badge = f'<span style="font-size:9pt;color:#999;float:right">{_esc(lang)}</span>' if lang and lang != "text" else ""
                parts.append(
                    f'<div class="preview-code">{lang_badge}'
                    f'<div style="clear:both"/>{_esc(content)}</div>'
                )
            elif btype == "table":
                headers = blk.get("headers", [])
                rows = blk.get("rows", [])
                caption = blk.get("caption", "")
                parts.append('<table>')
                if headers:
                    parts.append('<tr>' + ''.join(f'<th>{_esc(h)}</th>' for h in headers) + '</tr>')
                for row in rows:
                    parts.append('<tr>' + ''.join(f'<td>{_esc(c)}</td>' for c in row) + '</tr>')
                parts.append('</table>')
                if caption:
                    parts.append(f'<p class="preview-caption">{_esc(caption)}</p>')
            elif btype == "image":
                img_bytes = blk.get("bytes")
                caption = blk.get("caption", "")
                if img_bytes:
                    b64 = base64.b64encode(img_bytes).decode()
                    parts.append(
                        f'<div style="text-align:center;margin:12px 0">'
                        f'<img src="data:image/png;base64,{b64}" '
                        f'style="max-width:100%;max-height:400px;border:1px solid #DDD;border-radius:4px" />'
                        f'</div>'
                    )
                    if caption:
                        parts.append(f'<p class="preview-caption">{_esc(caption)}</p>')

    parts.append('</div>')
    return "\n".join(parts)


def report_to_ast(report: Dict[str, Any]) -> DocumentAST:
    """
    Convert the session-state report dict into a DocumentAST
    suitable for the existing formatting pipeline (generate_docx_from_plan).
    Tables are passed as TableNode-like paragraph placeholders for now;
    the extended docx_generator handles them via the 'table' node type.
    """
    meta = report.get("meta", {})
    sections = report.get("sections", [])
    ast_nodes = []

    doc_title = meta.get("title") or meta.get("experiment_title") or ""
    if meta.get("experiment_no") and not doc_title.startswith("EXPERIMENT"):
        doc_title = f"EXPERIMENT-{meta['experiment_no']} {doc_title}".strip()

    for sec in sections:
        name = sec.get("name", "").strip()
        blocks = sec.get("blocks", [])
        if not name and not blocks:
            continue

        ast_nodes.append(HeadingNode(text=name, level=1, raw_text=name))

        for blk in blocks:
            btype = blk.get("type", "")
            if btype == "text":
                content = blk.get("content", "").strip()
                if content:
                    # Split on double-newline into separate paragraph nodes
                    for para in content.split("\n\n"):
                        para = para.strip()
                        if para:
                            ast_nodes.append(ParagraphNode(text=para))
            elif btype == "code":
                content = blk.get("content", "").strip()
                lang = blk.get("language", "text")
                if content:
                    ast_nodes.append(CodeBlockNode(code=content, language=lang))
            elif btype == "table":
                ast_nodes.append(TableNode(
                    headers=blk.get("headers", []),
                    rows=blk.get("rows", []),
                    caption=blk.get("caption", ""),
                ))
            elif btype == "image":
                img_bytes = blk.get("bytes")
                caption = blk.get("caption", "Figure: Output")
                if img_bytes:
                    ast_nodes.append(ImageNode(
                        image_bytes=img_bytes,
                        caption=caption,
                        mode="embed",
                    ))

    raw_text = _extract_raw_text(report)

    return DocumentAST(
        title=doc_title,
        subject_name=meta.get("subject", ""),
        subject_code=meta.get("subject_code", ""),
        student_name=meta.get("student_name", ""),
        roll_number=meta.get("roll_number", ""),
        class_section=meta.get("class_section", ""),
        nodes=ast_nodes,
        raw_input_text=raw_text,
    )


class _TablePlaceholder:
    """Lightweight shim so docx_generator can detect table blocks from AST."""
    node_type = "table"
    def __init__(self, headers, rows, caption):
        self.headers = headers
        self.rows = rows
        self.caption = caption


def _extract_raw_text(report: Dict[str, Any]) -> str:
    parts = []
    for sec in report.get("sections", []):
        parts.append(sec.get("name", ""))
        for blk in sec.get("blocks", []):
            if blk.get("type") in ("text", "code"):
                parts.append(blk.get("content", ""))
    return "\n".join(parts)

