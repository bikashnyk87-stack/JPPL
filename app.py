import streamlit as st
import fitz  # PyMuPDF
import json
import pandas as pd
from datetime import datetime
from groq import Groq
import io

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="Jodhani Papers | Legal Auditor", 
    page_icon="⚖️", 
    layout="wide"
)

# Custom CSS to FORCE full text display and automatic row height
st.markdown("""
    <style>
    /* This forces the cells to wrap text and grow in height */
    div[data-testid="stDataTableBodyCell"] > div {
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
        display: block !important;
        line-height: 3 !important;
        height: auto !important;
        padding: 20px !important;
    }
    
    /* Ensures the dataframe container allows for larger rows */
    .stDataFrame [data-testid="stTable"] {
        height: auto !important;
    }

    .main-title { color: #1E88E5; font-size: 32px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADING ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    try: st.image("logo.png", width=450) # Adjusted width for better proportion
    except: st.markdown("### 🏢")
with col_title:
    st.markdown('<p class="main-title">Batch Legal Contract Auditor</p>', unsafe_allow_html=True)
    st.write("**Jodhani Papers Pvt. Ltd.**")

# --- 3. API INITIALIZATION ---
try:
    api_key = st.secrets["GROQ_API_KEY"]
except:
    api_key = "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"
client = Groq(api_key=api_key)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("📂 Document Center")
    uploaded_files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    user_instructions = st.text_area("Audit Focus:", value="Check for hidden penalties and jurisdiction.", height=100)
    selected_model = st.selectbox("AI Engine:", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"])
    run_audit = st.button("🚀 Start Batch Audit", type="primary", use_container_width=True)

# --- 5. LOGIC ---
def analyze_single_pdf(pdf_file, instructions, model):
    pdf_file.seek(0)
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = "".join([page.get_text() for page in doc])
    
    prompt = f"""
    Analyze for Jodhani Papers Pvt. Ltd. Instructions: {instructions}
    Return JSON: 
    'summary' (Detailed 3-4 sentences), 
    'checklist' (Detailed findings for Governing Law, Payment, Termination), 
    'top_risks' (Main risk description), 
    'risk_score' (1-10), 
    'status' (Safe/Warning/Critical).
    TEXT: {text[:15000]}
    """
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": "You are a Senior Lawyer. RESPOND ONLY IN JSON."},
                  {"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

# --- 6. DISPLAY RESULTS ---
if run_audit and uploaded_files:
    all_results = []
    progress_bar = st.progress(0)
    
    for i, file in enumerate(uploaded_files):
        with st.status(f"Auditing {file.name}...", expanded=False):
            try:
                res = analyze_single_pdf(file, user_instructions, selected_model)
                res['Filename'] = file.name
                all_results.append(res)
            except Exception as e:
                st.error(f"Error {file.name}: {e}")
        progress_bar.progress((i + 1) / len(uploaded_files))

    if all_results:
        df = pd.DataFrame(all_results)
        st.subheader("📊 Full Audit Report")

        # Use st.dataframe with a tall height to show all content
        st.dataframe(
            df,
            height=400, # Increased height to ensure more visible space
            column_config={
                "Filename": st.column_config.TextColumn("File Name", width="medium"),
                "status": st.column_config.TextColumn("Status", width="small"),
                "risk_score": st.column_config.NumberColumn("Score", format="%d ⭐"),
                "summary": st.column_config.TextColumn("Summary", width="large"),
                "checklist": st.column_config.TextColumn("Clause Checklist", width="large"),
                "top_risks": st.column_config.TextColumn("Primary Risk", width="medium"),
            },
            hide_index=True,
            use_container_width=True
        )

        # Download
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 Download Excel Report", output.getvalue(), "Jodhani_Audit_Report.xlsx", use_container_width=True)

