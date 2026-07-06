import os
import json
import time
from groq import Groq, APIConnectionError
from models import ObligationBase

GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_RETRIES = 3

# The prompt template for extraction
EXTRACTION_PROMPT = """
You are a regulatory compliance AI. Your job is to read the provided text chunks from a SEBI circular and extract all obligations imposed on stockbrokers.
Return the result strictly as a JSON list of objects matching this schema:
[
  {{
      "circular_name": "Name of the circular",
      "obligation_text": "Clear description of what must be done",
      "intermediary": "Who this applies to (e.g. stockbroker)",
      "deadline": "Deadline as an ISO date YYYY-MM-DD if the text gives or implies a specific calendar date, or null if it's open-ended/ongoing with no fixed date",
      "evidence_type": "What proof is needed to show compliance (e.g. policy document, board resolution)",
      "source_chunk": "A verbatim snippet of the text this came from"
  }}
]

Each numbered clause in the source text is exactly one obligation. Return exactly one JSON object per numbered clause — never split a single clause into multiple objects, and never duplicate the same clause into more than one object.

Do not include any other text in your response, only the JSON array.

Text to analyze:
{text_context}
"""

def extract_obligations(text_context: str, circular_name: str) -> list[ObligationBase]:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable is not set")

    prompt = EXTRACTION_PROMPT.format(text_context=text_context)
    client = Groq(api_key=api_key)

    response = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                temperature=0,
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            break
        except APIConnectionError as e:
            if attempt == MAX_RETRIES - 1:
                print(f"Extraction error (Groq connection failed after {MAX_RETRIES} attempts): {e}")
                return []
            time.sleep(1.5 * (attempt + 1))

    try:
        content = response.choices[0].message.content
        content = content.replace("```json", "").replace("```", "").strip()
        # Find JSON array in case there is surrounding text
        start_idx = content.find("[")
        end_idx = content.rfind("]") + 1
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx]
            data = json.loads(json_str)
            # Ensure circular name matches
            for item in data:
                if not item.get("circular_name") or item.get("circular_name") == "Name of the circular":
                    item["circular_name"] = circular_name
            return [ObligationBase(**item) for item in data]
        return []
    except Exception as e:
        print(f"Extraction error (Groq): {e}")
        return []
