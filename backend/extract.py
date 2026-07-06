import os
import json
import anthropic
import ollama
from models import ObligationBase

# The prompt template for extraction
EXTRACTION_PROMPT = """
You are a regulatory compliance AI. Your job is to read the provided text chunks from a SEBI circular and extract all obligations imposed on stockbrokers.
Return the result strictly as a JSON list of objects matching this schema:
[
  {{
      "circular_name": "Name of the circular",
      "obligation_text": "Clear description of what must be done",
      "intermediary": "Who this applies to (e.g. stockbroker)",
      "deadline": "Date or timeframe, or null if none",
      "evidence_type": "What proof is needed to show compliance (e.g. policy document, board resolution)",
      "source_chunk": "A verbatim snippet of the text this came from"
  }}
]

Do not include any other text in your response, only the JSON array.

Text to analyze:
{text_context}
"""

def extract_obligations(text_context: str, circular_name: str) -> list[ObligationBase]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    prompt = EXTRACTION_PROMPT.format(text_context=text_context)
    
    if api_key and api_key.strip() != "":
        return _extract_with_anthropic(prompt, api_key, circular_name)
    else:
        return _extract_with_ollama(prompt, circular_name)

def _extract_with_anthropic(prompt: str, api_key: str, circular_name: str) -> list[ObligationBase]:
    client = anthropic.Anthropic(api_key=api_key)
    
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=2000,
        temperature=0,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    try:
        content = response.content[0].text
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
        print(f"Extraction error (Anthropic): {e}")
        return []

def _extract_with_ollama(prompt: str, circular_name: str) -> list[ObligationBase]:
    try:
        response = ollama.chat(
            model='llama3',
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0}
        )
        content = response['message']['content']
        content = content.replace("```json", "").replace("```", "").strip()
        
        start_idx = content.find("[")
        end_idx = content.rfind("]") + 1
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx]
            data = json.loads(json_str)
            for item in data:
                if not item.get("circular_name") or item.get("circular_name") == "Name of the circular":
                    item["circular_name"] = circular_name
            return [ObligationBase(**item) for item in data]
        return []
    except Exception as e:
        print(f"Extraction error (Ollama): {e}")
        return []
