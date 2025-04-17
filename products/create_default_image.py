from PIL import Image, ImageDraw, ImageFont
import os

def create_default_image():
    # Create a 300x300 white image
    img = Image.new('RGB', (300, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add some text
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    text = "No Image"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x = (300 - text_width) // 2
    y = (300 - text_height) // 2
    
    draw.text((x, y), text, font=font, fill='gray')
    
    # Ensure directory exists
    os.makedirs('media/products', exist_ok=True)
    
    # Save the image
    img.save('media/products/default.jpg')

if __name__ == '__main__':
    create_default_image() 