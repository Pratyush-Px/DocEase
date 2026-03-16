import re

def clean_text(text: str) -> str:
    """
    Cleans text by removing extra whitespaces and special characters.
    """
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,-]', '', text)
    return text.strip()
