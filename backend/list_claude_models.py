# hello_debug.py — Debug Version with Better Error Handling
import os
import asyncio
import json
import logging
import time
import traceback
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
import uvicorn
from bs4 import BeautifulSoup
import anthropic

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Orchids Cloner Debug", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CloneRequest(BaseModel):
    url: HttpUrl
    max_input_tokens: Optional[int] = Field(default=3000, ge=500, le=4000)
    max_output_tokens: Optional[int] = Field(default=3000, ge=500, le=3000)
    include_responsive: bool = Field(default=True)
    css_framework: str = Field(default="tailwind", pattern="^(tailwind|bootstrap|custom)$")

class CloneResponse(BaseModel):
    html: str
    confidence_score: float
    processing_time: float
    token_usage: Dict[str, int]
    warnings: List[str] = []

# Test API keys (replace with your actual keys)
claude_api_key = "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"
hyper_api_key = "hb_aa12124d8acae736aaa4a8fd73d5"

# Test the API keys first
def test_api_keys():
    """Test if API keys are working"""
    logger.info("Testing API keys...")
    
    # Test Claude API
    try:
        client = anthropic.Anthropic(api_key=claude_api_key)
        # Try a simple request
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hello"}]
        )
        logger.info("✅ Claude API key is working")
        return True
    except Exception as e:
        logger.error(f"❌ Claude API key failed: {e}")
        return False

# Simplified WebCloner without HyperBrowser for testing
class SimpleWebCloner:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        logger.info("Initializing SimpleWebCloner...")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logger.info("Cleaning up SimpleWebCloner...")
        pass

def create_mock_layout_data():
    """Create mock layout data for testing"""
    return [
        {
            "tag": "header",
            "width": 1200,
            "height": 80,
            "text": "Sample Header",
            "styles": {"bg": "#ffffff", "color": "#333333"}
        },
        {
            "tag": "main",
            "width": 1200,
            "height": 600,
            "text": "Main content area",
            "styles": {"bg": "#f8f9fa", "color": "#212529"}
        },
        {
            "tag": "footer",
            "width": 1200,
            "height": 60,
            "text": "Footer content",
            "styles": {"bg": "#343a40", "color": "#ffffff"}
        }
    ]

def build_simple_prompt(url: str, framework: str = "tailwind") -> str:
    """Build a simple test prompt"""
    return f"""Create a simple HTML page that represents: {url}

Include:
- A header with navigation
- A main content area
- A footer

Use {framework} CSS classes. Output only complete HTML."""

@app.post("/api/clone", response_model=CloneResponse)
async def clone_website(request: CloneRequest):
    start_time = time.time()
    target_url = str(request.url)
    warnings = []
    
    logger.info(f"🚀 Starting clone for: {target_url}")
    
    try:
        # Test API keys first
        if not test_api_keys():
            raise HTTPException(status_code=500, detail="API keys are not working")
        
        # Use simplified cloner for testing
        async with SimpleWebCloner() as cloner:
            logger.info("✅ WebCloner initialized successfully")
            
            # Create mock data instead of scraping
            logger.info("Creating mock layout data...")
            layout_blocks = create_mock_layout_data()
            
            # Build simple prompt
            prompt = build_simple_prompt(target_url, request.css_framework)
            logger.info(f"Generated prompt: {prompt[:100]}...")
            
            # Generate with Claude
            logger.info("Calling Claude API...")
            client = anthropic.Anthropic(api_key=claude_api_key)
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=request.max_output_tokens,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}],
            )
            
            logger.info("✅ Claude API call successful")
            
            generated_html = response.content[0].text
            
            # Clean up HTML if needed
            if "```html" in generated_html:
                generated_html = generated_html.split("```html")[1].split("```")[0].strip()
            elif "```" in generated_html:
                generated_html = generated_html.split("```")[1].split("```")[0].strip()
            
            # Calculate metrics
            processing_time = time.time() - start_time
            confidence = 0.8  # Mock confidence score
            
            token_usage = {
                "input": response.usage.input_tokens,
                "output": response.usage.output_tokens,
                "total": response.usage.input_tokens + response.usage.output_tokens
            }
            
            logger.info(f"✅ Clone completed in {processing_time:.2f}s")
            
            return CloneResponse(
                html=generated_html,
                confidence_score=confidence,
                processing_time=processing_time,
                token_usage=token_usage,
                warnings=warnings
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Clone failed with error: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Cloning failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Enhanced health check"""
    try:
        # Test API connection
        api_working = test_api_keys()
        
        return {
            "status": "healthy" if api_working else "degraded",
            "timestamp": time.time(),
            "version": "2.0-debug",
            "api_status": "working" if api_working else "failed"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "Server is running", "timestamp": time.time()}

# Add error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    logger.error(f"Request: {request.url}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return {"error": "Internal server error", "detail": str(exc)}

def main():
    logger.info("🚀 Starting debug server...")
    uvicorn.run(
        "hello_debug:app", 
        host="127.0.0.1", 
        port=8002, 
        reload=True, 
        timeout_keep_alive=120,
        access_log=True,
        log_level="debug"
    )

if __name__ == "__main__":
    main()