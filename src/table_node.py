"""
TableNode — AST model for data tables within report sections.
Represents a structured grid of user-provided data.
Formatting Only — content is never rewritten or invented.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class TableNode(BaseModel):
    node_type: str = "table"
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    caption: str = ""
    col_widths: Optional[List[float]] = None  # fractional widths, sum=1.0

