import fitz  # PyMuPDF
import re
import json
import time
from typing import List, Dict, Any
from app.utils.helpers import clean_text
from app.config import logger
from app.services.gemini_client import get_model

# Expanded predefined technology list for skill extraction
# Uses word-boundary matching for short keywords
TECH_KEYWORDS = {
    # Languages
    "python",
    "javascript",
    "typescript",
    "java",
    "c++",
    "c#",
    "go",
    "rust",
    "ruby",
    "php",
    "swift",
    "kotlin",
    "scala",
    "r",
    "dart",
    "lua",
    "perl",
    "haskell",
    "elixir",
    "clojure",
    # Frontend
    "react",
    "vue",
    "angular",
    "svelte",
    "next.js",
    "nuxt.js",
    "html",
    "css",
    "sass",
    "tailwind",
    "bootstrap",
    "flexbox",
    "css grid",
    "media queries",
    # Backend
    "node.js",
    "express",
    "fastapi",
    "flask",
    "django",
    "spring boot",
    "rails",
    "laravel",
    "asp.net",
    ".net",
    # Templating
    "ejs",
    "jinja2",
    "handlebars",
    # Databases
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "sqlite",
    "cassandra",
    "dynamodb",
    "elasticsearch",
    "neo4j",
    "sql",
    "rdbms",
    "database design",
    "oracle",
    # Cloud & DevOps
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "terraform",
    "ansible",
    "jenkins",
    "github actions",
    "ci/cd",
    "red hat",
    "bash",
    "nginx",
    # Data & ML
    "tensorflow",
    "pytorch",
    "pandas",
    "numpy",
    "scikit-learn",
    "spark",
    "kafka",
    "airflow",
    "mlflow",
    # NLP / text processing
    "tokenization",
    "n-gram",
    "jaccard similarity",
    # Auth & security
    "jwt",
    "bcrypt",
    # API tools
    "postman",
    "swagger",
    # C++ utilities
    "stl",
    # Algorithms & CS
    "data structures",
    "algorithms",
    "object-oriented programming",
    "system design",
    "design patterns",
    # Tools
    "git",
    "linux",
    "graphql",
    "rest api",
    "grpc",
}

# Skills that need word-boundary matching (too short / common substrings)
SHORT_SKILLS = {
    "go",
    "r",
    "c#",
    "c++",
    "sql",
    "css",
    "git",
    "lua",
    "gcp",
    "java",
    "ejs",
    "jwt",
    "stl",
}


def format_skill(skill):
    # Special casing for well-known formats
    special = {
        "node.js": "Node.js",
        "next.js": "Next.js",
        "nuxt.js": "Nuxt.js",
        "c++": "C++",
        "c#": "C#",
        "asp.net": "ASP.NET",
        ".net": ".NET",
        "aws": "AWS",
        "gcp": "GCP",
        "sql": "SQL",
        "css": "CSS",
        "html": "HTML",
        "graphql": "GraphQL",
        "grpc": "gRPC",
        "ci/cd": "CI/CD",
        "rest api": "REST API",
        "mlflow": "MLflow",
        "jwt": "JWT",
        "bcrypt": "Bcrypt",
        "ejs": "EJS",
        "stl": "STL",
        "rdbms": "RDBMS",
        "css grid": "CSS Grid",
        "media queries": "Media Queries",
        "flexbox": "CSS3 Flexbox",
        "n-gram": "N-Gram",
        "jaccard similarity": "Jaccard Similarity",
        "red hat": "Red Hat",
        "postman": "Postman",
        "oracle": "Oracle",
        "jinja2": "Jinja2",
        "swagger": "Swagger",
        "nginx": "Nginx",
        "bash": "Bash",
    }
    return special.get(skill.lower(), skill.title())


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
            text = file_content.decode("utf-8")
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
            pattern = r"\b" + re.escape(tech_lower) + r"\b"
            if re.search(pattern, text_lower):
                found_skills.add(tech)
        else:
            if tech_lower in text_lower:
                found_skills.add(tech)

    # Return formatted skills
    return [format_skill(skill) for skill in found_skills]


def extract_skills_with_llm(resume_text: str) -> list[str]:
    try:
        model = get_model()
        prompt = f"""Extract all technical skills from this resume. Include languages, frameworks, tools, cloud platforms, databases, certifications, and domain knowledge.
Return ONLY a valid JSON array of strings, no explanation, no markdown, no preamble.
Example: ["Python", "FastAPI", "Redis", "Docker"]

Resume:
{resume_text[:3000]}"""

        logger.info("[Gemini Call 1] Starting LLM skill extraction...")
        for attempt in range(3):
            try:
                response = model.generate_content(
                    prompt, generation_config={"temperature": 0.2}
                )
                logger.info(f"[Gemini Call 1] Success on attempt {attempt + 1}")
                try:
                    result = json.loads(response.text)
                except json.JSONDecodeError:
                    match = re.search(r"\[.*\]", response.text, re.DOTALL)
                    result = json.loads(match.group()) if match else []
                logger.info(f"[Gemini Call 1] Extracted {len(result)} skills via LLM")
                return result

            except Exception as e:
                is_timeout = "504" in str(e) or "timeout" in str(e).lower()
                if is_timeout and attempt < 2:
                    wait = 2**attempt
                    logger.warning(
                        f"[Gemini Call 1] Timeout on attempt {attempt + 1}, retrying in {wait}s..."
                    )
                    time.sleep(wait)
                    continue
                raise

    except Exception as e:
        logger.warning(f"[Gemini Call 1] Gemini skill extraction failed: {e}")
        return []


def parse_resume(file_content: bytes) -> Dict[str, Any]:
    """
    Main orchestrator for resume parsing.
    """
    logger.info("[Resume Parser] Starting resume parsing...")
    raw_text = extract_text(file_content)
    cleaned_text = clean_text(raw_text)
    logger.info(
        f"[Resume Parser] Extracted {len(cleaned_text)} chars of text from resume"
    )

    logger.info("[Resume Parser] Running keyword-based skill extraction...")
    skills = extract_skills(cleaned_text)
    logger.info(
        f"[Resume Parser] Keyword extraction found {len(skills)} skills: {skills}"
    )

    llm_skills = extract_skills_with_llm(cleaned_text)
    logger.info(f"[Resume Parser] LLM extraction returned {len(llm_skills)} skills")

    GENERIC_SKILLS = {
        "apis",
        "backend development",
        "software engineering",
        "web development",
        "programming",
        "development",
        "coding",
        "software",
        "technology",
        "technical skills",
    }

    llm_skills_filtered = [
        s
        for s in llm_skills
        if len(s.strip()) >= 2 and s.lower().strip() not in GENERIC_SKILLS
    ]
    logger.info(
        f"[Resume Parser] After filtering generic skills: {len(llm_skills_filtered)} LLM skills remain"
    )

    keyword_norm = {s.lower().strip(): s for s in skills}
    llm_norm = {s.lower().strip(): s for s in llm_skills_filtered}
    merged_norm = {**llm_norm, **keyword_norm}  # keyword casing wins on collision
    combined = [format_skill(v) for v in merged_norm.values()][:40]
    logger.info(f"[Resume Parser] Final merged skill list: {len(combined)} skills")

    return {"skills": combined, "text": cleaned_text}
