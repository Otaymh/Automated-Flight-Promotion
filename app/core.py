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
    """Create Instagram post with details in styled boxes using Pillow, ensuring Arabic text is upright."""
    try:
        background = Image.open(background_image_bytes).convert('RGB')
        background = background.resize((1080, 1080), Image.Resampling.LANCZOS) 

        draw = ImageDraw.Draw(background)

        # Use a font that supports Arabic (NotoSansArabic or fallback to default)
        try:
            font_large = ImageFont.truetype("NotoSansArabic-Regular.ttf", 60)  # Requires font file
        except:
            font_large = ImageFont.load_default()  # Fallback if font not found

        # Ensure Arabic text is rendered right-to-left and upright
        def draw_arabic_text(text, x, y, box_color, outline_color, font):
            bbox = draw.textbbox((x, y), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            box_x = x - text_width - 40
            draw.rectangle(
                [box_x - 20, y - 20, box_x + text_width + 20, y + text_height + 20],
                fill=box_color,
                outline=outline_color,
                width=3
            )
            draw.text((box_x, y), text, fill='white' if box_color != 'white' else 'black', font=font, align='right')

        # Destination (white box)
        draw_arabic_text(destination, 1080 // 2, 200, 'white', 'black', font_large)

        # Price (green box)
        price_text = f"{price} دولار"
        draw_arabic_text(price_text, 1080 // 2, 320, '#28a745', 'darkgreen', font_large)

        # Flight Type (blue box)
        draw_arabic_text(flight_type, 1080 // 2, 440, '#007bff', 'darkblue', font_large)

        final_bytes = BytesIO()
        background.save(final_bytes, format='JPEG', quality=95)
        final_bytes.seek(0)

        image_b64 = base64.b64encode(final_bytes.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{image_b64}"

    except Exception as e:
        print(f"Composition error: {e}")
        image_b64 = base64.b64encode(background_image_bytes.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{image_b64}"