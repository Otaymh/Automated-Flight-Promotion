from fastapi import Header, HTTPException, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv('API_KEY')

limiter = Limiter(key_func=get_remote_address)

def api_key_auth(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key