# app/services/action_plan_service.py
from app.services.gemini_client import get_model
from app.config import logger


def generate_action_plan_llm(
    title: str, description: str, repo: str, skills: list[str]
) -> str:
    try:
        model = get_model()

        prompt = f"""
        You are an expert Open Source Engineering Mentor. 
        A developer is preparing to contribute to the '{repo}' repository.
        
        Their technical skills: {', '.join(skills[:20])}
        
        The GitHub Issue they want to solve:
        Title: {title}
        Description: {description[:1500]} # Trimmed to avoid token limits
        
        Write a concise, encouraging, and highly technical Step-by-Step Action Plan for them in Markdown.
        Structure it exactly like this:
        
        ### 🎯 Objective
        (One sentence summary of the goal)
        
        ### 📂 Where to Look
        (Guess which types of files or directories they should investigate first, based on the framework/repo)
        
        ### 🛠️ Recommended Approach
        (3-4 technical steps to solve it, keeping their specific skill set in mind)
        
        ### 💬 What to ask the Maintainer
        (Provide a polite, professional 1-2 sentence template they can copy-paste as a GitHub comment to claim the issue or ask for clarification)
        """

        response = model.generate_content(
            prompt, generation_config={"temperature": 0.4}
        )
        return response.text

    except Exception as e:
        logger.error(f"Failed to generate action plan: {e}")
        return "Failed to generate action plan. Please try again later."
