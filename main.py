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

# Add CORS middleware to allow requests from WordPress sites
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your WordPress domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for model and tokenizer
model = None
tokenizer = None

# Pydantic models for request/response
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
    template: Optional[dict] = None
    success: bool = True
    message: str = "Component generated successfully"

def cleanup_gpu_memory():
    """Clean up GPU memory after generation"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()

@app.on_event("startup")
async def load_model():
    """Load the Microsoft Phi-1.5 model on startup"""
    global model, tokenizer
    
    try:
        logger.info("Loading Microsoft Phi-1.5 model...")
        
        # Load tokenizer and model
        model_name = "microsoft/phi-1_5"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,  # Use float32 for CPU
            low_cpu_mem_usage=True,
            device_map="auto"
        )
        
        # Move model to CPU to save memory
        model = model.to("cpu")
        
        logger.info("Microsoft Phi-1.5 model loaded successfully!")
        
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise e

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CCC AI Server is running!",
        "model": "Microsoft Phi-1.5",
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
        "model_name": "microsoft/phi-1_5"
    }

@app.post("/generate-component", response_model=ComponentResponse)
async def generate_component(request: ComponentRequest):
    """Generate a component based on user prompt"""
    
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="AI model not loaded")
    
    try:
        logger.info(f"Generating component for prompt: {request.prompt}")
        
        # Create system prompt
        system_prompt = f"""
You are a WordPress component generator. Based on the user's description, generate a component structure.

User Request: {request.prompt}

Available field types: {', '.join(request.available_fields)}

Generate a JSON response with this exact structure:
{{
    "component": {{
        "name": "Component Name",
        "handle": "component_handle",
        "description": "Component description"
    }},
    "fields": [
        {{
            "label": "Field Label",
            "name": "field_name",
            "type": "field_type",
            "required": true/false,
            "placeholder": "Placeholder text",
            "config": {{}}
        }}
    ]
}}

Rules:
- Use only the available field types
- Create meaningful field names and labels
- Make important fields required
- Use appropriate field types for the content
- Keep component names descriptive
- Use kebab-case for handles
"""

        # Generate response
        inputs = tokenizer(system_prompt, return_tensors="pt", max_length=512, truncation=True)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=1000,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
                num_return_sequences=1
            )
        
        response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Clean up memory
        cleanup_gpu_memory()
        
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in AI response")
        
        json_str = response_text[json_start:json_end]
        result = json.loads(json_str)
        
        # Validate and structure the response
        component_data = result.get("component", {})
        fields_data = result.get("fields", [])
        
        # Create response
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
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to parse AI response")
        
    except Exception as e:
        logger.error(f"Error generating component: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate component: {str(e)}")
    
    finally:
        # Always clean up memory
        cleanup_gpu_memory()

@app.get("/test")
async def test_generation():
    """Test endpoint with a sample prompt"""
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