import os
import streamlit as st

def set_anthropic_key():
    try:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        from dotenv import load_dotenv
        load_dotenv()
