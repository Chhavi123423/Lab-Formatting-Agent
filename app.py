import streamlit as st
import io
import os
from src.preprocessor import clean_input_text
from src.heading_detector import extract_sections_with_llm_fallback
from src.content_detector import build_document_ast
from src.section_auditor import audit_missing_sections
from src.screenshot_processor import process_screenshot_embed, extract_text_from_screenshot_read_mode
from src.profiles import get_profile_by_name, get_university_practical_profile
from src.style_extractor import extract_formatting_rules_from_sample
from src.formatting_planner import create_formatting_plan
from src.docx_generator import generate_docx_from_plan
from src.validator import validate_generated_docx
from src.corrector import run_one_pass_correction
from src.models import HeadingNode, CodeBlockNode, ListNode, ImageNode, ParagraphNode


st.set_page_config(
    page_title="Lab File Formatting Agent",
    page_icon="📄",
    layout="wide"
)

# Custom header styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1F4E79;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.05rem;
        color: #555555;
        margin-bottom: 1.5rem;
    }
    .stButton>button {
        background-color: #1F4E79;
        color: white;
        font-weight: 600;
        font-size: 1rem;
        padding: 0.6rem 2rem;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📄 Lab File Formatting Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-assisted structural formatting engine — converts raw notes into standardized Word (.docx) lab reports.</div>', unsafe_allow_html=True)

# 1. Formatting Rule Mode Selection
st.markdown("### 🎨 Formatting Rules Source")
profile_mode = st.radio(
    "How would you like to define the formatting rules?",
    options=[
        "Use Curated Preset Profile (Built-in Rules)",
        "🪄 Upload Reference Document (Extract Rules Automatically with AI)"
    ],
    index=0,
    horizontal=True,
    help="Select a built-in template or let AI inspect an uploaded sample experiment (PDF/Image) to extract the rules."
)

active_profile = None
extracted_msg = None
server_api_key = os.getenv("GEMINI_API_KEY", "")

if "Extract Rules Automatically" in profile_mode:
    # Secure API Key Input (Bring Your Own Key Model)
    user_api_key = st.text_input(
        "🔑 Gemini API Key (Enter your own key or use server key if available)",
        type="password",
        value=st.session_state.get("user_provided_key", ""),
        placeholder="Enter your Gemini API key (AIzaSy...)",
        help="Get a free API key at https://aistudio.google.com. Your key remains strictly in your private browser session."
    )

    if user_api_key.strip():
        st.session_state["user_provided_key"] = user_api_key.strip()
        effective_user_key = user_api_key.strip()
        st.caption("🔒 *Using your private session key (isolated to your browser).*")
    elif server_api_key:
        effective_user_key = server_api_key
        st.caption("🔒 *Using server-configured environment key (hidden for security).*")
    else:
        effective_user_key = ""
        st.caption("ℹ️ *No API key detected. Get a 100% free key at [Google AI Studio](https://aistudio.google.com) to enable AI style extraction.*")

    ref_file = st.file_uploader(
        "Upload Reference Experiment Page (.pdf, .png, .jpg)",
        type=["pdf", "png", "jpg", "jpeg"],
        help="Upload 1 page of a completed practical file from your subject. AI will extract fonts, headers, and heading styles."
    )
    if ref_file:
        trigger_extract = (
            "last_ref_file" not in st.session_state 
            or st.session_state["last_ref_file"] != ref_file.name
            or st.session_state.get("last_used_key") != effective_user_key
        )
        if trigger_extract:
            with st.spinner("Analyzing document formatting with Vision AI..."):
                file_bytes = ref_file.getvalue()
                success, profile_data, msg = extract_formatting_rules_from_sample(
                    file_bytes, 
                    ref_file.name,
                    api_key=effective_user_key
                )
                st.session_state["extracted_profile"] = profile_data
                st.session_state["extracted_msg"] = msg
                st.session_state["last_ref_file"] = ref_file.name
                st.session_state["last_used_key"] = effective_user_key

        active_profile = st.session_state.get("extracted_profile", get_university_practical_profile())
        extracted_msg = st.session_state.get("extracted_msg", "")
        
        st.success(f"✅ {extracted_msg}")
        with st.expander("🔍 View Extracted Formatting Rules", expanded=False):
            st.json({
                "Profile Name": active_profile.get("profile_name"),
                "Font Family": active_profile.get("typography", {}).get("font_family"),
                "Color Scheme": active_profile.get("typography", {}).get("primary_color_rgb"),
                "Header Layout": active_profile.get("typography", {}).get("header", {}).get("layout"),
                "Inline Headings": active_profile.get("inline_headings"),
                "Block Headings": active_profile.get("block_headings"),
            })
    else:
        st.info("ℹ️ Upload a sample file above, or the system will default to University Practical File rules.")
        active_profile = get_university_practical_profile()
else:
    # Preset Mode
    preset_choice = st.selectbox(
        "Choose Built-in Profile",
        options=[
            "University Practical File (CIC-351 / Times New Roman / Split Header)",
            "Standard Academic Lab Profile (Calibri / Navy Accent / Boxed Code)"
        ],
        index=0
    )
    active_profile = get_profile_by_name(preset_choice)

# Pre-fill metadata from extracted profile if available
detected_header_left = active_profile.get("typography", {}).get("header", {}).get("left_text", "")
detected_header_right = active_profile.get("typography", {}).get("header", {}).get("right_text", "")

st.markdown("### 📋 Student & Lab Metadata")
col_meta1, col_meta2, col_meta3 = st.columns(3)
with col_meta1:
    subject_name = st.text_input(
        "Subject / Lab File Name",
        value=detected_header_left or "CD PRACTICAL FILE",
        placeholder="e.g. CD PRACTICAL FILE"
    )
    student_name = st.text_input("Student Name", value="Chhavi Choudhary", placeholder="e.g. Chhavi Choudhary")
with col_meta2:
    subject_code = st.text_input(
        "Subject / Course Code",
        value=detected_header_right or "CIC-351",
        placeholder="e.g. CIC-351"
    )
    class_section = st.text_input("Class / Section", value="IT-2", placeholder="e.g. IT-2")
with col_meta3:
    roll_number = st.text_input("Roll Number", value="19", placeholder="e.g. 19")

st.markdown("### 📝 Paste Raw Lab Content")
default_placeholder = (
    "EXPERIMENT-3\n\n"
    "AIM: Write a C++ program to check whether a given string is grammar or not\n\n"
    "THEORY: A grammar in formal language theory is a set of production rules used to generate strings belonging to a particular language.\n\n"
    "A grammar is generally represented as:\n"
    "G = (V, T, P, S)\n"
    "Where:\n"
    "V → Set of variables/non-terminals\n"
    "T → Set of terminals\n"
    "P → Set of production rules\n"
    "S → Start symbol\n"
    "For a simple grammar such as:\n"
    "S → aSb | abS\n\n"
    "CODE:\n"
    "#include <iostream>\n"
    "#include <string>\n"
    "using namespace std; \n"
    "int main()\n"
    "{\n"
    "    string str;\n"
    "    cout << \"Enter a string: \";\n"
    "    cin >> str;\n"
    "    int n = str.length();\n"
    "    if (n % 2 != 0)\n"
    "    {\n"
    "        cout << \"String is NOT generated by the grammar.\"; \n"
    "        return 0;\n"
    "    }\n"
    "    int half = n / 2;\n"
    "    for (int i = 0; i < half; i++)\n"
    "    {\n"
    "        if (str[i] != 'a')\n"
    "        {\n"
    "            cout << \"String is NOT generated by the grammar.\";\n"
    "            return 0;\n"
    "        }\n"
    "    }\n"
    "    for (int i = half; i < n; i++)\n"
    "    {\n"
    "        if (str[i] != 'b')\n"
    "        {\n"
    "            cout << \"String is NOT generated by the grammar.\";\n"
    "            return 0;\n"
    "        }\n"
    "    }\n"
    "    cout << \"String is generated by the grammar.\";\n"
    "    return 0;\n"
    "}\n\n"
    "OUTPUT:\n"
    "Enter a string: aaabbb\n"
    "String is generated by the grammar."
)

raw_text_input = st.text_area(
    "Paste your complete unstructured or semi-structured lab report text:",
    value=default_placeholder,
    height=320,
    help="You can paste all sections together. The agent detects inline headings (AIM:), block headings (CODE:), lists, and images."
)

col_img1, col_img2 = st.columns([1.5, 1])
with col_img1:
    uploaded_image = st.file_uploader(
        "Output Screenshot (Optional)",
        type=["png", "jpg", "jpeg"],
        help="Upload terminal or execution window screenshot"
    )
with col_img2:
    screenshot_mode = st.radio(
        "Screenshot Mode",
        options=["Embed Mode (Preserve original image)", "Read Mode (Extract terminal text via Vision AI)"],
        index=0,
        help="Embed mode resizes and centers the screenshot. Read mode uses Gemini Vision to extract terminal text verbatim."
    )

generate_btn = st.button("🚀 Generate Lab File (.docx)")

if generate_btn:
    if not raw_text_input.strip():
        st.error("Please enter raw lab text before generating.")
    else:
        with st.spinner("Processing document structure and formatting..."):
            # 1. Clean Input
            cleaned_text = clean_input_text(raw_text_input)

            # 2. Heading & Section Detection
            raw_sections = extract_sections_with_llm_fallback(cleaned_text)

            # 3. Screenshot Processing
            image_bytes = uploaded_image.getvalue() if uploaded_image else None
            is_read_mode = "Read Mode" in screenshot_mode
            read_warning = None

            if image_bytes and is_read_mode:
                active_api_key = (
                    st.session_state.get("user_provided_key") 
                    or st.session_state.get("gemini_api_key") 
                    or os.getenv("GEMINI_API_KEY", "")
                )
                success, extracted_text, msg = extract_text_from_screenshot_read_mode(image_bytes, api_key=active_api_key)
                if success:
                    output_found = False
                    for sec in raw_sections:
                        if sec["heading"].upper() in ["OUTPUT", "SCREENSHOT"]:
                            sec["content"] = (sec["content"] + "\n\n" + extracted_text).strip()
                            output_found = True
                            break
                    if not output_found:
                        raw_sections.append({
                            "heading": "OUTPUT",
                            "level": 1,
                            "content": extracted_text,
                            "confidence": 1.0
                        })
                    image_bytes = None
                else:
                    read_warning = msg
                    is_read_mode = False

            mode_str = "read" if is_read_mode else "embed"

            # 4. AST Construction
            ast = build_document_ast(
                raw_sections=raw_sections,
                subject_name=subject_name,
                subject_code=subject_code,
                student_name=student_name,
                roll_number=roll_number,
                class_section=class_section,
                raw_input_text=cleaned_text,
                uploaded_image_bytes=image_bytes,
                image_mode=mode_str
            )

            # 5. Missing Section Auditor (Warnings only, strictly no fabrication)
            missing_warnings = audit_missing_sections(ast)

            # 6. Apply Active Profile & Formatting Planner
            formatting_plan = create_formatting_plan(ast, custom_profile=active_profile)

            # 7. DOCX Generation
            initial_docx_bytes = generate_docx_from_plan(formatting_plan)

            # 8. Validation
            validation_result = validate_generated_docx(initial_docx_bytes, ast)

            # 9. One-Pass Correction Loop
            final_docx_bytes, final_validation = run_one_pass_correction(
                initial_docx_bytes,
                validation_result,
                ast,
                formatting_plan
            )

        # Presentation of Results
        st.divider()
        st.subheader("📊 Document Analysis & Validation")

        c_stat1, c_stat2, c_stat3 = st.columns(3)
        with c_stat1:
            st.metric("Detected Sections", len(raw_sections))
        with c_stat2:
            st.metric("Total AST Nodes", len(ast.nodes))
        with c_stat3:
            st.metric("Validation Status", final_validation.status)

        # Section List Display
        with st.expander("🔍 Detected Section Hierarchy", expanded=True):
            for sec in raw_sections:
                lvl = sec.get("level", 1)
                is_inl = sec.get("is_inline", False)
                type_tag = " (Inline)" if is_inl else ""
                prefix = "📁 H1: " if lvl == 1 else ("  📂 H2: " if lvl == 2 else "    📄 H3: ")
                st.write(f"**{prefix}{sec['heading']}**{type_tag}")

        # Warnings Section
        if missing_warnings or read_warning:
            st.warning("⚠️ **Notice / Warnings:**")
            if read_warning:
                st.info(f"📸 Screenshot Notice: {read_warning}")
            for w in missing_warnings:
                st.write(f"- {w}")
            st.caption("ℹ️ *Rule Enforced: The agent is a formatter and will never fabricate academic content for missing sections.*")

        # Validation Diagnostic Details
        if final_validation.status == "PASS":
            profile_label = active_profile.get("profile_name", "CUSTOM_PROFILE")
            st.success(f"✅ **Validation: PASS** — Formatting verified against '{profile_label}'.")
            if final_validation.correction_attempted:
                st.info("ℹ️ Note: Automatic one-pass correction successfully resolved initial formatting warnings.")
        else:
            st.error("❌ **Validation Issues Detected:**")
            for issue in final_validation.issues:
                st.write(f"- **{issue.rule_name}**: {issue.message}")

        # Download Section
        st.divider()
        safe_subject = (subject_code or "lab").replace(" ", "_")
        doc_filename = f"{safe_subject}_{roll_number or 'file'}.docx"
        st.download_button(
            label="📥 Download Formatted Lab File (.docx)",
            data=final_docx_bytes,
            file_name=doc_filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

        # Content Inspector Tab
        with st.expander("📑 Node Inspector (Abstract Syntax Tree)"):
            for idx, node in enumerate(ast.nodes):
                if isinstance(node, HeadingNode):
                    inl_badge = " [Inline]" if node.is_inline else ""
                    st.markdown(f"**Node {idx+1} [Heading H{node.level}]{inl_badge}:** `{node.text}`")
                    if node.is_inline and node.inline_text:
                        st.caption(f"↳ Inline Text: {node.inline_text[:80]}...")
                elif isinstance(node, CodeBlockNode):
                    st.markdown(f"**Node {idx+1} [CodeBlock ({node.language})]:**")
                    st.code(node.code, language=node.language)
                elif isinstance(node, ListNode):
                    st.markdown(f"**Node {idx+1} [List ({'Ordered' if node.is_ordered else 'Unordered'})]:** {len(node.items)} items")
                elif isinstance(node, ImageNode):
                    st.markdown(f"**Node {idx+1} [Image ({node.mode})]:** width={node.width_inches} in")
                elif isinstance(node, ParagraphNode):
                    st.markdown(f"**Node {idx+1} [Paragraph]:** {node.text[:80]}...")
