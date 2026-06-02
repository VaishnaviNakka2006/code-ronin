import os
import json
from groq import AsyncGroq
from app.schemas.ai_mission import AIMission, TestCase

# Initialize async Groq client
client = AsyncGroq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

PROMPT_TEMPLATE = """
You are a coding challenge generator for a cyberpunk game. Generate a Python programming mission.

Difficulty: {difficulty}
Topic: {topic}

Output a JSON object with:
- "title": string (cyberpunk style, max 60 chars)
- "description": string (clear problem statement, include example input/output if needed)
- "difficulty": string (easy, medium, hard)
- "test_cases": list of objects, each with "input" (string, could be empty) and "expected_output" (string, exact output expected from print statements)
- "code_stub": string (optional, initial code provided to user)

Rules:
- The user's code will be executed and its stdout compared to expected_output
- Test inputs (if any) are passed via stdin – but for Python functions, the test case will append code to call the function
- Keep each test case simple (one assertion)
- Provide at least 2 test cases
- Difficulty: easy -> basic syntax, medium -> loops/conditionals, hard -> functions/recursion
- Make the mission solvable in 5-10 lines of code

Return ONLY valid JSON.
"""

async def generate_mission(difficulty: str = "easy", topic: str = "general") -> dict:
    """Generate a mission using Groq's structured outputs for reliable JSON."""
    try:
        # Use Groq with json_object response format
        completion = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Supports json_object mode
            messages=[
                {
                    "role": "system",
                    "content": "You are a coding challenge generator. Output only valid JSON."
                },
                {
                    "role": "user",
                    "content": PROMPT_TEMPLATE.format(difficulty=difficulty, topic=topic)
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            timeout=15.0
        )
        
        content = completion.choices[0].message.content
        mission_dict = json.loads(content)
        validated = AIMission(**mission_dict)
        return validated.model_dump()
    
    except Exception as e:
        # Fallback to static mission
        return _fallback_mission(difficulty)

def _fallback_mission(difficulty: str) -> dict:
    """Static fallback mission when API call fails."""
    return {
        "title": "Legacy: Echo Chamber",
        "description": "Write a function `echo(text)` that returns the input text unchanged.",
        "difficulty": difficulty,
        "test_cases": [
            {"input": "echo('hello')", "expected_output": "hello"},
            {"input": "echo('cyber')", "expected_output": "cyber"}
        ],
        "code_stub": "def echo(text):\n    # Your code here\n    pass"
    }