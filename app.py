"""
AkiyaVision - AI-powered vacant house renovation visualizer
"""
import os
import base64
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, validator, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(title="AkiyaVision", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy - adjust as needed
        nonce = base64.b64encode(os.urandom(16)).decode('utf-8')
        csp = (
            f"default-src 'self'; "
            f"script-src 'self' https://cdn.tailwindcss.com 'nonce-{nonce}'; "
            f"style-src 'self' 'nonce-{nonce}'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        response.headers["X-Nonce"] = nonce
        response.headers["Content-Security-Policy"] = csp
        
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS - Restrict to specific origins in production
# For development, you can add localhost origins
allowed_origins = [
    "http://localhost:8000",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    # Add your production domain here when deploying
    # "https://your-domain.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Mount static files and templates
import sys
from pathlib import Path

# Get the project root directory
if hasattr(sys, '_MEIPASS'):
    # Running in PyInstaller bundle
    BASE_DIR = Path(sys._MEIPASS)
else:
    # Running in normal Python environment
    BASE_DIR = Path(__file__).resolve().parent

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Data models
class House(BaseModel):
    id: str
    name: str
    address: str
    price: str
    area: str
    age: str
    description: str
    images: List[Dict[str, str]] = []

class RenovateRequest(BaseModel):
    style: str = Field(..., min_length=1, max_length=50, pattern="^[a-zA-Z_]+$")
    image_url: Optional[str] = Field(None, max_length=5000)

# Demo images for each house type - using local images
DEMO_IMAGES = {
    "kominka": [
        {
            "id": "demo1",
            "name": "台所",
            "url": "/static/demo-images/demo1.jpg",
            "description": "Kitchen"
        },
        {
            "id": "demo2", 
            "name": "外観",
            "url": "/static/demo-images/demo2.jpg",
            "description": "Exterior view"
        },
        {
            "id": "demo3",
            "name": "廊下",
            "url": "/static/demo-images/demo3.jpeg",
            "description": "Corridor"
        }
    ],
    "ikkodate": [
        {
            "id": "demo4",
            "name": "和室",
            "url": "/static/demo-images/demo4.jpeg",
            "description": "Japanese-style room"
        },
        {
            "id": "demo5",
            "name": "空き部屋",
            "url": "/static/demo-images/demo5.jpg",
            "description": "Empty room"
        },
        {
            "id": "demo6",
            "name": "リビング",
            "url": "/static/demo-images/demo6.jpg",
            "description": "Living room"
        }
    ]
}

# In-memory storage
houses_db: Dict[str, House] = {
    "house1": House(
        id="house1",
        name="世田谷区 - 古民家",
        address="東京都世田谷区",
        price="3,800万円",
        area="180㎡",
        age="築80年",
        description="伝統的な日本家屋。広い庭付き。リノベーション向き。",
        images=[]
    ),
    "house2": House(
        id="house2",
        name="杉並区 - 一戸建て",
        address="東京都杉並区",
        price="5,200万円",
        area="120㎡",
        age="築50年",
        description="静かな住宅街の一軒家。駅から徒歩15分。",
        images=[]
    )
}

# Renovation styles and prompts
RENOVATION_STYLES = {
    "modern": {
        "name": "モダン",
        "prompt": "A sleek modern minimalist interior with clean lines, neutral color palette, open floor plan, floor-to-ceiling windows, polished concrete floors, designer furniture, ambient LED lighting, and sophisticated architectural details",
        "negative": "old, damaged, dark, cluttered, low quality, traditional, ornate"
    },
    "traditional": {
        "name": "和モダン",
        "prompt": "A refined Japanese modern interior featuring tatami floors, shoji screens, natural wood elements, minimalist zen aesthetic, built-in storage, paper lantern lighting, indoor garden views, and contemporary Japanese furniture",
        "negative": "western style, damaged, dark, old, low quality, cluttered, colorful"
    },
    "western": {
        "name": "洋風",
        "prompt": "A luxurious Western-style interior with hardwood flooring, crown molding, elegant furniture, crystal chandelier, marble accents, rich color scheme, formal dining area, and classic American or European design elements",
        "negative": "japanese style, old, damaged, dark, low quality, minimalist, modern"
    },
    "scandinavian": {
        "name": "北欧風",
        "prompt": "A cozy Scandinavian interior with white walls, light oak floors, hygge atmosphere, natural textiles, minimalist furniture, abundant natural light, indoor plants, warm throw blankets, and Nordic design elements",
        "negative": "dark, cluttered, damaged, old, low quality, ornate, colorful"
    },
    "industrial": {
        "name": "インダストリアル",
        "prompt": "An industrial loft interior with exposed concrete walls, metal beams, Edison bulb lighting, vintage leather furniture, steel fixtures, open ductwork, large factory-style windows, and raw wood accents",
        "negative": "fancy, ornate, traditional, carpeted, closed spaces"
    },
    "zen": {
        "name": "ミニマリスト禅",
        "prompt": "A serene minimalist zen interior with white walls, natural stone elements, bamboo accents, floor cushions, low wooden tables, indirect lighting, empty space as design element, and a small indoor rock garden",
        "negative": "cluttered, colorful, busy patterns, western furniture"
    },
    "showa": {
        "name": "昭和レトロ",
        "prompt": "A nostalgic Showa-era interior with wood paneling, vintage Japanese furniture, retro appliances, warm lighting, traditional kotatsu table, classic posters, and period-appropriate color scheme",
        "negative": "modern, minimalist, high-tech, western style"
    },
    "luxury": {
        "name": "ラグジュアリー",
        "prompt": "A luxury hotel-style interior with plush carpeting, elegant furniture, marble accents, designer lighting fixtures, rich textures, sophisticated color palette, and premium finishes throughout",
        "negative": "cheap, simple, rustic, industrial, DIY"
    },
    "eco": {
        "name": "エコナチュラル",
        "prompt": "A sustainable eco-friendly interior with reclaimed wood, living walls, natural fiber furniture, solar tube lighting, cork flooring, recycled materials, and abundant greenery",
        "negative": "synthetic, plastic, artificial lighting, non-sustainable"
    },
    "mediterranean": {
        "name": "地中海風",
        "prompt": "A Mediterranean coastal interior with white stucco walls, terracotta tiles, arched doorways, wrought iron details, blue accents, natural wood beams, and sun-drenched atmosphere",
        "negative": "dark, industrial, modern, Japanese traditional"
    },
    "smart": {
        "name": "スマートホーム",
        "prompt": "A futuristic smart home interior with integrated LED panels, voice-controlled lighting, minimalist tech furniture, hidden screens, automated systems, and seamless technology integration",
        "negative": "traditional, vintage, rustic, manual controls"
    },
    "bohemian": {
        "name": "ボヘミアン",
        "prompt": "A bohemian eclectic interior with layered textiles, macrame wall art, vintage rugs, mixed patterns, indoor plants, warm earth tones, floor cushions, and artistic decorative elements",
        "negative": "minimal, modern, structured, monochrome"
    }
}

@app.get("/", response_class=HTMLResponse)
@limiter.limit("100/minute")
async def root(request: Request):
    """Serve the main page"""
    return templates.TemplateResponse(request, "index.html")

@app.get("/api/houses")
@limiter.limit("100/minute")
async def get_houses(request: Request):
    """Get all houses"""
    return list(houses_db.values())

@app.get("/api/demo-images/{house_type}")
@limiter.limit("100/minute")
async def get_demo_images(house_type: str, request: Request):
    """Get demo images for a house type"""
    if house_type == "house1":
        return DEMO_IMAGES.get("kominka", [])
    elif house_type == "house2":
        return DEMO_IMAGES.get("ikkodate", [])
    else:
        raise HTTPException(status_code=404, detail="House type not found")


@app.post("/api/renovate/{house_id}/{image_id}")
@limiter.limit("10/hour")  # Strict limit for expensive AI operations
async def renovate_image(house_id: str, image_id: str, renovation_request: RenovateRequest, request: Request):
    """Generate a renovated version of the image"""
    if house_id not in houses_db:
        raise HTTPException(status_code=404, detail="House not found")
    
    house = houses_db[house_id]
    
    # Check if it's a demo image
    if image_id.startswith("demo-"):
        # For demo images, create a temporary image entry using the provided URL
        if not renovation_request.image_url:
            raise HTTPException(status_code=400, detail="Image URL required for demo images")
        image = {"id": image_id, "data": renovation_request.image_url}
    else:
        # Look for uploaded image
        image = next((img for img in house.images if img["id"] == image_id), None)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
    
    if renovation_request.style not in RENOVATION_STYLES:
        raise HTTPException(status_code=400, detail="Invalid style")
    
    style_config = RENOVATION_STYLES[renovation_request.style]
    
    # Check if Replicate API token is configured
    if not os.getenv("REPLICATE_API_TOKEN"):
        # Return mock response for development
        return {
            "id": f"mock-{uuid.uuid4()}",
            "status": "succeeded",
            "output": [image["data"]],  # Return original image as mock
            "style": renovation_request.style,
            "message": "Mock response - configure REPLICATE_API_TOKEN for real generation"
        }
    
    try:
        # Initialize Replicate client
        import replicate
        
        # Handle different image formats
        if image["data"].startswith("data:"):
            # It's a base64 data URL
            image_input = image["data"]
        elif image["data"].startswith("http"):
            # It's a URL - use directly
            image_input = image["data"]
        elif image["data"].startswith("/static/demo-images/"):
            # It's a local demo image - read the file and convert to base64
            # Extract just the filename to prevent path traversal
            filename = os.path.basename(image["data"])
            
            # Validate filename - only allow specific demo images
            allowed_files = ["demo1.jpg", "demo2.jpg", "demo3.jpeg", 
                           "demo4.jpeg", "demo5.jpg", "demo6.jpg"]
            
            if filename not in allowed_files:
                raise HTTPException(status_code=400, detail="Invalid demo image")
            
            # Construct safe path using BASE_DIR for Vercel compatibility
            file_path = BASE_DIR / "static" / "demo-images" / filename
            
            # Additional check to ensure we're within the demo-images directory
            abs_path = os.path.abspath(str(file_path))
            demo_dir = os.path.abspath(str(BASE_DIR / "static" / "demo-images"))
            
            if not abs_path.startswith(demo_dir):
                raise HTTPException(status_code=400, detail="Invalid file path")
            
            try:
                with open(file_path, "rb") as f:
                    file_content = f.read()
                    file_base64 = base64.b64encode(file_content).decode("utf-8")
                    # Determine mime type from extension
                    file_path_str = str(file_path)
                    if file_path_str.endswith(".jpg") or file_path_str.endswith(".jpeg"):
                        mime_type = "image/jpeg"
                    elif file_path_str.endswith(".png"):
                        mime_type = "image/png"
                    else:
                        mime_type = "image/jpeg"  # default
                    image_input = f"data:{mime_type};base64,{file_base64}"
            except Exception as e:
                # Don't expose internal error details
                raise HTTPException(status_code=500, detail="Failed to process image")
        else:
            # Assume it's base64 without data URL prefix
            image_input = f"data:image/png;base64,{image['data']}"
        
        # Run Interior AI model by erayyavuz
        # This model is specifically trained for interior design transformations
        output = replicate.run(
            "erayyavuz/interior-ai:e299c531485aac511610a878ef44b554381355de5ee032d109fcae5352f39fa9",
            input={
                "input": image_input,  # Note: this model uses "input" instead of "image"
                "prompt": style_config["prompt"],
                "negative_prompt": "lowres, watermark, banner, logo, watermark, contactinfo, text, deformed, blurry, blur, out of focus, out of frame, surreal, extra, ugly, upholstered walls, fabric walls, plush walls, mirror, mirrored, functional",
                "num_inference_steps": 25
            }
        )
        
        # Handle output from interior AI model
        # Different models return different formats (bytes, file-like objects, or URLs)
        try:
            if hasattr(output, 'read'):
                # It's a file-like object, read the bytes
                content = output.read()
                generated_url = f"data:image/png;base64,{base64.b64encode(content).decode('utf-8')}"
            elif isinstance(output, bytes):
                # Direct bytes
                generated_url = f"data:image/png;base64,{base64.b64encode(output).decode('utf-8')}"
            elif isinstance(output, str) and output.startswith('http'):
                # It's already a URL
                generated_url = output
            elif isinstance(output, list) and len(output) > 0:
                # List of outputs
                first = output[0]
                if hasattr(first, 'read'):
                    content = first.read()
                    generated_url = f"data:image/png;base64,{base64.b64encode(content).decode('utf-8')}"
                elif isinstance(first, str):
                    generated_url = first
                else:
                    generated_url = str(first)
            else:
                # Fallback
                generated_url = image["data"]
        except Exception as e:
            # Don't expose error details, use fallback
            generated_url = image["data"]
        
        # Store generated image
        generated_image = {
            "id": str(uuid.uuid4()),
            "original_id": image_id,
            "style": renovation_request.style,
            "data": generated_url,
            "generated_at": datetime.now().isoformat()
        }
        
        # Add to images list with metadata
        house.images.append(generated_image)
        
        return {
            "id": generated_image["id"],
            "status": "succeeded",
            "output": [str(generated_image["data"])],  # Ensure string
            "style": renovation_request.style
        }
        
    except Exception as e:
        # Log the error internally but don't expose details to client
        import logging
        logging.error(f"Error in renovate endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="画像生成に失敗しました")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port, reload=True)