from fastapi import FastAPI
from pydantic import BaseModel
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()
# Initialize the OpenAI client
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Initialize the FastAPI app
app = FastAPI(
    title="AI Shadow Worker API",
    description="A backend for AI-powered log analysis and workflow detection",
    version="1.0.0"
)

# --- Schemas ---
class AnalyzeLogsRequest(BaseModel):
    log_data: str
    file_type: str = "text"

# --- System Prompt ---
SYSTEM_PROMPT = """You are a senior backend engineer and log analysis expert.

Analyze the system logs and extract workflow/debugging insights.

You MUST output ONLY valid JSON with no additional text, explanations, or formatting.

The JSON must contain EXACTLY these top-level keys:
- "workflows_detected": integer (number of distinct workflows found)
- "primary_workflow": object with:
    - "steps": array of SHORT action strings (e.g. "Download CSV", not full sentences)
    - "confidence_score": integer between 0 and 100
    - "estimated_time_saved_mins_per_week": integer > 0
    - "automation_suggestion": string (practical suggestion using Python, Pandas, Zapier, etc.)

Rules:
- Output ONLY JSON
- No markdown or explanations
- All fields are mandatory
- Steps must be SHORT action phrases, not full sentences
- If no clear repetition is found, set workflows_detected to 0 and confidence_score below 50
- Ensure confidence_score is higher (80+) when clear repetition is detected
"""

def _build_messages(log_data: str):
    user_prompt = f'Analyze the following log data and return JSON only:\n\n"""\n{log_data}\n"""'
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

async def _call_llm(log_data: str):
    messages = _build_messages(log_data)
    for attempt in range(3):
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.0,
            )
            raw = response.choices[0].message.content.strip()
            # Strip markdown code fences if the model added them
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            messages.append({"role": "user", "content": "PLEASE RESPOND WITH ONLY VALID JSON. No markdown."})
    raise Exception("LLM failed to return valid JSON after retries")

# --- Health Endpoint ---
@app.get("/")
async def root():
    return {"status": "success", "message": "Backend is running!"}

@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "message": "Backend is healthy"}

# --- Main Analyze Logs Endpoint ---
@app.post("/api/v1/analyze-logs")
async def analyze_logs(request: AnalyzeLogsRequest):
    # Empty input guard
    if not request.log_data or not request.log_data.strip():
        return {"status": "error", "message": "Invalid input"}

    # Limit input size
    log_data = request.log_data.strip()[:20_000]

    try:
        result = await _call_llm(log_data)
        return {"status": "success", "data": result}
    except json.JSONDecodeError:
        return {"status": "error", "message": "LLM response was not valid JSON. Please try again."}
    except Exception as e:
        return {"status": "error", "message": f"LLM request failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

