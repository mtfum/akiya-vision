"""
Vercel serverless function entry point
"""
from app import app

# Vercel expects a callable named 'app'
# The FastAPI app instance is already named 'app' so we can use it directly