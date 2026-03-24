import google.generativeai as genai
from app.config import settings

genai.configure(api_key=settings.gemini_api_key)

def get_model(model_name: str = "gemini-2.5-flash") -> genai.GenerativeModel:
    return genai.GenerativeModel(model_name)
