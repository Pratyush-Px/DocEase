import fitz  # PyMuPDF
import re
from typing import List, Dict, Any
from app.utils.helpers import clean_text

# Expanded predefined technology list for skill extraction
# Uses word-boundary matching for short keywords
TECH_KEYWORDS = {
    # Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r", "dart", "lua",
    "perl", "haskell", "elixir", "clojure",
    # Frontend
    "react", "vue", "angular", "svelte", "next.js", "nuxt.js",
    "html", "css", "sass", "tailwind", "bootstrap",
    # Backend
    "node.js", "express", "fastapi", "flask", "django", "spring boot",
    "rails", "laravel", "asp.net", ".net",
    # Databases
    "postgresql", "mysql", "mongodb", "redis", "sqlite", "cassandra",
    "dynamodb", "elasticsearch", "neo4j", "sql",
    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
    "ansible", "jenkins", "github actions", "ci/cd",
    # Data & ML
    "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn",
    "spark", "kafka", "airflow", "mlflow",
    # Tools
    "git", "linux", "graphql", "rest api", "grpc",
}

# Skills that need word-boundary matching (too short / common substrings)
SHORT_SKILLS = {"go", "r", "c#", "c++", "sql", "css", "git", "lua", "gcp"}

def extract_text(file_content: bytes) -> str:
    """
    Extracts text from a PDF file using PyMuPDF.
    """
    text = ""
    try:
        pdf_document = fitz.open(stream=file_content, filetype="pdf")
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        pdf_document.close()
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        # Fallback if it's just a text file
        try:
            text = file_content.decode('utf-8')
        except UnicodeDecodeError:
            pass
    return text

def extract_skills(text: str) -> List[str]:
    """
    Extracts skills by matching predefined keywords.
    Uses word-boundary regex for short keywords to avoid false positives.
    """
    text_lower = text.lower()
    
    found_skills = set()
    for tech in TECH_KEYWORDS:
        tech_lower = tech.lower()
        if tech_lower in SHORT_SKILLS:
            # Use word-boundary for short/ambiguous terms
            pattern = r'\b' + re.escape(tech_lower) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(tech)
        else:
            if tech_lower in text_lower:
                found_skills.add(tech)
            
    # Return formatted skills
    def format_skill(skill):
        # Special casing for well-known formats
        special = {
            "node.js": "Node.js", "next.js": "Next.js", "nuxt.js": "Nuxt.js",
            "c++": "C++", "c#": "C#", "asp.net": "ASP.NET", ".net": ".NET",
            "aws": "AWS", "gcp": "GCP", "sql": "SQL", "css": "CSS",
            "html": "HTML", "graphql": "GraphQL", "grpc": "gRPC",
            "ci/cd": "CI/CD", "rest api": "REST API", "mlflow": "MLflow",
        }
        return special.get(skill.lower(), skill.title())
    
    return [format_skill(skill) for skill in found_skills]

def parse_resume(file_content: bytes) -> Dict[str, Any]:
    """
    Main orchestrator for resume parsing.
    """
    raw_text = extract_text(file_content)
    cleaned_text = clean_text(raw_text)
    skills = extract_skills(cleaned_text)
    
    return {
        "skills": skills,
        "text": cleaned_text
    }
