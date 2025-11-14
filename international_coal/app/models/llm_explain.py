import streamlit as st
import polars as pl
from dotenv import load_dotenv
import os
load_dotenv()

from google import genai

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

@st.cache_data
def explain_model_results(prompt: str, df: pl.DataFrame) -> genai.types.GenerateContentResponse:
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=f"{prompt}: {str(df)}"
    )
    return response