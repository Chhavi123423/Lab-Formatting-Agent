from typing import List, Literal, Optional, Union, Dict, Any
from pydantic import BaseModel, Field


class BaseNode(BaseModel):
    """Base class for all AST nodes."""
    node_type: str


class HeadingNode(BaseNode):
    node_type: Literal["heading"] = "heading"
    text: str
    level: int = 1  # 1 for H1, 2 for H2, 3 for H3
    raw_text: str = ""
    is_inline: bool = False
    inline_text: str = ""


class ParagraphNode(BaseNode):
    node_type: Literal["paragraph"] = "paragraph"
    text: str


class CodeBlockNode(BaseNode):
    node_type: Literal["code_block"] = "code_block"
    code: str
    language: str = "text"


class ListNode(BaseNode):
    node_type: Literal["list"] = "list"
    items: List[str] = Field(default_factory=list)
    is_ordered: bool = False


class ImageNode(BaseNode):
    node_type: Literal["image"] = "image"
    image_bytes: Optional[bytes] = None
    file_path: Optional[str] = None
    caption: str = ""
    width_inches: float = 5.5
    mode: Literal["embed", "read"] = "embed"


ASTNode = Union[HeadingNode, ParagraphNode, CodeBlockNode, ListNode, ImageNode]


class DocumentAST(BaseModel):
    title: str = ""
    subject_name: str = ""
    subject_code: str = ""
    student_name: str = ""
    roll_number: str = ""
    class_section: str = ""
    nodes: List[ASTNode] = Field(default_factory=list)
    raw_input_text: str = ""
    warnings: List[str] = Field(default_factory=list)


class FormattingPlan(BaseModel):
    profile_name: str = "CANONICAL_LAB_PROFILE_V1"
    page_config: Dict[str, Any]
    typography: Dict[str, Any]
    header_config: Dict[str, Any] = Field(default_factory=dict)
    footer_config: Dict[str, Any] = Field(default_factory=dict)
    subject_name: str = ""
    subject_code: str = ""
    student_name: str = ""
    roll_number: str = ""
    class_section: str = ""
    nodes: List[Dict[str, Any]] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    severity: Literal["error", "warning"] = "error"
    rule_name: str
    message: str


class ValidationResult(BaseModel):
    status: Literal["PASS", "FAIL"] = "PASS"
    issues: List[ValidationIssue] = Field(default_factory=list)
    checks_performed: List[str] = Field(default_factory=list)
    correction_attempted: bool = False
    correction_succeeded: bool = False

