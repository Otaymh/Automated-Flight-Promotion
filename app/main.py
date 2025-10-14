from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
import pandas as pd
from supabase import create_client, Client
from app.models import FlightData
from app.core import fetch_background_image, generate_caption, compose_image
from app.dependencies import api_key_auth, limiter
from app.utils import logger

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Flight Post Generator API",
    description="API for generating Instagram-ready posts from flight data",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL or SUPABASE_KEY environment variables are not set. Check your .env file.")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"Error: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.post("/generate_post", response_model=dict)
@limiter.limit("10/minute")
async def generate_post(request: Request, flight: FlightData, api_key: str = Depends(api_key_auth)):
    try:
        logger.info(f"Processing flight to {flight.destination}")
        
        background_image = fetch_background_image(flight.destination)
        caption = generate_caption(flight.dict(), os.getenv('OPENAI_API_KEY'))
        composed_image = compose_image(background_image, flight.price, flight.destination, flight.type)
        
        # Save to Supabase flight_posts table
        data = {
            "destination": flight.destination,
            "price": flight.price,
            "type": flight.type,
            "image_url": composed_image,
            "created_at": pd.Timestamp.now().isoformat(),
            "user_id": None  # Set to None or a specific user ID if required
            # caption is not a column in flight_posts, so it's excluded
        }
        response = supabase.table("flight_posts").insert(data).execute()
        
        if response.data:
            logger.info(f"Successfully generated post for {flight.destination}")
            return {
                "caption": caption,
                "image_url": composed_image,
                "image_type": "base64" if composed_image.startswith('data:') else "url"
            }
        else:
            raise Exception("Failed to insert data into Supabase")

    except Exception as e:
        logger.error(f"Error in generate_post: {str(e)}")
        raise HTTPException(status_code=500, detail="فشل في إنشاء المنشور")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)