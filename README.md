# AI-Powered Academic Lab Formatting Agent

## Technical Implementation Plan and Phase 1 Approval Record

This project converts raw laboratory notes and optional terminal screenshots into
publication-quality Microsoft Word (`.docx`) practical files. The system is a
**formatting-only** agent: it may normalize whitespace and presentation metadata,
but it must never rewrite, summarize, reorder, or invent academic content.

This document is the implementation contract for Phase 1. It describes the
architecture, module interfaces, data flow, persistence boundary, quality gates,
and test matrix. The Python modules in `src/` are the current reference
implementation for the deterministic path.

---

## 1. Product Invariants

The following requirements are non-negotiable:

1. **Content fidelity** — user words, code logic, section order, and meaningful
   whitespace are preserved. Formatting markers may be removed from rendered
   output, but their semantic content may not be changed.
2. **Deterministic rendering** — identical input bytes, profile, and options
   produce equivalent ASTs, formatting plans, and `.docx` output.
3. **Non-blocking audits** — missing canonical sections produce warnings, never
   fabricated content.
4. **In-memory document handling** — notes, images, ASTs, generated documents,
   and OCR text are held in memory and are not written to disk by the pipeline.
5. **Explicit OCR consent** — direct embedding is the offline default. Read Mode
   sends an image to Gemini only when the caller explicitly selects it and
   supplies a key.
6. **Bounded self-correction** — at most one correction pass is attempted; the
   original validation result remains observable.
7. **Auditability** — warnings, validation checks, correction status, and profile
   provenance are returned as structured data.

---

## 2. System Architecture

```text
Raw notes + optional image bytes + options
                    |
                    v
             Streamlit/API boundary
                    |
                    v
          Hygiene preprocessor (pure)
                    |
                    v
       Heading/section parser (pure)
                    |
                    v
       Content classifier + AST builder
                    |
          +---------+---------+
          |                   |
          v                   v
   Section audit        Profile selection
 (warnings only)   sample extraction or preset
          |                   |
          +---------+---------+
                    v
           Formatting plan builder
                    |
                    v
       Deterministic python-docx renderer
                    |
                    v
             DOCX bytes (BytesIO)
                    |
                    v
       Five-point validator + score
                    |
             FAIL?  +------+
               |    |      |
               | no | yes  |
               v    v      |
             return one-pass corrector
                         |
                         v
                    re-validation
                         |
                         v
                    final DOCX + report
```

### Current module map

| Concern | Module | Contract |
| --- | --- | --- |
| Configuration and canonical sections | `src/config.py` | Preset page and typography values, section vocabulary, environment loading |
| Input hygiene | `src/preprocessor.py` | Normalize line endings and trailing whitespace while retaining leading indentation |
| Heading recognition | `src/heading_detector.py` | Convert canonical, numbered, Markdown, bold, colon, and inline headings into ordered sections |
| Content classification | `src/content_detector.py` | Classify paragraphs, lists, code, and images without changing text |
| Typed intermediate representation | `src/models.py` | Pydantic AST, formatting plan, validation result, and issue contracts |
| Missing-section audit | `src/section_auditor.py` | Emit structured, non-fatal warnings |
| Profile extraction | `src/style_extractor.py` | Extract sample typography and layout metadata |
| Profile selection | `src/profiles/` and `src/formatting_planner.py` | Apply learned profile or deterministic preset fallback |
| Screenshot handling | `src/screenshot_processor.py` | Proportional embed mode and opt-in Gemini read mode |
| DOCX/OpenXML output | `src/docx_generator.py` | Headers, footers, page fields, code boxes, forced fonts, and images |
| Output QA | `src/validator.py` | Margins, heading levels, order, code font, image bounds, token preservation |
| Repair loop | `src/corrector.py` | One bounded, observable correction pass |

---

## 3. Strongly-Typed Contracts

The AST is the boundary between parsing and rendering. Renderers must consume
the AST/formatting plan rather than raw input text.

```python
class DocumentAST(BaseModel):
    title: str
    subject_name: str
    subject_code: str
    student_name: str
    roll_number: str
    class_section: str
    nodes: list[ASTNode]
    raw_input_text: str
    warnings: list[str]

ASTNode = HeadingNode | ParagraphNode | CodeBlockNode | ListNode | ImageNode
```

Required node semantics:

- `HeadingNode`: normalized display text, source text, and level (`H1`–`H3`).
- `ParagraphNode`: exact paragraph content after hygiene-only normalization.
- `CodeBlockNode`: complete code including internal blank lines and leading
  indentation; language is metadata only.
- `ListNode`: item text and ordered/unordered metadata.
- `ImageNode`: in-memory bytes, embed/read mode, caption, and calculated size.

