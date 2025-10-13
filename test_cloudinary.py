import requests
import os
from dotenv import load_dotenv
from io import BytesIO
import base64
from PIL import Image

load_dotenv()

CLOUDINARY_URL = os.getenv('CLOUDINARY_URL')
if not CLOUDINARY_URL:
    print("CLOUDINARY_URL not found in .env")
    exit(1)

import re
match = re.match(r'cloudinary://([^:]+):([^@]+)@(.+)', CLOUDINARY_URL)
if not match:
    print("Invalid CLOUDINARY_URL format")
    exit(1)

api_key, api_secret, cloud_name = match.groups()
print(f"Cloud: {cloud_name}, Key: {api_key[:5]}..., Secret: {api_secret[:5]}...")

img = Image.new('RGB', (100, 100), color='red')
img_bytes = BytesIO()
img.save(img_bytes, format='JPEG')
img_bytes.seek(0)

upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"

files = {'file': ('test.jpg', img_bytes.getvalue(), 'image/jpeg')}


data = {
    'upload_preset': 'unsigned', 
    'transformation': 'w_200,h_200,c_fill' 
}

try:
    response = requests.post(upload_url, files=files, data=data, auth=(api_key, api_secret), timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    if response.status_code == 200:
        print(f"Success! Secure URL: {response.json().get('secure_url')}")
except Exception as e:
    print(f"Error: {e}")
    if hasattr(e, 'response'):
        print(f"Response content: {e.response.content.decode('utf-8') if e.response.content else 'No content'}")