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
