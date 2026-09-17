import re
from typing import List, Optional, Tuple
from src.models import (
    ASTNode, HeadingNode, ParagraphNode, CodeBlockNode, ListNode, ImageNode, DocumentAST
)

# Common programming syntax cues
RE_CODE_MARKERS = [
    re.compile(r"^\s*#include\s*<", re.MULTILINE),
    re.compile(r"^\s*(int|void|float|char|double)\s+main\s*\(", re.MULTILINE),
    re.compile(r"^\s*def\s+[a-zA-Z_]\w*\s*\(", re.MULTILINE),
    re.compile(r"^\s*class\s+[a-zA-Z_]\w*\s*[:\{]", re.MULTILINE),
    re.compile(r"^\s*public\s+static\s+void\s+main", re.MULTILINE),
    re.compile(r"^\s*import\s+[a-zA-Z0-9_\.]+", re.MULTILINE),
    re.compile(r"^\s*from\s+[a-zA-Z0-9_\.]+\s+import", re.MULTILINE),
    re.compile(r"^\s*SELECT\s+.+\s+FROM\s+", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*CREATE\s+TABLE\s+", re.MULTILINE | re.IGNORECASE),
]

RE_ORDERED_LIST = re.compile(r"^\s*(\d+[\.\)]|[a-zA-Z][\.\)])\s+(.+)$")
RE_BULLET_LIST = re.compile(r"^\s*([-\*•])\s+(.+)$")
RE_IMAGE_PLACEHOLDER = re.compile(r"^\[(?:screenshot|output\s*(?:image|screenshot)?|image)\]$", re.IGNORECASE)


def detect_programming_language(code: str) -> str:
    """Heuristic guessing of programming language for display/styling."""
    if "#include" in code or "printf(" in code or "scanf(" in code:
        return "c"
    if "public class" in code or "System.out.println" in code:
        return "java"
    if "def " in code or "import " in code or "print(" in code:
        return "python"
    if "SELECT " in code.upper() or "INSERT INTO" in code.upper():
        return "sql"
    if "<html>" in code.lower() or "<div>" in code.lower():
        return "html"
    return "text"


def is_code_block(text: str) -> Tuple[bool, str]:
    """
    Determines whether a block of text is code.
    Returns: (is_code, detected_language)
    """
    stripped = text.strip()
    if not stripped:
        return False, "text"

    # Check explicit markdown code fences
    if stripped.startswith("```") and stripped.endswith("```"):
        first_line = stripped.split("\n")[0].replace("```", "").strip()
        lang = first_line if first_line else "text"
        return True, lang

    # Check for strong regex syntax markers
    for pattern in RE_CODE_MARKERS:
        if pattern.search(stripped):
            return True, detect_programming_language(stripped)

    # Heuristic: count semicolons, braces, and line indentation
    lines = [l for l in stripped.split("\n") if l.strip()]
    if len(lines) >= 3:
        semicolons = sum(1 for l in lines if l.strip().endswith(";"))
        braces = sum(1 for l in lines if "{" in l or "}" in l)
        indented = sum(1 for l in lines if l.startswith("    ") or l.startswith("\t"))
        
        ratio_semi = semicolons / len(lines)
        ratio_braces = braces / len(lines)
        ratio_indent = indented / len(lines)

        if (ratio_semi > 0.35 and ratio_braces > 0.15) or (ratio_indent > 0.5 and ratio_semi > 0.2):
            return True, detect_programming_language(stripped)

    return False, "text"


def parse_list_items(text: str) -> Tuple[bool, bool, List[str]]:
    """
    Checks if lines form a bullet or numbered list.
    Returns: (is_list, is_ordered, items)
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if len(lines) < 2:
        return False, False, []

    ordered_matches = [RE_ORDERED_LIST.match(l) for l in lines]
    bullet_matches = [RE_BULLET_LIST.match(l) for l in lines]

    if all(m is not None for m in ordered_matches):
        items = [m.group(2).strip() for m in ordered_matches]
        return True, True, items

    if all(m is not None for m in bullet_matches):
        items = [m.group(2).strip() for m in bullet_matches]
        return True, False, items

    return False, False, []


def parse_section_content_to_nodes(
    heading_text: str,
    heading_level: int,
    raw_content: str,
    uploaded_image_bytes: Optional[bytes] = None,
    image_mode: str = "embed",
    is_inline: bool = False
) -> List[ASTNode]:
    """
    Converts a single section and its raw text into typed AST nodes.
    Supports inline headings (e.g., AIM: Write a C++ program...)
    """
    nodes: List[ASTNode] = []

    # Split section content into chunks separated by blank lines
    chunks = [c.strip() for c in re.split(r"\n\s*\n", raw_content.strip()) if c.strip()] if raw_content.strip() else []

    first_inline_chunk = ""
    remaining_chunks = chunks

    if is_inline and chunks:
        # The first chunk sits inline with the heading
        first_inline_chunk = chunks[0]
        remaining_chunks = chunks[1:]

    # Add heading node
    nodes.append(HeadingNode(
        text=heading_text,
        level=heading_level,
        raw_text=heading_text,
        is_inline=is_inline,
        inline_text=first_inline_chunk
    ))

    # If the section is a dedicated code section, preserve the ENTIRE content as one contiguous CodeBlockNode
    # This prevents blank lines inside code from fragmenting code into paragraphs with changing fonts!
    if heading_text.upper().strip() in ["CODE", "IMPLEMENTATION", "SOURCE CODE", "PROGRAM", "C++ CODE", "JAVA CODE", "PYTHON CODE"]:
        clean_code = raw_content.strip()
        if clean_code:
            if clean_code.startswith("```") and clean_code.endswith("```"):
                c_lines = clean_code.split("\n")
                lang = c_lines[0].replace("```", "").strip() or "text"
                clean_code = "\n".join(c_lines[1:-1])
            else:
                lang = detect_programming_language(clean_code)
            nodes.append(CodeBlockNode(code=clean_code, language=lang))
        return nodes

    if not remaining_chunks and not (heading_text.upper() in ["OUTPUT", "SCREENSHOT"] and uploaded_image_bytes):
        return nodes

    for chunk_clean in remaining_chunks:
        # 1. Image placeholder check
        if RE_IMAGE_PLACEHOLDER.match(chunk_clean):
            if uploaded_image_bytes:
                nodes.append(ImageNode(
                    image_bytes=uploaded_image_bytes,
                    caption="Figure: Program Output Execution",
                    mode=image_mode
                ))
            continue

        # 2. Markdown code fence check
        if chunk_clean.startswith("```") and chunk_clean.endswith("```"):
            lines = chunk_clean.split("\n")
            lang = lines[0].replace("```", "").strip() or "text"
            inner_code = "\n".join(lines[1:-1])
            nodes.append(CodeBlockNode(code=inner_code, language=lang))
            continue

        # 3. Check for Code Block
        is_code, lang = is_code_block(chunk_clean)
        if not is_code and heading_text.upper() in ["CODE", "IMPLEMENTATION", "SOURCE CODE", "PROGRAM"]:
            if len(chunk_clean.split("\n")) > 2:
                is_code = True
                lang = detect_programming_language(chunk_clean)

        if is_code:
            nodes.append(CodeBlockNode(code=chunk_clean, language=lang))
            continue

        # 4. Check for List
        is_list, is_ordered, list_items = parse_list_items(chunk_clean)
        if is_list:
            nodes.append(ListNode(items=list_items, is_ordered=is_ordered))
            continue

        # 5. Default: Paragraph Node
        nodes.append(ParagraphNode(text=chunk_clean))

    # If this is the OUTPUT section and we have an uploaded screenshot, insert ImageNode if not already inserted
    if heading_text.upper() in ["OUTPUT", "SCREENSHOT", "EXECUTION OUTPUT"] and uploaded_image_bytes:
        already_has_image = any(isinstance(n, ImageNode) for n in nodes)
        if not already_has_image:
            nodes.append(ImageNode(
                image_bytes=uploaded_image_bytes,
                caption="Figure: Program Output Execution",
                mode=image_mode
            ))

    return nodes


def build_document_ast(
    raw_sections: Optional[List[dict]] = None,
    student_name: str = "",
    roll_number: str = "",
    enrollment_number: str = "",
    title: str = "",
    subject_name: str = "",
    subject_code: str = "",
    class_section: str = "",
    raw_input_text: str = "",
    uploaded_image_bytes: Optional[bytes] = None,
    image_mode: str = "embed",
    sections: Optional[List[dict]] = None,
) -> DocumentAST:
    """
    Builds the full Document AST tree from extracted sections and student metadata.
    """
    input_sections = raw_sections if raw_sections is not None else (sections or [])
    ast_nodes: List[ASTNode] = []

    # Check if a TITLE section or EXPERIMENT title was extracted
    doc_title = title
    for sec in input_sections:
        h_upper = sec["heading"].upper().strip()
        if h_upper == "TITLE":
            if not doc_title:
                doc_title = sec["content"].split("\n")[0].strip()
        elif h_upper.startswith("EXPERIMENT") and not doc_title:
            doc_title = sec["heading"].strip()

    for sec in input_sections:
        sec_heading = sec["heading"]
        sec_level = sec.get("level", 1)
        sec_content = sec.get("content", "")
        sec_is_inline = sec.get("is_inline", False)

        # Skip rendering title twice if it's already used as top document title and has no other content
        if doc_title and sec_heading.strip() == doc_title.strip() and not sec_content.strip():
            continue

        section_nodes = parse_section_content_to_nodes(
            heading_text=sec_heading,
            heading_level=sec_level,
            raw_content=sec_content,
            uploaded_image_bytes=uploaded_image_bytes,
            image_mode=image_mode,
            is_inline=sec_is_inline
        )
        ast_nodes.extend(section_nodes)

    return DocumentAST(
        title=doc_title,
        subject_name=subject_name,
        subject_code=subject_code,
        student_name=student_name,
        roll_number=roll_number,
        enrollment_number=enrollment_number,
        class_section=class_section,
        nodes=ast_nodes,
        raw_input_text=raw_input_text,
    )
