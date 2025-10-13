from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.models import FlightData, Flight, Post, Base
from app.core import fetch_background_image, generate_caption, compose_image
from app.dependencies import api_key_auth, limiter
from app.utils import logger
from dotenv import load_dotenv
import os
import requests
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from io import BytesIO
from app.models import FlightData, Post, Base 
from app.core import fetch_background_image, generate_caption, compose_image
from app.dependencies import api_key_auth, limiter
from sqlalchemy.orm import Session

load_dotenv()

app = FastAPI(
    title="Flight Post Generator API",
    description="API for generating Instagram-ready posts from flight data",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8080", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter

# Database setup it's SQLite
DATABASE_URL = "sqlite:///./flight_posts.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"Error: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/generate_post", response_model=dict)
@limiter.limit("10/minute")
async def generate_post(request: Request, flight: FlightData, api_key: str = Depends(api_key_auth), db: Session = Depends(get_db)):
    try:
        logger.info(f"Processing flight to {flight.destination}")
        
        
        background_image = fetch_background_image(flight.destination)
        
        
        caption = generate_caption(flight.dict(), os.getenv('OPENAI_API_KEY'))
        
        
        composed_image = compose_image(background_image, flight.price, flight.destination, flight.type)
        
        # this to save to database
        db_post = Post(
            destination=flight.destination,
            price=flight.price,
            type=flight.type,
            caption=caption,
            image_url=composed_image 
        )
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        
        logger.info(f"Successfully generated post for {flight.destination}")
        return {
            "caption": caption,
            "image_url": composed_image,
            "image_type": "base64" if composed_image.startswith('data:') else "url"
        }
        
    except Exception as e:
        logger.error(f"Error in generate_post: {str(e)}")
        raise HTTPException(status_code=500, detail="فشل في إنشاء المنشور")
