from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
import re
import logging

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Allow all CORS origins (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model name (can change to gpt2, gpt2-medium etc.)
model_name = "distilgpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Set pad token if missing (needed for sampling)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_name": model_name
    }

# Request model
class PromptRequest(BaseModel):
    prompt: str

# Helper function to extract valid JSON
def extract_json(text: str) -> dict:
    try:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if not json_match:
            raise ValueError("No valid JSON found")
        json_str = json_match.group(0)
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"JSON extraction error: {e}")
        raise HTTPException(status_code=500, detail="Invalid JSON format from model")

# Main generation endpoint
@app.post("/generate-component")
async def generate_component(data: PromptRequest):
    try:
        # Prompt template
        prompt = (
            f"Generate a React component in JSON format for the following task:\n"
            f"{data.prompt}\n\n"
            f"Response format:\n"
            f'{{"componentName": "", "fields": [{{"name": "", "type": ""}}]}}\n\n'
            f"Output:\n"
        )

        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
            num_return_sequences=1
        )

        response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"Model output: {response_text}")

        # Extract valid JSON
        result = extract_json(response_text)
        return result

    except Exception as e:
        logger.error(f"Error in generation: {e}")
        raise HTTPException(status_code=500, detail="Component generation failed")
