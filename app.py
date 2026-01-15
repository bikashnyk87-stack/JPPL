import streamlit as st
import fitz  # PyMuPDF
import json
import pandas as pd
from datetime import datetime
from groq import Groq
import io
from PIL import Image # For image handling

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="2026 Batch Legal Auditor", layout="wide")

# --- ADDING IMAGE TO HEADING ---
# Option A: Logo from a URL (e.g., your website)
# logo_url = "https://yourwebsite.com/logo.png"
# st.image(logo_url, width=200)

# Option B: Logo from your GitHub folder (Upload 'logo.png' to your repo)
try:
    logo = Image.open("logo.png")
    st.image(logo, width=150)
except:
    st.info("💡 Tip: Upload a file named 'logo.png' to your GitHub to show your company logo here.")

st.title("🛡️ Batch Legal Contract Auditor")
st.subheader("Jodhani Papers Pvt. Ltd.")
st.markdown("---") # Adds a horizontal line
import streamlit as st
import fitz  # PyMuPDF
import json
import pandas as pd
from datetime import datetime
from groq import Groq
import io

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="2026 Batch Legal Auditor", layout="wide")
st.title("🛡️ Batch Legal Contract Auditor_JPPL")
st.markdown("Upload multiple PDFs to generate a combined risk report.")

# Initialize Groq Client
client = Groq(api_key="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")

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    # Allow multiple files
    uploaded_files = st.file_uploader("Upload Contracts (PDF)", type="pdf", accept_multiple_files=True)
    
    user_instructions = st.text_area(
        "Audit Instructions:",
        value="Identify liability limits, termination notice, and AI data usage.",
        height=150
    )
    
    selected_model = st.selectbox("AI Engine:", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"])
    
    run_audit = st.button("🚀 Run Batch Audit", type="primary")

# --- 3. PROCESSING LOGIC ---
def analyze_single_pdf(pdf_file, instructions, model):
    pdf_file.seek(0)
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = "".join([page.get_text() for page in doc])
    
    if not text.strip():
        return {"summary": "Empty/Scanned PDF", "top_risks": "N/A", "risk_score": 0, "compliance_status": "Manual Review"}

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": f"You are a Legal Expert. Instructions: {instructions}. RESPOND ONLY IN JSON."},
            {"role": "user", "content": f"Return JSON: 'summary', 'top_risks', 'risk_score', 'compliance_status'. \n\nTEXT: {text[:12000]}"}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

# --- 4. EXECUTION & RESULTS ---
if run_audit and uploaded_files:
    all_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, file in enumerate(uploaded_files):
        status_text.text(f"Processing {i+1} of {len(uploaded_files)}: {file.name}...")
        try:
            analysis = analyze_single_pdf(file, user_instructions, selected_model)
            analysis['Filename'] = file.name
            analysis['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            all_results.append(analysis)
        except Exception as e:
            st.error(f"Error processing {file.name}: {e}")
        
        progress_bar.progress((i + 1) / len(uploaded_files))

    # --- 5. COMBINED REPORT ---
    if all_results:
        status_text.success(f"✅ Successfully audited {len(all_results)} contracts!")
        df = pd.DataFrame(all_results)
        
        # Display the combined table
        st.subheader("📊 Combined Audit Report")
        st.dataframe(df, use_container_width=True)
        
        # Create Excel Download in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Audit_Summary')
        processed_data = output.getvalue()

        st.download_button(
            label="📥 Download Master Excel Report",
            data=processed_data,
            file_name=f"Master_Audit_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
elif run_audit:
    st.warning("Please upload at least one PDF file.")

