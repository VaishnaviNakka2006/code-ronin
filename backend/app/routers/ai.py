from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(
    prefix="/ai",
    tags=["ai"]
)

class ErrorContext(BaseModel):
    error_message: str
    code_snippet: str

@router.post("/hint")
async def get_hint(context: ErrorContext):

    error = context.error_message.lower()
    code = context.code_snippet.lower()

    if "indent" in error:
        return {
            "hint":
            "Indentation issue detected. Python requires proper spacing."
        }

    if "nameerror" in error:
        return {
            "hint":
            "A variable is being used before being defined."
        }

    if "syntax" in error:
        return {
            "hint":
            "Syntax error detected. Check brackets, quotes, or colons."
        }

    if "for" not in code and "range" not in code:
        return {
            "hint":
            "Try using a loop with range()."
        }

    if "print" not in code:
        return {
            "hint":
            "You may need to print the result."
        }

    return {
        "hint":
        "Review your logic carefully and debug step-by-step."
    }