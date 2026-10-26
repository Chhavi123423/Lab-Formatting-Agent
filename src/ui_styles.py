"""
ui_styles.py — Clean, professional CSS design system for Lab Report Formatting Agent.
Features academic, readable typography, subtle borders, and harmonious Light and Dark modes.
"""

DESIGN_SYSTEM_CSS = """
<style>
/* ── Theme Tokens ────────────────────────────────────────────────────────── */
:root {
  --color-primary:        #1F4E79;
  --color-primary-light:  #2B6CB0;
  --color-primary-dim:    #EBF4FB;
  --color-accent:         #3182CE;
  --color-success:        #2E7D32;
  --color-warning:        #ED8936;
  --color-danger:         #E53E3E;
  --color-bg:             #F7FAFC;
  --color-surface:        #FFFFFF;
  --color-surface-alt:    #EDF2F7;
  --color-border:         #E2E8F0;
  --color-border-strong:  #CBD5E0;
  --color-text:           #2D3748;
  --color-text-muted:     #718096;
  --color-code-bg:        #F8F9FA;
  --radius-sm:            6px;
  --radius-md:            8px;
  --radius-lg:            12px;
  --shadow-sm:            0 1px 3px rgba(0,0,0,0.06);
  --shadow-md:            0 4px 6px -1px rgba(0,0,0,0.08);
}

[data-theme="dark"] {
  --color-primary:        #63B3ED;
  --color-primary-light:  #90CDF4;
  --color-primary-dim:    #1A365D;
  --color-accent:         #4299E1;
  --color-success:        #48BB78;
  --color-warning:        #F6AD55;
  --color-danger:         #FC8181;
  --color-bg:             #0F172A;
  --color-surface:        #1E293B;
  --color-surface-alt:    #283548;
  --color-border:         #334155;
  --color-border-strong:  #475569;
  --color-text:           #F8FAFC;
  --color-text-muted:     #94A3B8;
  --color-code-bg:        #162032;
}

/* ── Streamlit Element Styling ───────────────────────────────────────────── */
.main .block-container {
  padding-top: 1.5rem !important;
  padding-bottom: 2rem !important;
  max-width: 98% !important;
}

/* ── Top Header / Brand ─────────────────────────────────────────────────── */
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 18px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  margin-bottom: 1rem;
  box-shadow: var(--shadow-sm);
}

.app-title-box {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-icon {
  font-size: 1.8rem;
}

.app-heading {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-primary);
  margin: 0;
  line-height: 1.2;
}

.app-subheading {
  font-size: 0.82rem;
  color: var(--color-text-muted);
  margin: 0;
}

/* ── Toolbar Bar ─────────────────────────────────────────────────────────── */
.top-toolbar-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 8px 16px;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: var(--shadow-sm);
}

/* ── Sidebar Accordions ─────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
}

[data-testid="stSidebar"] .streamlit-expanderHeader {
  font-size: 0.9rem !important;
  font-weight: 600 !important;
  color: var(--color-text) !important;
  border-radius: var(--radius-sm) !important;
  padding: 8px 12px !important;
  border: 1px solid var(--color-border) !important;
  background: var(--color-surface-alt) !important;
  margin-bottom: 6px !important;
}

[data-testid="stSidebar"] .streamlit-expanderHeader:hover {
  background: var(--color-primary-dim) !important;
  color: var(--color-primary) !important;
}

/* ── Section Pills in Sidebar ───────────────────────────────────────────── */
.sec-pill-active {
  background: var(--color-primary-dim) !important;
  border-left: 4px solid var(--color-primary) !important;
  font-weight: 700 !important;
}

/* ── Workspace Block Cards ──────────────────────────────────────────────── */
.block-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 16px 20px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-sm);
  transition: border-color 0.2s ease;
}

.block-card:hover {
  border-color: var(--color-primary-light);
  box-shadow: var(--shadow-md);
}

.block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--color-border);
}

.block-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 3px 10px;
  border-radius: 12px;
}

.tag-text   { background: #E2E8F0; color: #2D3748; }
.tag-code   { background: #FEFCBF; color: #744210; }
.tag-table  { background: #E9D8FD; color: #44337A; }
.tag-image  { background: #C6F6D5; color: #22543D; }

/* ── Preview Document (Academic Word Canvas Simulation) ─────────────────── */
.preview-container {
  background: #525659;
  padding: 24px;
  border-radius: var(--radius-md);
  overflow-x: auto;
}

.preview-doc {
  background: #FFFFFF !important;
  color: #111111 !important;
  max-width: 800px;
  min-height: 960px;
  margin: 0 auto;
  padding: 65px 75px;
  box-shadow: 0 4px 18px rgba(0,0,0,0.25);
  font-family: 'Times New Roman', Times, Georgia, serif;
  font-size: 12pt;
  line-height: 1.5;
}

.preview-doc h1 {
  font-size: 14pt;
  text-align: center;
  font-weight: bold;
  text-transform: uppercase;
  margin-bottom: 18px;
  color: #000000 !important;
}

.preview-doc h2 {
  font-size: 12pt;
  font-weight: bold;
  text-transform: uppercase;
  margin-top: 18px;
  margin-bottom: 6px;
  color: #000000 !important;
  border-bottom: 1px solid #E2E8F0;
  padding-bottom: 2px;
}

.preview-doc .preview-code {
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 9.5pt;
  background: #F4F4F4;
  border: 1px solid #D1D5DB;
  padding: 10px 14px;
  white-space: pre-wrap;
  margin: 8px 0;
  line-height: 1.4;
  color: #1A202C !important;
}

.preview-doc table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 11pt;
}

.preview-doc th {
  background: #1F4E79;
  color: #FFFFFF !important;
  padding: 6px 10px;
  text-align: left;
  border: 1px solid #1F4E79;
}

.preview-doc td {
  border: 1px solid #CBD5E0;
  padding: 5px 10px;
  color: #2D3748 !important;
}

.preview-doc tr:nth-child(even) td {
  background: #F8FAFC;
}

.preview-caption {
  text-align: center;
  font-size: 9pt;
  color: #718096 !important;
  font-style: italic;
  margin-top: 4px;
}

/* ── General Buttons ────────────────────────────────────────────────────── */
.stButton > button {
  border-radius: var(--radius-sm) !important;
  font-weight: 600 !important;
  transition: all 0.15s ease !important;
}

/* ── Tab Bar Clean Styling ──────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  gap: 8px;
  border-bottom: 2px solid var(--color-border);
}

.stTabs [data-baseweb="tab"] {
  font-weight: 600;
  padding: 8px 16px;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
}
</style>
"""

DARK_MODE_SCRIPT = """
<script>
(function() {
  const theme = localStorage.getItem('lab_formatting_theme') || 'light';
  document.documentElement.setAttribute('data-theme', theme);
})();
</script>
"""

def set_theme_script(theme: str) -> str:
    return f"""
<script>
localStorage.setItem('lab_formatting_theme', '{theme}');
document.documentElement.setAttribute('data-theme', '{theme}');
</script>
"""
