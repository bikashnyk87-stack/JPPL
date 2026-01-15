import streamlit as st
import fitz  # PyMuPDF
import json
import pandas as pd
from datetime import datetime
from groq import Groq
import io
from PIL import Image

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Jodhani Papers | Legal Auditor", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. BEAUTIFUL STYLING (CSS) ---
st.markdown("""
    <style>
    /* Main Theme Colors */
    :root { --primary-color: #1E88E5; }
    
    .main-title { 
        color: #1E88E5; 
        font-size: 36px; 
        font-weight: 800; 
        margin-bottom: 0px;
    }
    
    .company-name {
        color: #555;
        font-size: 18px;
        font-weight: 400;
        margin-top: -10px;
    }

    /* Force text wrapping in dataframes for mobile readability */
    div[data-testid="stDataTableBodyCell"] {
        white-space: normal !important;
        word-wrap: break-word !important;
    }

    /* Custom sidebar style */
    [data-testid="stSidebar"] {
        background-color: #f0f2f6;
    }
    
    /* Risk Score Badge styling */
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGO & HEADING ---
col_logo, col_title = st.columns([1, 5])

with col_logo:
    try:
        # Upload 'logo.png' to your GitHub repo root for this to show
        st.image("logo.png", width=100)
    except:
        st.markdown("### 🏢")

with col_title:
    st.markdown('<p class="main-title">Batch Legal Contract Auditor</p>', unsafe_allow_html=True)
    st.markdown('<p class="company-name">Jodhani Papers Pvt. Ltd.</p>', unsafe_allow_html=True)

st.markdown("---")

# --- 4. SECURE API INITIALIZATION ---
try:
    # This works once you set it up in Streamlit Cloud Settings > Secrets
    api_key = st.secrets["GROQ_API_KEY"]
except:
    # Fallback for your local testing
    api_key = "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"

client = Groq(api_key=api_key)

# --- 5. SIDEBAR: UPLOAD & RULES ---
with st.sidebar:
    st.header("📂 Document Center")
    uploaded_files = st.file_uploader("Drop PDFs here", type="pdf", accept_multiple_files=True)
    
    st.subheader("📝 Audit Focus")
    user_instructions = st.text_area(
        "Additional Instructions:",
        value="Check for hidden penalties, automatic renewals, and jurisdiction.",
        height=100
    )
    
    selected_model = st.selectbox("AI Intelligence Level:", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"])
    
    st.divider()
    run_audit = st.button("🚀 Start Batch Analysis", type="primary", use_container_width=True)

# --- 6. ADVANCED AUDIT LOGIC ---
def analyze_single_pdf(pdf_file, instructions, model):
    pdf_file.seek(0)
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = "".join([page.get_text() for page in doc])
    
    if not text.strip():
        return {"summary": "Empty/Scanned PDF", "checklist": "N/A", "risk_score": 0, "status": "Error"}

    # Comprehensive Prompt with Checklist
    prompt = f"""
    Analyze this legal document for Jodhani Papers Pvt. Ltd. 
    Instructions: {instructions}
    
    You must return a JSON object with exactly these keys:
    1. 'summary': A 2-sentence executive summary.
    2. 'checklist': A bulleted list checking for: 
       - Governing Law (Found/Not Found)
       - Payment Terms (Found/Not Found)
       - Termination Clause (Found/Not Found)
       - Indemnity (Found/Not Found)
    3. 'top_risks': The single biggest risk identified.
    4. 'risk_score': 1 to 10 (10 being most dangerous).
    5. 'status': (Safe / Warning / Critical)

    TEXT: {text[:15000]}
    """

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a Senior Corporate Lawyer. RESPOND ONLY IN JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

# --- 7. RESULTS DISPLAY ---
if run_audit and uploaded_files:
    all_results = []
    progress_bar = st.progress(0)
    
    for i, file in enumerate(uploaded_files):
        with st.status(f"Auditing: {file.name}", expanded=False) as status:
            try:
                analysis = analyze_single_pdf(file, user_instructions, selected_model)
                analysis['Filename'] = file.name
                all_results.append(analysis)
                status.update(label=f"✅ {file.name} Audited", state="complete")
            except Exception as e:
                st.error(f"Failed {file.name}: {str(e)}")
        
        progress_bar.progress((i + 1) / len(uploaded_files))

    if all_results:
        st.balloons()
        df = pd.DataFrame(all_results)

        # Rearrange columns for better reading
        cols = ['Filename', 'status', 'risk_score', 'summary', 'checklist', 'top_risks']
        df = df[cols]

        st.subheader("📊 Master Audit Table")
        
        # Interactive & Mobile Responsive Table
        st.dataframe(
            df,
            column_config={
                "Filename": st.column_config.TextColumn("File Name", width="medium"),
                "status": st.column_config.SelectboxColumn("Status", options=["Safe", "Warning", "Critical"]),
                "risk_score": st.column_config.ProgressColumn("Risk Level", min_value=0, max_value=10, format="%d"),
                "summary": st.column_config.TextColumn("Executive Summary", width="large"),
                "checklist": st.column_config.TextColumn("Clause Checklist", width="large"),
                "top_risks": st.column_config.TextColumn("Primary Risk", width="medium"),
            },
            hide_index=True,
            use_container_width=True
        )

        # --- 8. EXCEL EXPORT ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Audit_Report')
            # Optional: Add formatting to Excel here if needed
            
        st.download_button(
            label="📥 Download Master Excel Audit Report",
            data=output.getvalue(),
            file_name=f"Jodhani_Audit_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
elif run_audit:
    st.warning("⚠️ Please upload PDF files in the sidebar first.")
