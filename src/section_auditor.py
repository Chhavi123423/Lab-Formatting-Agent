from typing import List
from src.models import DocumentAST, HeadingNode


# Canonical section groups (synonyms grouped together)
CANONICAL_EXPECTATIONS = [
    {"name": "AIM / OBJECTIVE", "keywords": ["AIM", "OBJECTIVE", "PURPOSE"]},
    {"name": "THEORY", "keywords": ["THEORY", "BACKGROUND", "INTRODUCTION"]},
    {"name": "IMPLEMENTATION / CODE", "keywords": ["IMPLEMENTATION", "CODE", "SOURCE CODE", "PROGRAM", "ALGORITHM"]},
    {"name": "OUTPUT", "keywords": ["OUTPUT", "SCREENSHOT", "EXECUTION"]},
    {"name": "RESULT / CONCLUSION", "keywords": ["RESULT", "RESULTS", "CONCLUSION"]},
]


def audit_missing_sections(ast: DocumentAST) -> List[str]:
    """
    Audits the AST against canonical lab expectations.
    Returns a list of user-facing warning messages.
    NEVER fabricates or adds content.
    """
    warnings: List[str] = []

    # Extract all heading names in uppercase
    detected_headings = [
        node.text.upper().strip()
        for node in ast.nodes
        if isinstance(node, HeadingNode)
    ]

    for expected in CANONICAL_EXPECTATIONS:
        group_name = expected["name"]
        keywords = expected["keywords"]

        found = any(
            any(kw in h for kw in keywords)
            for h in detected_headings
        )

        if not found:
            warnings.append(
                f"Missing expected lab section: '{group_name}'. "
                "Document will be formatted with your provided sections only."
            )

    ast.warnings.extend(warnings)
    return warnings

