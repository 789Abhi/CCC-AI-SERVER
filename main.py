from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json
import logging
from typing import List, Optional
import os
import gc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CCC AI Server",
    description="AI-powered component generator for Custom Craft Component plugin",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
model = None
tokenizer = None

# Pydantic models
class ComponentRequest(BaseModel):
    prompt: str
    available_fields: Optional[List[str]] = [
        "text", "textarea", "image", "video", "color", 
        "select", "checkbox", "radio", "wysiwyg", "repeater"
    ]

class Field(BaseModel):
    label: str
    name: str
    type: str
    required: bool = False
    placeholder: str = ""
    config: Optional[dict] = None

class Component(BaseModel):
    name: str
    handle: str
    description: str = ""

class ComponentResponse(BaseModel):
    component: Component
    fields: List[Field]
    success: bool = True
    message: str = "Component generated successfully"

def cleanup_memory():
    """Clean up memory after generation"""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

@app.on_event("startup")
async def load_model():
    """Load a very small and efficient model"""
    global model, tokenizer
    
    try:
        logger.info("Loading distilgpt2 model...")
        model_name = "distilgpt2"
        cache_dir = os.environ.get("HF_HOME", None)
        tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            device_map="cpu"
        )
        logger.info("distilgpt2 model loaded successfully!")
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise e

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CCC AI Server is running!",
        "model": "distilgpt2",
        "endpoints": {
            "health": "/health",
            "generate": "/generate-component"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_name": "distilgpt2"
    }

@app.post("/generate-component", response_model=ComponentResponse)
async def generate_component(request: ComponentRequest):
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="AI model not loaded")
    
    try:
        logger.info(f"Generating component for prompt: {request.prompt}")

        system_prompt = f"""<|system|>
You are a WordPress component generator. Create a component based on the user's request.
Available field types: {', '.join(request.available_fields)}

Return only valid JSON in this format:
{{
    "component": {{
        "name": "Component Name",
        "handle": "component_handle",
        "description": "Description"
    }},
    "fields": [
        {{
            "label": "Field Label",
            "name": "field_name",
            "type": "field_type",
            "required": true/false,
            "placeholder": "Placeholder"
        }}
    ]
}}
</s>
<|user|>
{request.prompt}
</s>
<|assistant|>"""

        inputs = tokenizer(system_prompt, return_tensors="pt", max_length=256, truncation=True)
        
        logger.info("Starting model.generate()")
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=150,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
                num_return_sequences=1
            )
        logger.info("model.generate() completed")

        response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"Response text: {response_text}")

        cleanup_memory()
        
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in AI response")
        
        json_str = response_text[json_start:json_end]
        result = json.loads(json_str)
        
        component_data = result.get("component", {})
        fields_data = result.get("fields", [])
        
        component = Component(
            name=component_data.get("name", "Generated Component"),
            handle=component_data.get("handle", "generated_component"),
            description=component_data.get("description", "")
        )
        
        fields = []
        for field_data in fields_data:
            field = Field(
                label=field_data.get("label", "Field"),
                name=field_data.get("name", "field"),
                type=field_data.get("type", "text"),
                required=field_data.get("required", False),
                placeholder=field_data.get("placeholder", ""),
                config=field_data.get("config", {})
            )
            fields.append(field)
        
        logger.info(f"Successfully generated component: {component.name}")
        
        return ComponentResponse(
            component=component,
            fields=fields,
            success=True,
            message="Component generated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error generating component: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate component: {str(e)}")
    
    finally:
        cleanup_memory()

@app.get("/test")
async def test_generation():
    test_request = ComponentRequest(
        prompt="Create a hero section with video background and heading"
    )
    try:
        result = await generate_component(test_request)
        return {
            "test": "successful",
            "result": result
        }
    except Exception as e:
        return {
            "test": "failed",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
