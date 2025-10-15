import requests
import os
import re
import base64 
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
API_KEY = os.getenv('API_KEY')

def fetch_background_image(destination: str) -> BytesIO:
    """Generate destination-specific background using OpenAI DALL-E."""
    prompt = f"High-quality realistic photo of famous landmark in {destination},photorealistic, no text."
    url = "https://api.openai.com/v1/images/generations"
    headers = {'Authorization': f'Bearer {OPENAI_API_KEY}', 'Content-Type': 'application/json'}
    payload = {
        'model': 'dall-e-3',
        'prompt': prompt,
        'n': 1,
        'size': '1024x1024',
        'response_format': 'b64_json'
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get('data') and data['data'][0].get('b64_json'):
            image_data = base64.b64decode(data['data'][0]['b64_json'])
            print(f"OpenAI image generated for {destination}")
            return BytesIO(image_data)
        raise ValueError("No image data from OpenAI")
    except Exception as e:
        print(f"OpenAI error: {e}")
    
        img = Image.new('RGB', (800, 600), color='lightblue')
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        draw.text((50, 250), f"صورة {destination}", fill='darkblue', font=font)
        fallback_bytes = BytesIO()
        img.save(fallback_bytes, format='JPEG')
        fallback_bytes.seek(0)
        return fallback_bytes

def generate_caption(flight_data: dict, api_key: str) -> str:
    prompt = f"أنشئ تعليقًا مثيرًا لإنستغرام عن رحلة {flight_data['type']} إلى {flight_data['destination']} بسعر {flight_data['price']} ."
    url = "https://api.openai.com/v1/chat/completions"
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    payload = {'model': 'gpt-4o-mini', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 100}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Caption error: {e}")
        return f"رحلة إلى {flight_data['destination']} بسعر {flight_data['price']} دولار #سفر"

def compose_image(background_image_bytes: BytesIO, price: int, destination: str, flight_type: str) -> str:
    """Create Instagram post with details in styled boxes using Pillow."""
    try:
        background = Image.open(background_image_bytes).convert('RGB')
        background = background.resize((1080, 1080), Image.Resampling.LANCZOS)  # Instagram square
        
        draw = ImageDraw.Draw(background)
        
        font_large = ImageFont.load_default()
        try:
            font_large = ImageFont.truetype("arial.ttf", 60)
        except:
            pass
        
        dest_bbox = draw.textbbox((0, 0), destination, font=font_large)
        dest_width = dest_bbox[2] - dest_bbox[0] + 40
        dest_x = (1080 - dest_width) // 2
        dest_y = 200
        draw.rectangle([dest_x-20, dest_y-20, dest_x+dest_width+20, dest_y+80], fill='white', outline='black', width=3)
        draw.text((dest_x, dest_y), destination, fill='black', font=font_large)
        
        price_text = f"{price} دولار"
        price_bbox = draw.textbbox((0, 0), price_text, font=font_large)
        price_width = price_bbox[2] - price_bbox[0] + 40
        price_x = (1080 - price_width) // 2
        price_y = dest_y + 120
        draw.rectangle([price_x-20, price_y-20, price_x+price_width+20, price_y+80], fill='#28a745', outline='darkgreen', width=3)
        draw.text((price_x, price_y), price_text, fill='white', font=font_large)
        
        type_bbox = draw.textbbox((0, 0), flight_type, font=font_large)
        type_width = type_bbox[2] - type_bbox[0] + 40
        type_x = (1080 - type_width) // 2
        type_y = price_y + 120
        draw.rectangle([type_x-20, type_y-20, type_x+type_width+20, type_y+80], fill='#007bff', outline='darkblue', width=3)
        draw.text((type_x, type_y), flight_type, fill='white', font=font_large)
        
        final_bytes = BytesIO()
        background.save(final_bytes, format='JPEG', quality=95)
        final_bytes.seek(0)
        
        image_b64 = base64.b64encode(final_bytes.getvalue()).decode('utf-8')
        print(f" Composed Instagram post for {destination}")
        return f"data:image/jpeg;base64,{image_b64}"
        
    except Exception as e:
        print(f" Composition error: {e}")
      
        image_b64 = base64.b64encode(background_image_bytes.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{image_b64}"