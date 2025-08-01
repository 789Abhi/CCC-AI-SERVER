from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline, set_seed
import logging
import json
import re

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

generator = pipeline("text-generation", model="distilgpt2")
set_seed(42)

class PromptRequest(BaseModel):
    prompt: str

@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": True, "model_name": "distilgpt2"}

@app.post("/generate-component")
async def generate_component(request: PromptRequest):
    prompt = f"""
Generate a React component schema in JSON format for the following task:

{request.prompt}

Format:
{{
  "componentName": "ComponentName",
  "fields": [
    {{
      "name": "field1",
      "type": "text"
    }},
    {{
      "name": "field2",
      "type": "password"
    }}
  ]
}}

Only return a valid JSON.
"""
    try:
        logger.info("Generating model output for prompt: %s", request.prompt)
        output = generator(prompt, max_length=300, num_return_sequences=1)[0]['generated_text']
        logger.info("Model output: %s", output)

        json_matches = re.findall(r'\{[\s\S]*\}', output)
        for match in json_matches:
            try:
                parsed = json.loads(match)
                return {"success": True, "component": parsed}
            except json.JSONDecodeError:
                continue
        raise ValueError("No valid JSON object found in model output.")

    except Exception as e:
        logger.error("Error in generation: %s", e)
        return {"success": False, "error": str(e)}
