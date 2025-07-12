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
        csp = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.tailwindcss.com 'unsafe-inline'; "
            "style-src 'self' https://cdn.tailwindcss.com 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
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
    "*",  # Allow all origins temporarily for debugging
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
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

# Mount public folder for local development
if (BASE_DIR / "public").exists():
    app.mount("/public", StaticFiles(directory=str(BASE_DIR / "public")), name="public")

# Also mount static for backward compatibility if it exists
if (BASE_DIR / "static").exists():
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

# Demo images for each house type
# In production, these could be hosted on a CDN or external storage
# For now, using local paths that will be served by Vercel
DEMO_IMAGES = {
    "kominka": [
        {
            "id": "demo1",
            "name": "台所",
            "url": "/public/demo1.jpg",
            "description": "Kitchen"
        },
        {
            "id": "demo2", 
            "name": "外観",
            "url": "/public/demo2.jpg",
            "description": "Exterior view"
        },
        {
            "id": "demo3",
            "name": "廊下",
            "url": "/public/demo3.jpeg",
            "description": "Corridor"
        }
    ],
    "ikkodate": [
        {
            "id": "demo4",
            "name": "和室",
            "url": "/public/demo4.jpeg",
            "description": "Japanese-style room"
        },
        {
            "id": "demo5",
            "name": "空き部屋",
            "url": "/public/demo5.jpg",
            "description": "Empty room"
        },
        {
            "id": "demo6",
            "name": "リビング",
            "url": "/public/demo6.jpg",
            "description": "Living room"
        }
    ]
}

# Get demo houses data - function ensures data is always available in serverless
def get_demo_houses() -> Dict[str, House]:
    return {
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

# In-memory storage - will be populated on each request in serverless
houses_db: Dict[str, House] = {}

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

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/", response_class=HTMLResponse)
@limiter.limit("100/minute")
async def root(request: Request):
    """Serve the main page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/houses")
@limiter.limit("100/minute")
async def get_houses(request: Request):
    """Get all houses"""
    try:
        # Always return demo data in serverless environment
        demo_houses = get_demo_houses()
        houses_list = list(demo_houses.values())
        print(f"Returning {len(houses_list)} houses")
        return houses_list
    except Exception as e:
        print(f"Error in get_houses: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching houses: {str(e)}")

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
    # Get demo houses for serverless environment
    demo_houses = get_demo_houses()
    
    if house_id not in demo_houses:
        raise HTTPException(status_code=404, detail="House not found")
    
    house = demo_houses[house_id]
    
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
        elif image["data"].startswith("/public/"):
            # In production on Vercel, these images are served from public folder
            # The Replicate API can accept URLs
            
            # Get the base URL from the request
            base_url = str(request.base_url).rstrip('/')
            
            # Construct the full URL for the image
            image_input = f"{base_url}{image['data']}"
            
            print(f"Using demo image URL: {image_input}")
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
        
        # Note: In serverless, we don't persist the generated images
        # They would need to be stored in a database or external storage
        
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