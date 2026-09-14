# 📄 Lab File Formatting Agent

An AI-assisted system that takes unstructured or semi-structured raw lab report notes and produces a standardized, publication-quality academic Microsoft Word (`.docx`) lab report.

---

## 🎯 Core Principles

1. **Formatting Only — Never Fabricate Content**:
   The agent structures, types, and styles your lab report. It **never** hallucinates or auto-generates missing academic content (e.g. if the `RESULT` section is omitted, it issues a helpful warning rather than fabricating an artificial result).
2. **Deterministic Architecture**:
   - Heuristic & regex parsing as primary for fast, predictable, zero-cost heading detection.
   - Abstract Syntax Tree (AST) representation for clean separation of concerns.
   - Canonical formatting profile enforcing standard academic styles (A4, 1.0-inch margins, font scales, monospaced code table shading).
   - Automated validation & single-pass correction loop to verify margin integrity, heading hierarchy, and content preservation.
3. **Screenshot Processing**:
   - **Embed Mode**: Proportional auto-scaling to fit within printable page boundaries.
   - **Read Mode**: Google Gemini Vision API to transcribe verbatim terminal output into monospaced console blocks (with graceful fallback to Embed Mode).

---

## 🏗️ Architecture & Data Flow

```
User Raw Text + Screenshot
           │
           ▼
     Streamlit UI (app.py)
           │
           ▼
     Input Preprocessor (src/preprocessor.py)
           │
           ▼
     Heading & Section Detector (src/heading_detector.py)
     • Regex, Colons, Markdown (#), Markdown Bold (**Theory**), Numbers
     • Optional LLM boundary fallback
           │
           ▼
     Content Type Detector (src/content_detector.py)
     • Code Blocks (C, Python, Java, SQL)
     • Lists (Ordered / Unordered)
     • Body Paragraphs
     • Image Nodes
           │
           ▼
     Document AST (src/models.py)
           │
           ▼
     Missing Section Auditor (src/section_auditor.py)
     • Emits non-fatal warnings for missing lab sections
           │
           ▼
     Formatting Planner (src/formatting_planner.py)
     • Applies Canonical Lab Profile (src/profiles/lab_profile.py)
           │
           ▼
     python-docx Generator (src/docx_generator.py)
     • A4, 1-inch margins, shaded code boxes, headers & footers
           │
           ▼
     Document Validator (src/validator.py)
     • Checks margins, heading skips, code styling, content preservation
           │
      ┌────┴────┐
    PASS       FAIL
      │         │
      │         ▼
      │    One-Pass Corrector (src/corrector.py)
      │         │
      │         ▼
      │    Re-validate
      │         │
      └────┬────┘
           ▼
     Downloadable .docx
```

---

## 🚀 Getting Started

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
If you wish to use **Read Mode** with Google Gemini Vision AI to transcribe terminal screenshots:
1. Copy `.env.example` to `.env`:
   ```powershell
   copy .env.example .env
   ```
2. Add your Gemini API key:
   ```env
   GEMINI_API_KEY=AIzaSy...
   ```
*(If no API key is provided, the agent will seamlessly use Embed Mode).*

### 3. Run the Streamlit Application
```powershell
streamlit run app.py
```

---

## 🧪 Running Automated Tests
```powershell
pytest -v
```

All 12 automated unit and integration tests verify:
- Markdown bold heading parsing (`**Theory**`, `**3. Algorithm:**`).
- Code detection for C and Python.
- List parsing and hierarchy traversal.
- Missing section warning generation without content fabrication.
- Proportional image embedding and dimension calculation.
- End-to-end DOCX generation, validation checks, and one-pass correction.