The formatting plan adds page, typography, header, footer, and node-level style
metadata. Validation returns `PASS` or `FAIL`, named checks, issues, and
correction state; it does not silently downgrade errors to warnings.

---

## 4. Parsing and Content-Preservation Rules

The parser applies these tiers in order:

1. Explicit Markdown headings (`#`, `##`, `###`).
2. Canonical headings (`AIM`, `THEORY`, `ALGORITHM`, `CODE`, `OUTPUT`,
   `RESULT`, and configured aliases).
3. Numbered headings (`1. Aim`, `2) Algorithm`, including bold forms).
4. Markdown-bold headings (`**Theory**`, `**3. Algorithm:**`).
5. Colon headings (`Aim:` and equivalent case variants).
6. Inline heading notation where a canonical heading starts a line.
7. Conservative heuristic fallback for all-caps or short heading-like lines.

A line that could be either code or a heading is treated as code when it is
inside a fenced block or a detected code run. Blank lines inside a code block
remain part of the same `CodeBlockNode`; they must not create empty prose
paragraphs or split the block.

The hygiene preprocessor may:

- normalize `CRLF`/`CR` to `LF`;
- remove trailing whitespace per line; and
- remove document-edge blank lines.

It must not dedent code, collapse internal code blank lines, change casing, or
normalize punctuation.

---

## 5. Style Learning and Preset Profiles

When a sample PDF or image is supplied, the style extractor produces a
`FormattingProfile` containing:

- page size and all four margins;
- body, title, H1, H2, and code font families and sizes;
- line spacing and paragraph spacing;
- header split/alignment and footer layout;
- code-box fill and border colors; and
- confidence and extraction warnings.

Low-confidence or missing sample attributes are filled from a named preset, not
from arbitrary guesses. Phase 1 presets are:

| Profile | Intended use | Body | Headings | Code |
| --- | --- | --- | --- | --- |
| `UNIVERSITY_PRACTICAL_TNR` | Traditional practical manual | Times New Roman | Times New Roman hierarchy | Consolas |
| `MODERN_ACADEMIC_CALIBRI` | Modern academic handout | Calibri | Calibri hierarchy | Consolas |
| `CANONICAL_LAB_PROFILE_V1` | Existing deterministic fallback | Calibri | Calibri hierarchy | Consolas |

Profile provenance (`learned`, `preset`, or `mixed`) is recorded in the
formatting plan and validation report.

---

## 6. Word/OpenXML Rendering Requirements

The renderer must:

- configure A4 dimensions and profile-selected printable margins;
- apply `keep_with_next` to every heading;
- render code in a single-cell shaded and bordered table;
- force code run fonts through `w:ascii`, `w:hAnsi`, and `w:cs` to `Consolas`;
- create a two-column header split when subject name/code are available;
- insert a dynamic Word `PAGE` field in the footer when page numbering is used;
- scale images proportionally to the printable width without distortion; and
- return `.docx` bytes from `io.BytesIO`, never a temporary output file.

OpenXML manipulation is isolated to the DOCX renderer. Parsers and validators
must not depend on private Word XML details beyond the checks they explicitly
own.

---

## 7. End-to-End API/Data Flow

```python
result = format_lab_document(
    raw_text: str,
    screenshots: list[bytes] | None = None,
    sample_reference: bytes | None = None,
    profile_name: str | None = None,
    screenshot_mode: Literal["embed", "read"] = "embed",
    student_name: str = "",
    roll_number: str = "",
)
```

The result contains:

```python
{
    "docx_bytes": bytes,
    "ast": DocumentAST,
    "profile": FormattingProfile,
    "validation": ValidationResult,
    "warnings": list[str],
}
```

Read Mode failures are surfaced as warnings with an explicit fallback status.
They must not erase the original image or replace it with guessed text.

---

## 8. Persistence Model and Privacy Boundary

The formatting pipeline is intentionally stateless. SQLite/SQLAlchemy is
limited to operational metadata and is **not** a document store.

### Phase 1 metadata schema

```text
format_jobs
-----------
id                 UUID/text primary key
created_at         UTC timestamp
status             queued | processing | completed | failed
profile_name       nullable text
profile_source     preset | learned | mixed
screenshot_mode    embed | read
validation_status  PASS | FAIL
preservation_score decimal
warning_count      integer
error_code         nullable text
completed_at       nullable UTC timestamp

validation_issues
-----------------
id                 integer primary key
job_id             foreign key -> format_jobs.id
rule_name          text
severity           warning | error
message            text
created_at         UTC timestamp
```

