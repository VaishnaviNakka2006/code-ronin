import os
import json
import asyncio
import time
from groq import AsyncGroq
from app.schemas.ai_mission import AIMission, TestCase

# Initialize async Groq client
client = AsyncGroq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

# Async-safe cache

_cache = {}

_cache_lock = asyncio.Lock()

CACHE_TTL_SECONDS = 300


def _make_cache_key(
    difficulty: str,
    topic: str
) -> str:
    return f"{difficulty}:{topic}"

PROMPT_TEMPLATE = """
You are generating Python coding missions.

Difficulty: {difficulty}
Topic: {topic}

Return ONLY valid JSON.

Rules:

1. Generate ONLY stdin/stdout problems.
2. User solutions will be executed as complete Python scripts.
3. Inputs are provided through input().
4. Outputs are validated using printed stdout.
5. NEVER generate functions like:
   def solve(...)
   def factorial(...)
6. NEVER ask the user to return values.
7. Every test case MUST match the mission description exactly.
8. At least 2 test cases.
9. Easy = print/input/basic if.
10. Medium = loops/conditions.
11. Hard = functions/recursion.

JSON format:

{{
  "title": "...",
  "description": "...",
  "difficulty": "...",
  "test_cases": [
    {{
      "input": "...",
      "expected_output": "..."
    }}
  ],
  "code_stub": "..."
}}
"""

async def generate_mission(
    difficulty: str = "easy",
    topic: str = "general"
) -> dict:

    key = _make_cache_key(
        difficulty,
        topic
    )

    async with _cache_lock:

        if key in _cache:

            mission_data, timestamp = _cache[key]

            if (
                time.time() - timestamp
                < CACHE_TTL_SECONDS
            ):

                print("CACHE HIT:", key)

                return mission_data

            else:

                del _cache[key]

    print("CACHE MISS:", key)

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
            temperature=0.2,
            timeout=15.0
        )
        
        content = completion.choices[0].message.content

        print("GROQ RESPONSE:", content)

        mission_dict = json.loads(content)
        for tc in mission_dict["test_cases"]:
            tc["expected_output"] = tc["expected_output"].strip()

        code_stub = mission_dict.get("code_stub", "")

        banned_patterns = [
            "def solve",
            "def factorial",
            "def echo",
            "return "
        ]

        if any(p in code_stub for p in banned_patterns):
            raise Exception("Function-based mission rejected")
            raise Exception("Function-based mission rejected")
        validated = AIMission(**mission_dict)

        result = validated.model_dump()

        async with _cache_lock:

            _cache[key] = (
                result,
                time.time()
            )

        return result
    
    except Exception as e:
        # Fallback to static mission
        print("GROQ ERROR:", e)
        return _fallback_mission(difficulty)

def _fallback_mission(difficulty: str) -> dict:
    return {
        "title": "Legacy: Neon Greeting",
        "description": "Read a name and print Hello, <name>!",
        "difficulty": difficulty,
        "test_cases": [
            {
                "input": "Neo",
                "expected_output": "Hello, Neo!"
            },
            {
                "input": "Trinity",
                "expected_output": "Hello, Trinity!"
            }
        ],
        "code_stub": (
            "name = input()\n"
            "# Your code here\n"
        )
    }