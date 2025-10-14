from pydantic import BaseModel, validator, Field
import datetime
import pandas as pd

class FlightData(BaseModel):
    price: int = Field(..., gt=0)
    destination: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)

    @validator('price')
    @classmethod
    def validate_price(cls, v):
        if v < 1:
            raise ValueError('Price must be at least $1')
        return v

# Optional: Comment out SQLAlchemy models since using Supabase API
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Flight(Base):
    __tablename__ = "flights"
    id = Column(Integer, primary_key=True, index=True)
    price = Column(Integer)
    destination = Column(String, index=True)
    type = Column(String)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    destination = Column(String, index=True)
    price = Column(Integer)
    type = Column(String)
    caption = Column(String)
    image_url = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
"""