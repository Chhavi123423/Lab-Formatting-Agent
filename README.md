# 📄 Lab Report Formatting Agent — v2.0

A professional, modern **Lab Report Builder** web application. Students build structured lab reports section by section in an interactive workspace, then export a properly formatted Word (`.docx`) file.

> **Core Principle: Formatting Only — Never Content.**
> The application structures, styles, and exports your work. It never rewrites, summarizes, invents, or changes your academic content.

---

## 🆕 What's New in v2.0

| Feature | Before | After |
|---|---|---|
| UI | Single paste-and-go form | Left sidebar + wide central workspace |
| Sections | Detected from pasted text | Full section manager (add/rename/reorder/duplicate/delete) |
| Content types | Text + one screenshot | Text, Code, Tables, Images — multiple per section |
| Tables | Flattened to text | Real Word tables (editable in MS Word) |
| Screenshots | One per report | Multiple images per section, independent captions |
| Preview | None | Full in-app HTML preview before export |
| Auth | None | Sign up / Sign in / Session management |
| Database | None | SQLite — saved reports per user account |
| Theme | Fixed light | Light + Dark mode toggle |
| Tests | 18 | 48 (30 new for auth, tables, section state) |

---

## 🏗️ Architecture

```
app.py                        ← Streamlit entry point (routing, UI)
src/
  ui_styles.py                ← CSS design system (light/dark tokens)
  report_state.py             ← Session-state section & block manager
  preview_renderer.py         ← HTML preview + AST bridge
  auth.py                     ← bcrypt password hashing, session tokens
  database.py                 ← SQLite schema, parameterized queries
  table_node.py               ← TableNode AST shim
  models.py                   ← Pydantic AST models (unchanged)
  preprocessor.py             ← Text cleaning (unchanged)
  heading_detector.py         ← Heuristic + LLM section parser (unchanged)
  content_detector.py         ← Code/list/image detector (unchanged)
  section_auditor.py          ← Missing section warnings (unchanged)
  formatting_planner.py       ← AST → FormattingPlan (extended for tables)
  docx_generator.py           ← python-docx renderer (extended for tables)
  validator.py                ← Margin/heading/content checks (unchanged)
  corrector.py                ← One-pass correction loop (unchanged)
  screenshot_processor.py     ← Image embed / Vision AI read (unchanged)
  style_extractor.py          ← AI formatting rule extractor (unchanged)
  profiles/                   ← Built-in document profiles (unchanged)
tests/
  test_auth.py                ← 12 auth unit tests (new)
  test_tables.py              ← 4 table rendering tests (new)
  test_report_state.py        ← 14 section/block state tests (new)
  test_*.py                   ← 18 original tests (all preserved)
```

---

## 🚀 Getting Started

### 1. Install dependencies
```powershell
pip install -r requirements.txt
```

### 2. Configure environment (optional)
```powershell
copy .env.example .env
```
Edit `.env` and add your Gemini API key if you want **Read Mode** (Vision AI screenshot transcription).

### 3. Run the application
```powershell
streamlit run app.py
```

The database (`lab_reports.db`) is created automatically on first run.

---

## 🧪 Running Tests
```powershell
pytest -v
```
All 48 tests should pass. Tests cover:
- Password hashing, email validation, session tokens
- Table rendering in Word documents (headers, rows, real Word tables)
- Section management (add, rename, delete, duplicate, reorder)
- Block management (multiple images, text, code, table blocks)
- Report serialization (image bytes excluded from saved data)
- All original 18 pipeline tests (unchanged)

---

## 🖥️ UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│  TOOLBAR:  📄 Report Title   [Preview] [Validate] [Export]  │
├──────────────────┬──────────────────────────────────────────┤
│  LEFT SIDEBAR    │  CENTRAL WORKSPACE                       │
│                  │                                          │
│  🏠 Dashboard    │  ✏️ [Active Section Name]                │
│  📋 Report Details│                                         │
│  📂 Sections ◀   │  ┌─────────────────────────────────┐    │
│   • Aim ●        │  │ ✏️ Text  [content text area]    │    │
│   • Theory ●     │  └─────────────────────────────────┘    │
│   • Code ●       │  ┌─────────────────────────────────┐    │
│   • Output ⚪    │  │ 💻 Code  python ▾  [code area]  │    │
│  🎨 Formatting   │  └─────────────────────────────────┘    │
│  🖼️ Images       │  ┌─────────────────────────────────┐    │
│  📊 Tables       │  │ 📊 Table  [header|cells grid]   │    │
│  📥 Import       │  └─────────────────────────────────┘    │
│  👁️ Preview      │  ┌─────────────────────────────────┐    │
│  📤 Export       │  │ 🖼️ Image  [upload/preview]      │    │
│  👤 Account      │  └─────────────────────────────────┘    │
│                  │                                          │
│                  │  [✏️ Text] [💻 Code] [📊 Table] [🖼️ Img] │
└──────────────────┴──────────────────────────────────────────┘
```

---

## 🔒 Security

- Passwords hashed with **bcrypt** (never stored in plain text)
- All database queries use **parameterized statements** (no SQL injection)
- Session tokens: cryptographically random (48-byte URL-safe)
- Sessions stored server-side in SQLite (7-day expiry)
- Image bytes excluded from serialized saved reports
- No secrets committed to source control (use `.env`)

---

## 📊 Database Schema

```sql
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,      -- normalized to lowercase
    password_hash TEXT    NOT NULL,             -- bcrypt hash
    created_at    TEXT    NOT NULL,
    updated_at    TEXT    NOT NULL,
    last_login_at TEXT
);

CREATE TABLE sessions (
    token      TEXT    PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT    NOT NULL,
    expires_at TEXT    NOT NULL
);

CREATE TABLE saved_reports (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title         TEXT    NOT NULL,
    document_data TEXT    NOT NULL,             -- JSON blob (no image bytes)
    created_at    TEXT    NOT NULL,
    updated_at    TEXT    NOT NULL
);
```

---

## 📋 Section Content Types

Each section can contain any combination of:

| Block type | Description | Exported as |
|---|---|---|
| **Text** | Paragraphs, lists, notes | Styled Word paragraphs |
| **Code** | Program source code (C/C++/Python/Java/SQL/…) | Monospaced shaded/unboxed code block |
| **Table** | Grid of data with headers | Real Word table (not flat text) |
| **Image** | Screenshots, diagrams | Embedded image with caption |

Multiple blocks of any type per section. Multiple images never overwrite each other.

---

## ⚙️ Known Limitations

1. **Raw-text import** (Import Raw Text sidebar) uses heuristic heading detection. Complex or unconventional formatting may require manual section cleanup after import.
2. **Image bytes** are not saved to the database (session-only by design). Reload a saved report and re-upload images if needed.
3. **Read Mode** (Vision AI screenshot transcription) requires a Gemini API key in `.env`.
4. **Theme persistence** uses `localStorage` — preserved across page refreshes in the same browser.
5. Tables currently use a fixed column distribution. Custom column widths are a planned enhancement.
