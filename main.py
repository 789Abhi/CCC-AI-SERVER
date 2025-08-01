import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import json
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

logging.basicConfig(level=logging.INFO)
app = FastAPI()

origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


class PromptRequest(BaseModel):
    prompt: str


def extract_json(text):
    try:
        # Find the first and last curly braces
        start = text.find('{')
        end = text.rfind('}') + 1
        json_str = text[start:end]
        return json.loads(json_str)
    except Exception as e:
        logging.error(f"JSON extraction error: {e}")
        return None


@app.post("/generate-component")
async def generate_component(request: PromptRequest):
    try:
        system_message = {
            "role": "system",
            "content": (
                "You are a helpful assistant that generates only valid JSON output for React components. "
                "Respond with only JSON. Do not include explanations or extra text."
            )
        }

        user_message = {
            "role": "user",
            "content": (
                f"{request.prompt}\n\n"
                "Return only JSON in the following format:\n\n"
                '{\n'
                '  "componentName": "RegistrationForm",\n'
                '  "fields": [\n'
                '    {"name": "email", "type": "email"},\n'
                '    {"name": "password", "type": "password"}\n'
                '  ]\n'
                '}'
            )
        }

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[system_message, user_message],
            temperature=0.2,
        )

        output = response['choices'][0]['message']['content']
        logging.info(f"Model output:\n{output}")

        extracted = extract_json(output)
        if not extracted:
            raise ValueError("No valid JSON object found in model output.")

        return {"success": True, "data": extracted}

    except Exception as e:
        logging.error(f"Error in generation: {e}")
        return {"success": False, "error": str(e)}
