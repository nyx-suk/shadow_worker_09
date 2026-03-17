import os
from openai import OpenAI
from dotenv import load_dotenv

# Load `.env` file containing OPENAI_API_KEY
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_KEY_HERE")
)

SYSTEM_PROMPT = """You are a workflow analyzer.

Analyze the workflow provided by the user and return a structured evaluation.

You MUST output ONLY valid JSON with no additional text, explanations, or formatting.

The JSON must contain exactly the following keys:
- "steps": an array of strings describing the workflow steps in order
- "confidence_score": a number between 0 and 1
- "time_saved": a percentage string (e.g., "30%")
- "recommendations": an array of actionable suggestions

Rules:
- Output ONLY JSON
- No markdown or explanations
- All fields are mandatory
- Ensure correct data types
- If the input is unclear, make reasonable assumptions and proceed"""

USER_PROMPT = """Analyze this workflow:
"I download reports from emails, copy data into Excel, clean it, and create weekly reports."
"""

try:
    print("Calling OpenAI API to test the prompt...\n")
    response = client.chat.completions.create(
        model="gpt-4o",  # or "gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT}
        ],
        temperature=0.0 # Make response deterministic
    )

    print("--- API Response ---")
    print(response.choices[0].message.content)
    print("--------------------")

except Exception as e:
    print(f"Error during API call: {e}\n(Did you replace the API key?)")
