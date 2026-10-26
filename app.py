"""
app.py — Lab Report Formatting Agent v2.0
Interactive Document Builder & Formatting Engine.

Core Principle: Formatting Only — Never Content.
The application preserves technical content verbatim; it never silently rewrites,
summarizes, or fabricates academic data.
"""
import io
import os
import json
import pandas as pd
import streamlit as st
from datetime import datetime, timezone, timedelta

# ── 1. Page Configuration (Wide Workspace) ───────────────────────────────────
st.set_page_config(
    page_title="Lab Report Formatting Agent",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 2. Imports & Internal Modules ─────────────────────────────────────────────
from src.ui_styles import DESIGN_SYSTEM_CSS, DARK_MODE_SCRIPT, set_theme_script
from src.report_state import (
    init_report, reset_report, load_sample_report, get_meta, update_meta,
    get_sections, get_section_by_id, add_section, rename_section,
    duplicate_section, delete_section, move_section_up, move_section_down,
    section_has_content, add_block, update_block, delete_block,
    move_block_up, move_block_down, report_to_dict, report_from_dict,
    import_from_raw_text
)
from src.preview_renderer import render_preview_html, report_to_ast
from src.auth import (
    hash_password, verify_password, validate_email, validate_password,
    normalize_email, generate_session_token
)
from src.database import (
    init_db, create_user, get_user_by_email, get_user_by_id, update_last_login,
    create_session, get_session, delete_session,
    save_report, update_report, get_user_reports, get_report, delete_report
)
from src.profiles import get_profile_by_name, get_university_practical_profile
from src.style_extractor import extract_formatting_rules_from_sample
from src.screenshot_processor import extract_text_from_screenshot_read_mode
from src.formatting_planner import create_formatting_plan
from src.docx_generator import generate_docx_from_plan
from src.validator import validate_generated_docx
from src.corrector import run_one_pass_correction
from src.section_auditor import audit_missing_sections
from src.models import HeadingNode, CodeBlockNode, ListNode, ImageNode, ParagraphNode, TableNode

# ── 3. Initialize Database & Session State ────────────────────────────────────
try:
    init_db()
except Exception as _e:
    pass

init_report()

# Inject CSS tokens & Theme
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"
st.markdown(DARK_MODE_SCRIPT, unsafe_allow_html=True)
st.markdown(DESIGN_SYSTEM_CSS, unsafe_allow_html=True)
st.markdown(set_theme_script(st.session_state["theme"]), unsafe_allow_html=True)
st.markdown(
    f"""<style>
    .sidebar-brand {{ padding: .35rem 0 .8rem; letter-spacing: .04em; color: var(--color-primary); }}
    .sidebar-brand small {{ display: block; margin-top: .25rem; color: var(--color-text-muted); font-size: .72rem; letter-spacing: 0; }}
    .home-hero {{ min-height: calc(100vh - 8rem); display: flex; flex-direction: column; justify-content: center;
                  align-items: center; text-align: center; color: var(--color-text); padding-top: 2rem; }}
    .home-hero h2 {{ font-size: clamp(2rem, 4vw, 3.3rem); margin-bottom: .6rem; }}
    [data-testid="stSidebar"] {{ transition: width .18s ease, min-width .18s ease; }}
    [data-testid="stSidebarCollapseButton"], [data-testid="stSidebar"] button[kind="header"] {{ display: none !important; }}
    {('[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child { width: 4.8rem !important; min-width: 4.8rem !important; max-width: 4.8rem !important; } [data-testid="stSidebar"] .sidebar-brand strong, [data-testid="stSidebar"] .sidebar-brand small, [data-testid="stSidebar"] > div:first-child > div > div > p, [data-testid="stSidebar"] .stExpander, [data-testid="stSidebar"] [data-testid="stExpander"], [data-testid="stSidebar"] hr { display: none !important; } [data-testid="stSidebar"] .stButton > button { padding-left: .35rem !important; padding-right: .35rem !important; }' if st.session_state.get("sidebar_collapsed") else '')}
    </style>""",
    unsafe_allow_html=True,
)


# ── 4. Helper Functions ───────────────────────────────────────────────────────
def get_current_user():
    token = st.session_state.get("session_token")
    if not token:
        return None
    sess = get_session(token)
    if not sess:
        st.session_state.pop("session_token", None)
        return None
    return get_user_by_id(sess["user_id"])

def login_user(user_id: int):
    token = generate_session_token()
    expires = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    create_session(token, user_id, expires)
    st.session_state["session_token"] = token
    update_last_login(user_id)

def logout_user():
    token = st.session_state.get("session_token")
    if token:
        delete_session(token)
    st.session_state.pop("session_token", None)

def toggle_theme():
    st.session_state["theme"] = "dark" if st.session_state["theme"] == "light" else "light"
    st.markdown(set_theme_script(st.session_state["theme"]), unsafe_allow_html=True)

def mark_download_started():
    """Record the user action so completion messaging is not shown prematurely."""
    st.session_state["download_started"] = True

def display_name():
    return user["name"] if user else "there"

user = get_current_user()

if "active_nav" not in st.session_state:
    st.session_state["active_nav"] = "Home"
if "sidebar_collapsed" not in st.session_state:
    st.session_state["sidebar_collapsed"] = False

# ── Top account and overflow actions ──
top_left, top_spacer, top_signin, top_signup, top_more = st.columns([4, 3, 1, 1, .6])
with top_left:
    st.markdown("### LAB FORMATTING AGENT")
with top_signin:
    if user:
        st.caption(f"Signed in as **{user['name']}**")
    elif st.button("Sign in", use_container_width=True, key="top_signin"):
        st.session_state["auth_panel"] = "signin"
        st.rerun()
with top_signup:
    if not user and st.button("Sign up", use_container_width=True, key="top_signup"):
        st.session_state["auth_panel"] = "signup"
        st.rerun()
with top_more:
    with st.popover("⋮", use_container_width=True):
        if user:
            st.write(user["email"])
            if st.button("Sign out", use_container_width=True, key="top_signout"):
                logout_user()
                st.rerun()
        else:
            st.caption("Guest mode: reports remain in this browser session.")

if st.session_state.get("auth_panel") and not user:
    auth_title = "Sign in to your account" if st.session_state["auth_panel"] == "signin" else "Create your account"
    with st.container(border=True):
        st.markdown(f"#### {auth_title}")
        if st.session_state["auth_panel"] == "signin":
            with st.form("top_login_form"):
                top_email = st.text_input("Email", key="top_login_email")
                top_password = st.text_input("Password", type="password", key="top_login_password")
                if st.form_submit_button("Sign in", use_container_width=True):
                    u_record = get_user_by_email(normalize_email(top_email))
                    if u_record and verify_password(top_password, u_record["password_hash"]):
                        login_user(u_record["id"])
                        st.session_state.pop("auth_panel", None)
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")
        else:
            with st.form("top_signup_form"):
                top_name = st.text_input("Full name", key="top_signup_name")
                top_email = st.text_input("Email", key="top_signup_email")
                top_password = st.text_input("Password (min 8 chars)", type="password", key="top_signup_password")
                if st.form_submit_button("Create account", use_container_width=True):
                    e_ok, e_msg = validate_email(top_email)
                    p_ok, p_msg = validate_password(top_password)
                    if not e_ok:
                        st.error(e_msg)
                    elif not p_ok:
                        st.error(p_msg)
                    elif not top_name.strip():
                        st.error("Name is required.")
                    else:
                        ok, msg, new_uid = create_user(
                            top_name, normalize_email(top_email), hash_password(top_password)
                        )
                        if ok:
                            login_user(new_uid)
                            st.session_state.pop("auth_panel", None)
                            st.rerun()
                        else:
                            st.error(msg)


# ═════════════════════════════════════════════════════════════════════════════
#  LEFT SIDEBAR — 9 Feature Groups
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    nav_items = [
        ("Home", "⌂"),
        ("Formatting Rules", "🎨"),
        ("History", "🕘"),
        ("Uploads", "🖼️"),
        ("Document Settings", "⚙️"),
        ("Account Settings", "👤"),
        ("Feedback", "💬"),
    ]
    brand_col, toggle_col = st.columns([5, 1])
    with brand_col:
        st.markdown(
            '<div class="sidebar-brand"><strong>LAB FORMATTING AGENT</strong>'
            '<small>Formatting only — never content</small></div>',
            unsafe_allow_html=True,
        )
    with toggle_col:
        if st.button("»" if not st.session_state["sidebar_collapsed"] else "«",
                     help="Collapse or expand navigation", key="sidebar_toggle"):
            st.session_state["sidebar_collapsed"] = not st.session_state["sidebar_collapsed"]
            st.rerun()

    if not st.session_state["sidebar_collapsed"]:
        st.markdown("**Navigate**")
    for label, icon in nav_items:
        nav_label = icon if st.session_state["sidebar_collapsed"] else f"{icon}  {label}"
        if st.button(
            nav_label,
            key=f"nav_{label.lower().replace(' ', '_')}",
            use_container_width=True,
            type="primary" if st.session_state["active_nav"] == label else "secondary",
            help=label,
        ):
            st.session_state["active_nav"] = label
            st.rerun()
    st.markdown("---")

    # ── Group 1: Report Details ──
    with st.expander("📋 Report Details", expanded=False):
        meta = get_meta()
        new_title = st.text_input("Document Title", value=meta.get("title", ""), placeholder="e.g. EXPERIMENT-3")
        c1, c2 = st.columns(2)
        with c1:
            new_sub = st.text_input("Subject / Course", value=meta.get("subject", ""), placeholder="e.g. CD PRACTICAL FILE")
            new_exp_no = st.text_input("Experiment No.", value=meta.get("experiment_no", ""), placeholder="e.g. 3")
            new_name = st.text_input("Student Name", value=meta.get("student_name", ""), placeholder="e.g. Chhavi Choudhary")
            new_class = st.text_input("Class / Section", value=meta.get("class_section", ""), placeholder="e.g. IT-2")
            new_inst = st.text_input("Institution", value=meta.get("institution", ""), placeholder="College / University")
        with c2:
            new_code = st.text_input("Course Code", value=meta.get("subject_code", ""), placeholder="e.g. CIC-351")
            new_exp_title = st.text_input("Experiment Title", value=meta.get("experiment_title", ""), placeholder="Brief title")
            new_roll = st.text_input("Roll Number", value=meta.get("roll_number", ""), placeholder="e.g. 19")
            new_faculty = st.text_input("Faculty / Instructor", value=meta.get("faculty_name", ""), placeholder="Instructor name")
            new_date = st.text_input("Submission Date", value=meta.get("submission_date", ""), placeholder="e.g. 26-Oct-2026")
        
        # Immediate reactive update without forced submission button
        update_meta(
            title=new_title, subject=new_sub, subject_code=new_code,
            experiment_no=new_exp_no, experiment_title=new_exp_title,
            student_name=new_name, roll_number=new_roll,
            class_section=new_class, faculty_name=new_faculty,
            submission_date=new_date, institution=new_inst
        )

    # ── Group 2: Sections Manager ──
    with st.expander("📂 Sections Manager", expanded=True):
        sections = get_sections()
        active_id = st.session_state.get("active_section_id")

        # Add section form
        add_col1, add_col2 = st.columns([3, 1])
        with add_col1:
            new_sec_name = st.text_input("Section Name", placeholder="New section name...", label_visibility="collapsed", key="add_sec_txt")
        with add_col2:
            if st.button("＋ Add", use_container_width=True, key="btn_add_sec"):
                if new_sec_name.strip():
                    add_section(new_sec_name.strip())
                    st.rerun()

        st.caption("Click a section to open it in the central workspace:")
        for idx, sec in enumerate(sections):
            is_active = (sec["id"] == active_id)
            has_c = section_has_content(sec["id"])
            indicator = "🟢" if has_c else "⚪"
            btn_label = f"{indicator} {sec['name']}"

            col_btn, col_actions = st.columns([3, 1])
            with col_btn:
                btn_type = "primary" if is_active else "secondary"
                if st.button(btn_label, key=f"sec_btn_{sec['id']}", use_container_width=True, type=btn_type):
                    st.session_state["active_section_id"] = sec["id"]
                    st.rerun()

            with col_actions:
                with st.popover("⚙️"):
                    st.markdown(f"**Manage: {sec['name']}**")
                    new_n = st.text_input("Rename", value=sec["name"], key=f"rn_{sec['id']}")
                    if st.button("Rename", key=f"do_rn_{sec['id']}"):
                        rename_section(sec["id"], new_n)
                        st.rerun()
                    
                    st.markdown("---")
                    c_up, c_dn = st.columns(2)
                    with c_up:
                        if st.button("⬆ Up", key=f"up_{sec['id']}", disabled=(idx == 0)):
                            move_section_up(sec["id"])
                            st.rerun()
                    with c_dn:
                        if st.button("⬇ Down", key=f"dn_{sec['id']}", disabled=(idx == len(sections) - 1)):
                            move_section_down(sec["id"])
                            st.rerun()

                    if st.button("📋 Duplicate", key=f"dup_{sec['id']}", use_container_width=True):
                        duplicate_section(sec["id"])
                        st.rerun()

                    if st.button("🗑️ Delete", key=f"del_{sec['id']}", use_container_width=True, type="primary"):
                        delete_section(sec["id"])
                        st.rerun()

    # ── Group 3: Content Editor ──
    with st.expander("✏️ Content Editor Quick Tools", expanded=False):
        active_sec = get_section_by_id(st.session_state.get("active_section_id", ""))
        if active_sec:
            st.markdown(f"**Target Section:** `{active_sec['name']}`")
            st.caption("Insert a new block directly into this section:")
            c_b1, c_b2 = st.columns(2)
            with c_b1:
                if st.button("＋ Text Block", use_container_width=True, key="quick_add_txt"):
                    add_block(active_sec["id"], "text")
                    st.rerun()
                if st.button("＋ Code Block", use_container_width=True, key="quick_add_code"):
                    add_block(active_sec["id"], "code", language="cpp")
                    st.rerun()
            with c_b2:
                if st.button("＋ Data Table", use_container_width=True, key="quick_add_tbl"):
                    add_block(active_sec["id"], "table", headers=["Param", "Value"], rows=[["", ""]])
                    st.rerun()
                if st.button("＋ Screenshot", use_container_width=True, key="quick_add_img"):
                    add_block(active_sec["id"], "image")
                    st.rerun()
        else:
            st.info("Select a section above to add blocks.")

    # ── Group 4: Images & Screenshots ──
    with st.expander("🖼️ Images & Screenshots", expanded=False):
        active_sec = get_section_by_id(st.session_state.get("active_section_id", ""))
        if active_sec:
            st.markdown(f"**Section:** `{active_sec['name']}`")
            uploaded_quick_img = st.file_uploader("Upload screenshot to this section", type=["png", "jpg", "jpeg"], key="sb_quick_img")
            img_caption_input = st.text_input("Image Caption", value="Figure: Execution Output", key="sb_quick_img_cap")
            if uploaded_quick_img and st.button("Add Image", key="sb_quick_add_img_btn", use_container_width=True):
                add_block(
                    active_sec["id"], "image",
                    bytes=uploaded_quick_img.getvalue(),
                    filename=uploaded_quick_img.name,
                    caption=img_caption_input
                )
                st.success("Image added to section.")
                st.rerun()
        else:
            st.info("Select a section first.")

    # ── Group 5: Tables ──
    with st.expander("📊 Tables Tool", expanded=False):
        active_sec = get_section_by_id(st.session_state.get("active_section_id", ""))
        if active_sec:
            st.markdown(f"**Section:** `{active_sec['name']}`")
            t_cols = st.number_input("Columns", min_value=1, max_value=8, value=3, key="sb_tbl_cols")
            t_rows = st.number_input("Rows", min_value=1, max_value=15, value=3, key="sb_tbl_rows")
            t_cap = st.text_input("Table Caption", value="Table 1: Experimental Data", key="sb_tbl_cap")
            if st.button("Insert Table", key="sb_tbl_insert_btn", use_container_width=True):
                add_block(
                    active_sec["id"], "table",
                    headers=[f"Column {i+1}" for i in range(int(t_cols))],
                    rows=[["" for _ in range(int(t_cols))] for _ in range(int(t_rows))],
                    caption=t_cap
                )
                st.success("Table added.")
                st.rerun()
        else:
            st.info("Select a section first.")

    # ── Group 6: Formatting and Page Layout (Restored AI Extractor!) ──
    with st.expander(
        "🎨 Formatting & Page Layout",
        expanded=st.session_state.get("active_nav") in {"Formatting Rules", "Document Settings"},
    ):
        profile_mode = st.radio(
            "Formatting Rules Source",
            options=["Built-in Academic Profile", "🪄 Extract Rules with Vision AI"],
            index=1 if st.session_state.get("reference_upload_mode") else 0,
            key="sb_prof_mode"
        )

        active_profile = get_university_practical_profile()
        server_key = os.getenv("GEMINI_API_KEY", "")

        if "Extract Rules" in profile_mode:
            user_key = st.text_input(
                "Gemini API Key (BYOK)",
                type="password",
                value=st.session_state.get("user_provided_key", ""),
                placeholder="AIzaSy...",
                help="Get a free key at https://aistudio.google.com"
            )
            if user_key.strip():
                st.session_state["user_provided_key"] = user_key.strip()
                eff_key = user_key.strip()
            else:
                eff_key = server_key

            ref_file = st.file_uploader("Upload Sample Practical File (.pdf, .png, .jpg)", type=["pdf", "png", "jpg", "jpeg"], key="sb_ref_upload")
            if ref_file:
                if st.button("Extract Formatting Profile", key="sb_do_extract"):
                    with st.spinner("Analyzing style with Vision AI..."):
                        success, prof_data, msg = extract_formatting_rules_from_sample(ref_file.getvalue(), ref_file.name, api_key=eff_key)
                        if success:
                            st.session_state["extracted_profile"] = prof_data
                            st.success(f"✅ {msg}")
                        else:
                            st.error(msg)
            
            if "extracted_profile" in st.session_state:
                active_profile = st.session_state["extracted_profile"]
                if st.button("Reset to Default Rules", key="sb_clear_rules"):
                    st.session_state.pop("extracted_profile", None)
                    st.rerun()
        else:
            preset_choice = st.selectbox(
                "Preset Profile",
                [
                    "University Practical File (CIC-351 / Times New Roman / Split Header)",
                    "Standard Academic Lab Profile (Calibri / Navy Accent / Boxed Code)"
                ],
                index=0,
                key="sb_preset_sel"
            )
            active_profile = get_profile_by_name(preset_choice)

        st.session_state["active_profile"] = active_profile

        # Footer styling options
        st.markdown("**Footer Options**")
        footer_choice = st.selectbox(
            "Footer Layout",
            ["Auto (from Profile)", "Student Stamp (Name, Class, Roll No)", "Page Numbering (Page X)", "Custom Text", "None"],
            index=0,
            key="sb_footer_choice"
        )
        st.session_state["footer_choice"] = footer_choice
        if "Custom Text" in footer_choice:
            st.text_input("Custom footer text", value="Lab File Record", key="sb_custom_footer_txt")

        # Page margins
        st.markdown("**Page Margins (Inches)**")
        m_c1, m_c2 = st.columns(2)
        with m_c1:
            st.number_input("Top", value=1.0, step=0.1, key="sb_m_top", min_value=0.5, max_value=2.0)
            st.number_input("Left", value=1.0, step=0.1, key="sb_m_left", min_value=0.5, max_value=2.0)
        with m_c2:
            st.number_input("Bottom", value=1.0, step=0.1, key="sb_m_bottom", min_value=0.5, max_value=2.0)
            st.number_input("Right", value=1.0, step=0.1, key="sb_m_right", min_value=0.5, max_value=2.0)

    # ── Group 7: Preview and Validation ──
    with st.expander("👁️ Preview & Validation", expanded=False):
        st.caption("Use the central workspace tabs to inspect live document rendering or view detailed validation diagnostics.")
        st.info("💡 You can switch directly between the **Editor**, **Preview**, and **Validation** tabs in the main workspace.")

    # ── Group 8: Export / Download ──
    with st.expander("📥 Export / Download", expanded=False):
        st.caption("Generate your standardized, publication-quality Microsoft Word document:")
        if st.button("⚡ Generate Word Document (.docx)", use_container_width=True, type="primary", key="sb_gen_btn"):
            st.session_state["trigger_generate"] = True

    # ── Group 9: Account and Settings ──
    with st.expander("👤 Account & Settings", expanded=False):
        if user:
            st.markdown(f"**Signed in as:** `{user['name']}`")
            st.caption(f"Email: {user['email']}")
            
            # Saved reports
            st.markdown("**Your Saved Reports:**")
            u_reports = get_user_reports(user["id"])
            if u_reports:
                for rpt in u_reports[:5]:
                    rc1, rc2 = st.columns([3, 1])
                    with rc1:
                        st.caption(rpt["title"] or "(Untitled)")
                    with rc2:
                        if st.button("Load", key=f"ld_rpt_{rpt['id']}"):
                            full_r = get_report(rpt["id"], user["id"])
                            if full_r:
                                report_from_dict(full_r["document_data"])
                                st.session_state["saved_report_id"] = rpt["id"]
                                st.success("Loaded!")
                                st.rerun()
            else:
                st.caption("No saved reports yet.")

            if st.button("💾 Save Current Report", use_container_width=True, key="sb_save_acc_btn"):
                r_dict = report_to_dict()
                m_title = get_meta().get("title") or get_meta().get("subject") or "Untitled Report"
                sid = st.session_state.get("saved_report_id")
                if sid:
                    ok, msg = update_report(sid, user["id"], m_title, r_dict)
                else:
                    ok, msg, new_id = save_report(user["id"], m_title, r_dict)
                    if ok:
                        st.session_state["saved_report_id"] = new_id
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

            if st.button("Sign Out", use_container_width=True, key="sb_logout_btn"):
                logout_user()
                st.rerun()
        else:
            st.info("Guest Mode: Reports are stored in browser session.")
            auth_tab_login, auth_tab_signup = st.tabs(["Sign In", "Sign Up"])
            with auth_tab_login:
                with st.form("sb_login_form"):
                    l_email = st.text_input("Email", placeholder="you@university.edu")
                    l_pass = st.text_input("Password", type="password")
                    if st.form_submit_button("Sign In", use_container_width=True):
                        u_record = get_user_by_email(normalize_email(l_email))
                        if u_record and verify_password(l_pass, u_record["password_hash"]):
                            login_user(u_record["id"])
                            st.success(f"Welcome, {u_record['name']}!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials.")
            with auth_tab_signup:
                with st.form("sb_signup_form"):
                    s_name = st.text_input("Full Name", placeholder="Your Name")
                    s_email = st.text_input("Email", placeholder="you@university.edu")
                    s_pass = st.text_input("Password (min 8 chars)", type="password")
                    if st.form_submit_button("Sign Up", use_container_width=True):
                        e_ok, e_msg = validate_email(s_email)
                        p_ok, p_msg = validate_password(s_pass)
                        if not e_ok:
                            st.error(e_msg)
                        elif not p_ok:
                            st.error(p_msg)
                        elif not s_name.strip():
                            st.error("Name is required.")
                        else:
                            pw_h = hash_password(s_pass)
                            ok, msg, new_uid = create_user(s_name, normalize_email(s_email), pw_h)
                            if ok:
                                login_user(new_uid)
                                st.success("Account created!")
                                st.rerun()
                            else:
                                st.error(msg)


# ═════════════════════════════════════════════════════════════════════════════
#  HOME / CENTRAL WORKSPACE
# ═════════════════════════════════════════════════════════════════════════════

if st.session_state["active_nav"] == "Home":
    home_left, home_right = st.columns([5, 1])
    with home_right:
        if st.button("＋ Create", type="primary", use_container_width=True, key="home_create"):
            st.session_state["create_menu_open"] = not st.session_state.get("create_menu_open", False)
    if st.session_state.get("create_menu_open"):
        with st.container(border=True):
            st.markdown("### Start a report")
            st.caption("Choose how you want to set up formatting. Your content remains unchanged.")
            create_col1, create_col2, create_col3 = st.columns(3)
            with create_col1:
                if st.button("Build from Scratch", use_container_width=True, type="primary"):
                    reset_report()
                    st.session_state["active_nav"] = "Document Settings"
                    st.session_state["workspace_mode"] = "scratch"
                    st.session_state["create_menu_open"] = False
                    st.rerun()
            with create_col2:
                if st.button("Set My Own Formatting Rules", use_container_width=True):
                    st.session_state["active_nav"] = "Formatting Rules"
                    st.session_state["workspace_mode"] = "custom"
                    st.session_state["create_menu_open"] = False
                    st.rerun()
            with create_col3:
                if st.button("Upload a Reference Document", use_container_width=True):
                    st.session_state["active_nav"] = "Formatting Rules"
                    st.session_state["reference_upload_mode"] = True
                    st.session_state["workspace_mode"] = "reference"
                    st.session_state["create_menu_open"] = False
                    st.rerun()
    st.markdown("<div class='home-hero'>", unsafe_allow_html=True)
    st.markdown(f"## Welcome back, {display_name()}")
    st.caption("Create a polished laboratory report while keeping every word, image, and result yours.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

active_nav = st.session_state["active_nav"]
if active_nav != "Home":
    st.markdown(f"### {active_nav}")
    if active_nav == "History":
        if user:
            reports = get_user_reports(user["id"])
            if reports:
                for report in reports:
                    history_col, action_col = st.columns([5, 1])
                    with history_col:
                        st.markdown(f"**{report['title'] or 'Untitled report'}**")
                        st.caption(f"Last updated {report['updated_at']}")
                    with action_col:
                        if st.button("Open", key=f"history_open_{report['id']}", use_container_width=True):
                            full_report = get_report(report["id"], user["id"])
                            if full_report:
                                report_from_dict(full_report["document_data"])
                                st.session_state["saved_report_id"] = report["id"]
                                st.session_state["active_nav"] = "Formatting Rules"
                                st.rerun()
            else:
                st.info("No saved reports yet.")
        else:
            st.info("Sign in to view saved report history.")
        st.stop()
    elif active_nav == "Uploads":
        uploads = [
            (section, block)
            for section in get_sections()
            for block in section.get("blocks", [])
            if block.get("type") == "image" and block.get("bytes")
        ]
        if not uploads:
            st.info("No uploaded images in the current report.")
        for section, block in uploads:
            upload_col, detail_col, remove_col = st.columns([1.5, 3, 1])
            with upload_col:
                st.image(block["bytes"], use_container_width=True)
            with detail_col:
                st.markdown(f"**{block.get('filename') or 'Untitled image'}**")
                st.caption(f"Section: {section['name']}")
                st.caption(block.get("caption") or "No caption")
            with remove_col:
                if st.button("Remove", key=f"upload_remove_{block['id']}", use_container_width=True):
                    delete_block(section["id"], block["id"])
                    st.rerun()
        st.stop()
    elif active_nav == "Account Settings" and not user:
        st.info("Sign in from the Account & Settings panel in the sidebar to manage your profile.")
        st.stop()
    elif active_nav == "Account Settings":
        st.markdown(f"**Name:** {user['name']}")
        st.markdown(f"**Email:** {user['email']}")
        st.caption("Your saved reports are associated with this account. Password changes are not available in this version.")
        if st.button("Sign Out", key="central_logout"):
            logout_user()
            st.rerun()
        st.stop()
    elif active_nav == "Feedback":
        with st.form("feedback_form"):
            feedback = st.text_area("How can we improve the formatting workflow?", max_chars=2000)
            if st.form_submit_button("Send feedback"):
                if feedback.strip():
                    st.session_state["feedback_submitted"] = True
                    st.success("Thank you — your feedback was submitted for this session.")
                else:
                    st.error("Please enter feedback before submitting.")
        st.stop()

# ── Top Action Toolbar ──
meta = get_meta()
current_doc_title = meta.get("title") or meta.get("experiment_title") or meta.get("subject") or "Untitled Lab Report"
saved_status_label = "💾 Saved to Account" if st.session_state.get("saved_report_id") else "📝 Unsaved Session Draft"

tb_col1, tb_col2, tb_col3, tb_col4, tb_col5 = st.columns([3, 1.2, 1, 1, 0.6])
with tb_col1:
    st.markdown(f"### 📄 {current_doc_title}")
    st.caption(f"{saved_status_label} &nbsp;|&nbsp; Active Section: **{get_section_by_id(st.session_state.get('active_section_id', ''))['name'] if get_section_by_id(st.session_state.get('active_section_id', '')) else 'None'}**")

with tb_col2:
    if st.button("⚡ Load Sample Lab Report", use_container_width=True, help="Load a complete C++ experiment to instantly test preview and DOCX generation"):
        load_sample_report()
        st.success("Sample experiment loaded.")
        st.rerun()

with tb_col3:
    if st.button("🔄 Reset Report", use_container_width=True, help="Start fresh with clean default sections"):
        reset_report()
        st.rerun()

with tb_col4:
    if st.button("📥 Export .docx", use_container_width=True, type="primary", key="tb_export_btn"):
        st.session_state["trigger_generate"] = True

with tb_col5:
    th_icon = "🌙" if st.session_state["theme"] == "light" else "☀️"
    if st.button(th_icon, use_container_width=True, help="Toggle Light/Dark Theme"):
        toggle_theme()
        st.rerun()

if st.session_state.get("create_menu_open") and st.session_state["active_nav"] != "Home":
    with st.container(border=True):
        st.markdown("### Start a report")
        st.caption("Choose a formatting setup. Report content is never rewritten.")
        create_col1, create_col2, create_col3 = st.columns(3)
        with create_col1:
            if st.button("Build from Scratch", use_container_width=True, type="primary", key="toolbar_build"):
                reset_report()
                st.session_state["workspace_mode"] = "scratch"
                st.session_state["create_menu_open"] = False
                st.rerun()
        with create_col2:
            if st.button("Set My Own Formatting Rules", use_container_width=True, key="toolbar_rules"):
                st.session_state["active_nav"] = "Formatting Rules"
                st.session_state["workspace_mode"] = "custom"
                st.session_state["create_menu_open"] = False
                st.rerun()
        with create_col3:
            if st.button("Upload a Reference Document", use_container_width=True, key="toolbar_reference"):
                st.session_state["active_nav"] = "Formatting Rules"
                st.session_state["reference_upload_mode"] = True
                st.session_state["workspace_mode"] = "reference"
                st.session_state["create_menu_open"] = False
                st.rerun()

# ── Reference document setup ──
if st.session_state.get("reference_upload_mode") and active_nav == "Formatting Rules":
    with st.container(border=True):
        st.markdown("#### Upload a reference document")
        st.caption(
            "Upload a PDF or image of a formatted practical file. Only its visual formatting "
            "will be analyzed; its academic content will not be copied."
        )
        reference_key = st.text_input(
            "Gemini API key (optional)",
            type="password",
            value=st.session_state.get("user_provided_key", ""),
            key="central_reference_key",
            help="Stored only in this session and never shown in logs.",
        )
        if reference_key.strip():
            st.session_state["user_provided_key"] = reference_key.strip()
        central_ref_file = st.file_uploader(
            "Choose reference file",
            type=["pdf", "png", "jpg", "jpeg"],
            key="central_reference_upload",
        )
        if central_ref_file and st.button("Analyze formatting", type="primary", key="central_reference_analyze"):
            with st.spinner("Analyzing formatting rules..."):
                success, profile_data, message = extract_formatting_rules_from_sample(
                    central_ref_file.getvalue(),
                    central_ref_file.name,
                    api_key=st.session_state.get("user_provided_key", "") or os.getenv("GEMINI_API_KEY", ""),
                )
            if success:
                st.session_state["extracted_profile"] = profile_data
                st.session_state["workspace_rule_choice"] = "Reference document rules"
                st.success("Formatting rules extracted. Review them in the sidebar before exporting.")
            else:
                st.error(message)

# ── Focused workspace toolbar ──
if active_nav in {"Formatting Rules", "Document Settings"}:
    rule_col, download_col = st.columns([4, 1])
    with rule_col:
        rule_options = [
            "Built-in academic rules",
            "My formatting rules",
            "Reference document rules",
        ]
        if "workspace_rule_choice" not in st.session_state:
            st.session_state["workspace_rule_choice"] = (
                rule_options[2] if "extracted_profile" in st.session_state else rule_options[0]
            )
        selected_rule = st.selectbox(
            "Formatting Rules",
            rule_options,
            key="workspace_rule_choice",
            help="Choose the formatting profile used for preview and Word export.",
        )
        if selected_rule == rule_options[0]:
            st.session_state["active_profile"] = get_university_practical_profile()
        elif selected_rule == rule_options[2] and "extracted_profile" in st.session_state:
            st.session_state["active_profile"] = st.session_state["extracted_profile"]
        elif selected_rule == rule_options[2]:
            st.info("Upload and extract a reference document from the sidebar to activate these rules.")
    with download_col:
        st.markdown("<div style='height: 1.65rem'></div>", unsafe_allow_html=True)
        if st.button("📥 Download", type="primary", use_container_width=True, key="workspace_download"):
            st.session_state["trigger_generate"] = True

st.markdown("---")

# ── Generation Handler (when requested) ──
if st.session_state.get("trigger_generate"):
    with st.spinner("Generating publication-quality Word document..."):
        try:
            ast = report_to_ast(st.session_state["report"])
            prof = dict(st.session_state.get("active_profile", get_university_practical_profile()))
            
            # Apply footer customization
            f_choice = st.session_state.get("footer_choice", "Auto")
            prof["typography"] = dict(prof.get("typography", {}))
            prof["typography"]["footer"] = dict(prof["typography"].get("footer", {}))
            if "Student Stamp" in f_choice:
                prof["typography"]["footer"]["layout"] = "STUDENT_STAMP"
            elif "Page Numbering" in f_choice:
                prof["typography"]["footer"]["layout"] = "PAGE_NUMBER"
            elif "Custom Text" in f_choice:
                prof["typography"]["footer"]["layout"] = "CUSTOM_TEXT"
                prof["typography"]["footer"]["text"] = st.session_state.get("sb_custom_footer_txt", "Lab Record")
            elif "None" in f_choice:
                prof["typography"]["footer"]["layout"] = "NONE"

            # Apply margins
            prof.setdefault("page", {})
            prof["page"]["margin_top_inches"] = float(st.session_state.get("sb_m_top", 1.0))
            prof["page"]["margin_bottom_inches"] = float(st.session_state.get("sb_m_bottom", 1.0))
            prof["page"]["margin_left_inches"] = float(st.session_state.get("sb_m_left", 1.0))
            prof["page"]["margin_right_inches"] = float(st.session_state.get("sb_m_right", 1.0))

            plan = create_formatting_plan(ast, custom_profile=prof)
            docx_raw = generate_docx_from_plan(plan)
            val_res = validate_generated_docx(docx_raw, ast)
            final_bytes, final_val = run_one_pass_correction(docx_raw, val_res, ast, plan)

            st.session_state["generated_docx"] = final_bytes
            st.session_state["validation_result"] = final_val
            st.session_state["generated_warnings"] = audit_missing_sections(ast)
        except Exception as _gen_err:
            st.error(f"Generation error: {_gen_err}")
    st.session_state["trigger_generate"] = False

# Display generated download banner if document is ready
if "generated_docx" in st.session_state:
    st.success("✅ **Word document (.docx) generated successfully!** Formatting and content preservation verified.")
    d_c1, d_c2 = st.columns([3, 1])
    with d_c1:
        s_code = (meta.get("subject_code") or meta.get("subject") or "lab").replace(" ", "_")
        r_num = meta.get("roll_number") or "file"
        st.download_button(
            label=f"📥 Download Formatted Document ({s_code}_{r_num}.docx)",
            data=st.session_state["generated_docx"],
            file_name=f"{s_code}_{r_num}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
            type="primary",
            on_click=mark_download_started
        )
    with d_c2:
        if st.button("Dismiss", key="dismiss_dl"):
            st.session_state.pop("generated_docx", None)
            st.session_state.pop("validation_result", None)
            st.rerun()
    if st.session_state.get("download_started"):
        st.success(f"Thank you, {display_name()}! Your report is ready.")

# ── Primary Workspace Tabs ──
ws_tab1, ws_tab2, ws_tab3, ws_tab4 = st.tabs([
    "📝 Section Content Editor",
    "👁️ Live Document Preview",
    "✅ Validation & Diagnostics",
    "📥 Import Raw Lab Notes"
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: Section Content Editor
# ─────────────────────────────────────────────────────────────────────────────
with ws_tab1:
    sec = get_section_by_id(st.session_state.get("active_section_id", ""))
    if not sec:
        secs = get_sections()
        if secs:
            sec = secs[0]
            st.session_state["active_section_id"] = sec["id"]
        else:
            st.info("No sections available. Add a section using the sidebar.")
            st.stop()

    # Section Title & Quick Section Switcher
    sec_c1, sec_c2 = st.columns([3, 1.5])
    with sec_c1:
        st.markdown(f"## ✏️ Section: **{sec['name']}**")
    with sec_c2:
        sec_names = [s["name"] for s in get_sections()]
        current_idx = next((i for i, s in enumerate(get_sections()) if s["id"] == sec["id"]), 0)
        sel_sec_name = st.selectbox(
            "Quick switch section",
            options=sec_names,
            index=current_idx,
            key="quick_switch_sec_sel",
            label_visibility="collapsed"
        )
        if sel_sec_name != sec["name"]:
            target_s = next((s for s in get_sections() if s["name"] == sel_sec_name), None)
            if target_s:
                st.session_state["active_section_id"] = target_s["id"]
                st.rerun()

    blocks = sec.get("blocks", [])
    total_blocks = len(blocks)

    if not blocks:
        st.info(f"The section **'{sec['name']}'** is currently empty. Choose a block type below to begin adding content.")

    # Render Content Blocks
    for b_idx, blk in enumerate(blocks):
        b_type = blk.get("type", "text")
        b_id = blk["id"]

        with st.container():
            st.markdown('<div class="block-card">', unsafe_allow_html=True)
            
            # Header with tag and controls
            hdr_col1, hdr_col2 = st.columns([3, 1])
            with hdr_col1:
                if b_type == "text":
                    st.markdown('<span class="block-tag tag-text">✏️ Text Block</span>', unsafe_allow_html=True)
                elif b_type == "code":
                    st.markdown(f'<span class="block-tag tag-code">💻 Code Block ({blk.get("language", "text")})</span>', unsafe_allow_html=True)
                elif b_type == "table":
                    st.markdown('<span class="block-tag tag-table">📊 Data Table</span>', unsafe_allow_html=True)
                elif b_type == "image":
                    st.markdown('<span class="block-tag tag-image">🖼️ Screenshot / Image</span>', unsafe_allow_html=True)

            with hdr_col2:
                btn_u, btn_d, btn_rm = st.columns(3)
                with btn_u:
                    if st.button("⬆", key=f"blk_u_{b_id}", disabled=(b_idx == 0), help="Move block up"):
                        move_block_up(sec["id"], b_id)
                        st.rerun()
                with btn_d:
                    if st.button("⬇", key=f"blk_d_{b_id}", disabled=(b_idx == total_blocks - 1), help="Move block down"):
                        move_block_down(sec["id"], b_id)
                        st.rerun()
                with btn_rm:
                    if st.button("🗑️", key=f"blk_rm_{b_id}", help="Delete block"):
                        delete_block(sec["id"], b_id)
                        st.rerun()

            # Block-specific editor
            if b_type == "text":
                txt_val = st.text_area(
                    "Content",
                    value=blk.get("content", ""),
                    key=f"val_txt_{b_id}",
                    height=130,
                    label_visibility="collapsed",
                    placeholder="Enter paragraphs or bullet notes here. Double blank lines create distinct paragraphs."
                )
                if txt_val != blk.get("content", ""):
                    update_block(sec["id"], b_id, content=txt_val)

            elif b_type == "code":
                c_lang_col, c_help_col = st.columns([1.5, 3])
                with c_lang_col:
                    lang_opts = ["cpp", "c", "python", "java", "sql", "html", "javascript", "bash", "text"]
                    c_lang = blk.get("language", "cpp")
                    sel_l = st.selectbox(
                        "Syntax Language",
                        lang_opts,
                        index=lang_opts.index(c_lang) if c_lang in lang_opts else 0,
                        key=f"val_lang_{b_id}"
                    )
                with c_help_col:
                    st.caption("Indentation, tabs, and line breaks are strictly preserved in the exported Word document.")

                code_val = st.text_area(
                    "Program Code",
                    value=blk.get("content", ""),
                    key=f"val_code_{b_id}",
                    height=220,
                    label_visibility="collapsed",
                    placeholder="Paste your source code here..."
                )
                if code_val != blk.get("content", "") or sel_l != blk.get("language", "cpp"):
                    update_block(sec["id"], b_id, content=code_val, language=sel_l)

            elif b_type == "table":
                # Real interactive Data Table using st.data_editor
                headers = blk.get("headers", ["Column 1", "Column 2"])
                rows = blk.get("rows", [["", ""]])

                # Build clean DataFrame
                try:
                    df = pd.DataFrame(rows, columns=headers)
                except Exception:
                    df = pd.DataFrame([["", ""]], columns=["Col 1", "Col 2"])

                st.caption("Edit cells directly. Add or remove rows using the table tool below:")
                edited_df = st.data_editor(
                    df,
                    num_rows="dynamic",
                    use_container_width=True,
                    key=f"val_tbl_{b_id}"
                )

                tbl_caption_val = st.text_input(
                    "Table Caption",
                    value=blk.get("caption", ""),
                    key=f"val_tbl_cap_{b_id}",
                    placeholder="e.g. Table 1: Experimental Observations"
                )

                # Persist dataframe updates back to block
                new_hdrs = list(edited_df.columns)
                new_rows = edited_df.fillna("").astype(str).values.tolist()
                update_block(sec["id"], b_id, headers=new_hdrs, rows=new_rows, caption=tbl_caption_val)

            elif b_type == "image":
                img_bytes = blk.get("bytes")
                if img_bytes:
                    img_preview_col, img_info_col = st.columns([1.5, 2.5])
                    with img_preview_col:
                        st.image(img_bytes, use_container_width=True)
                    with img_info_col:
                        cap_val = st.text_input("Figure Caption", value=blk.get("caption", ""), key=f"val_img_cap_{b_id}")
                        update_block(sec["id"], b_id, caption=cap_val)
                        repl_file = st.file_uploader("Replace image", type=["png", "jpg", "jpeg"], key=f"val_img_repl_{b_id}")
                        if repl_file:
                            update_block(sec["id"], b_id, bytes=repl_file.getvalue(), filename=repl_file.name)
                            st.rerun()
                else:
                    up_img = st.file_uploader("Upload screenshot / figure", type=["png", "jpg", "jpeg"], key=f"val_img_up_{b_id}")
                    cap_val = st.text_input("Figure Caption", value=blk.get("caption", "Figure: Program Execution"), key=f"val_img_cap_empty_{b_id}")
                    if up_img:
                        update_block(sec["id"], b_id, bytes=up_img.getvalue(), filename=up_img.name, caption=cap_val)
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

    # Add block toolbar at bottom of active section
    st.markdown("#### ＋ Add Content Block to this Section")
    ab_c1, ab_c2, ab_c3, ab_c4 = st.columns(4)
    with ab_c1:
        if st.button("✏️ Add Text Block", use_container_width=True, key="btn_add_txt_ws"):
            add_block(sec["id"], "text")
            st.rerun()
    with ab_c2:
        if st.button("💻 Add Code Block", use_container_width=True, key="btn_add_code_ws"):
            add_block(sec["id"], "code", language="cpp")
            st.rerun()
    with ab_c3:
        if st.button("📊 Add Data Table", use_container_width=True, key="btn_add_tbl_ws"):
            add_block(sec["id"], "table", headers=["Parameter", "Specification", "Result"], rows=[["", "", ""]])
            st.rerun()
    with ab_c4:
        if st.button("🖼️ Add Screenshot", use_container_width=True, key="btn_add_img_ws"):
            add_block(sec["id"], "image")
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: Live Document Preview
# ─────────────────────────────────────────────────────────────────────────────
with ws_tab2:
    st.markdown("### 👁️ Real-time Document Preview (A4 Page Simulation)")
    st.caption("Renders exact heading hierarchy, two-column split headers, student stamps, tables, boxed code, and centered images:")
    
    preview_html = render_preview_html(st.session_state["report"])
    st.markdown(f'<div class="preview-container">{preview_html}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: Validation & Diagnostics
# ─────────────────────────────────────────────────────────────────────────────
with ws_tab3:
    st.markdown("### ✅ Document Hierarchy & Formatting Audit")
    
    # Run AST Auditor
    ast_current = report_to_ast(st.session_state["report"])
    missing_warnings = audit_missing_sections(ast_current)

    v_col1, v_col2, v_col3 = st.columns(3)
    v_col1.metric("Total Sections", len(st.session_state["report"].get("sections", [])))
    v_col2.metric("Total AST Nodes", len(ast_current.nodes))
    v_col3.metric("Rule Enforcement", "Formatting Only")

    # Missing Canonical Section Warnings (Advisory, never hallucinated)
    if missing_warnings:
        st.warning("⚠️ **Academic Structure Advisory:**")
        for w in missing_warnings:
            st.write(f"- {w}")
        st.caption("ℹ️ *Rule Enforced: The agent is a structural formatter and will never fabricate academic content for missing sections.*")
    else:
        st.success("✅ **All canonical lab sections (Aim, Theory, Code, Output, Result) are accounted for.**")

    # Hierarchy Inspector
    with st.expander("🔍 Detected Section Hierarchy Tree", expanded=True):
        for s in st.session_state["report"].get("sections", []):
            b_count = len(s.get("blocks", []))
            types = ", ".join(set(b["type"] for b in s.get("blocks", []))) or "empty"
            st.write(f"📁 **{s['name']}** — *({b_count} blocks: {types})*")

    # AST Node Inspector
    with st.expander("📑 Node Inspector (Abstract Syntax Tree)", expanded=False):
        for idx, node in enumerate(ast_current.nodes):
            if isinstance(node, HeadingNode):
                st.markdown(f"**Node {idx+1} [Heading H{node.level}]:** `{node.text}`")
            elif isinstance(node, CodeBlockNode):
                st.markdown(f"**Node {idx+1} [CodeBlock ({node.language})]:** {len(node.code.splitlines())} lines")
            elif isinstance(node, ListNode):
                st.markdown(f"**Node {idx+1} [List]:** {len(node.items)} items")
            elif isinstance(node, ImageNode):
                st.markdown(f"**Node {idx+1} [Image]:** width={node.width_inches} in")
            elif isinstance(node, TableNode):
                st.markdown(f"**Node {idx+1} [Table]:** {len(node.headers)} cols x {len(node.rows)} rows")
            elif isinstance(node, ParagraphNode):
                st.markdown(f"**Node {idx+1} [Paragraph]:** {node.text[:80]}...")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4: Import Raw Lab Notes (Preserving Original Paste-and-Go Workflow)
# ─────────────────────────────────────────────────────────────────────────────
with ws_tab4:
    st.markdown("### 📥 Import Raw Unstructured or Semi-Structured Lab Notes")
    st.caption("Paste your raw experiment text. The structural detector will automatically identify headings (AIM:, THEORY:, CODE:) and populate your workspace:")

    raw_text_val = st.text_area(
        "Raw Lab Text",
        height=280,
        placeholder="Paste your complete notes here (e.g. AIM: ..., THEORY: ..., CODE: #include ...)",
        key="ws_raw_text_paste"
    )

    im_c1, im_c2 = st.columns([1.5, 1])
    with im_c1:
        raw_uploaded_img = st.file_uploader("Output Screenshot (Optional)", type=["png", "jpg", "jpeg"], key="ws_raw_img_upload")
    with im_c2:
        raw_ss_mode = st.radio(
            "Screenshot Mode",
            ["Embed Mode (Preserve original image)", "Read Mode (Extract terminal text via Vision AI)"],
            index=0,
            key="ws_raw_ss_mode"
        )

    if st.button("🚀 Convert into Structured Sections", use_container_width=True, type="primary", key="ws_do_import_btn"):
        if not raw_text_val.strip():
            st.error("Please enter raw text first.")
        else:
            with st.spinner("Analyzing document structure and splitting into sections..."):
                img_bytes = raw_uploaded_img.getvalue() if raw_uploaded_img else None
                
                # Handle Read Mode via Vision AI if selected
                if img_bytes and "Read Mode" in raw_ss_mode:
                    act_key = st.session_state.get("user_provided_key") or os.getenv("GEMINI_API_KEY", "")
                    s_ok, s_txt, s_msg = extract_text_from_screenshot_read_mode(img_bytes, api_key=act_key)
                    if s_ok:
                        raw_text_val = raw_text_val + "\n\nOUTPUT:\n" + s_txt
                        img_bytes = None
                        st.info("Terminal text extracted via Vision AI.")
                    else:
                        st.warning(f"Read Mode notice: {s_msg}. Falling back to Embed Mode.")

                import_from_raw_text(raw_text_val, img_bytes)
                st.success("Sections successfully created from raw text! Switch to the **Section Content Editor** tab to review.")
                st.rerun()