No raw notes, code, screenshot bytes, OCR transcription, AST payload, DOCX
bytes, API keys, or full user-identifying fields are persisted. A deployment
that requires job history must make retention explicit, encrypt the database,
restrict access, and store only a redacted audit record. SQLAlchemy models and
the SQLite repository are Phase 1 operational work; they must not be introduced
as hidden persistence in the core formatter.

---

## 9. Five-Point Quality Gate and Self-Correction

Every generated document is checked for:

1. page margins and page dimensions;
2. heading hierarchy and illegal level skips;
3. section order and heading presence;
4. code font/OpenXML style and image bounds; and
5. token-bag preservation of at least **85%** of source tokens.

The validator reports each check independently. A failed check may trigger one
correction pass for known formatting defects (for example, heading-level
normalization or missing code font). Content-preservation failures are not
“repaired” by changing user text. If the corrected output still fails, the
document and failure report are returned for user review.

---

## 10. Phase 1 Delivery Plan

### In scope

- Freeze the AST, formatting-plan, profile, and validation contracts.
- Extract style attributes from sample PDF/image inputs with confidence and
  deterministic preset fallback.
- Complete canonical heading aliases and seven-tier parser tests.
- Harden code-block grouping and run-level OpenXML font forcing.
- Add in-memory orchestration returning bytes plus an audit report.
- Add SQLAlchemy/SQLite metadata repository with the privacy restrictions above.
- Add deterministic integration fixtures and the full test matrix below.
- Document Gemini consent, key handling, timeout, and fallback behavior.

### Out of scope

- Generating or editing academic prose.
- Long-term storage of student submissions.
- Multi-user authentication, cloud object storage, or asynchronous job queues.
- Automatic OCR correction or semantic interpretation of terminal output.

### Phase 1 exit criteria

- Existing tests remain green.
- New tests cover every parser tier, profile fallback, OpenXML requirements,
  privacy boundary, and correction limit.
- A repeated run with the same inputs produces the same validation result and
  equivalent document structure.
- A missing section produces only an audit warning.
- A source token preservation score below 85% fails validation.
- No production path writes notes, images, or generated documents to disk.

**Decision: APPROVED to begin Phase 1 active development**, subject to the
exit criteria and privacy boundary above.

---

## 11. Test Matrix

| Area | Scenarios | Expected assertion |
| --- | --- | --- |
| Hygiene | LF, CRLF, CR; trailing spaces; indented code | Line endings normalize; indentation remains |
| Headings | Markdown, bold, numbered, colon, inline, aliases, mixed case | Correct ordered levels and section boundaries |
| Code | Fences, C/Python/Java/SQL, blank lines, braces/operators | One complete code node; source text retained |
| AST | Paragraphs, lists, images, metadata | Typed nodes and source order preserved |
| Audit | Missing AIM/THEORY/RESULT; extra sections | Warnings only; no fabricated nodes |
| Profiles | Valid sample, partial sample, unreadable sample, each preset | Learned values used where confident; fallback is deterministic |
| DOCX XML | Shading, borders, `w:ascii`/`w:hAnsi`/`w:cs`, PAGE field | Required XML elements exist and code uses Consolas |
| Layout | A4 margins, heading orphaning, long image, narrow image | Bounds and keep-with-next rules are enforced |
| OCR | No key, successful read, API failure, unreadable image | Explicit warning/fallback; original image remains available |
| Validation | Margin error, heading skip, order change, token loss | Correct rule and severity reported |
| Correction | Repairable defect, unrepairable defect, second-pass attempt | Exactly one correction pass; final status is observable |
| Privacy | BytesIO input/output, repository audit row | No content payload or secret reaches SQLite/disk |
| Integration | Complete lab report through download | Valid DOCX, `PASS`, zero unexpected issues |

Run the existing suite with:

```powershell
pip install -r requirements.txt
pytest -v
```

Run the Streamlit application with:

```powershell
streamlit run app.py
```

Read Mode requires an explicitly configured `GEMINI_API_KEY`; without it, the
application remains fully usable in offline Embed Mode.

---

## 12. Repository Layout

```text
.
├── app.py
├── requirements.txt
├── .env.example
├── src/
│   ├── models.py
│   ├── preprocessor.py
│   ├── heading_detector.py
│   ├── content_detector.py
│   ├── section_auditor.py
│   ├── style_extractor.py
│   ├── formatting_planner.py
│   ├── screenshot_processor.py
│   ├── docx_generator.py
│   ├── validator.py
│   ├── corrector.py
│   └── profiles/
└── tests/
```

The implementation should continue to preserve this separation: pure parsing
and validation logic must remain independently testable, while UI, database
metadata, and external OCR integrations stay at the application boundary.
