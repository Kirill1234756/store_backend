from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO
import os
from django.core.files.storage import default_storage

def save_image(image_file, path_prefix='products/', max_size=(1200, 1200), quality=85):
    """
    Save an image file with compression and optimization
    
    Args:
        image_file: The uploaded image file
        path_prefix: Directory prefix for saving the image
        max_size: Maximum dimensions (width, height)
        quality: JPEG/WebP quality (1-100)
    
    Returns:
        str: Path to the saved image
    """
    # Open and process image
    image = Image.open(image_file)
    
    # Convert to RGB if necessary
    if image.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        image = background
    
    # Resize if too large
    if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Generate filename
    ext = '.webp'  # Use WebP for better compression
    filename = f"{os.path.splitext(image_file.name)[0]}{ext}"
    filepath = os.path.join(path_prefix, filename)
    
    # Save as WebP
    output = BytesIO()
    image.save(output, format='WEBP', quality=quality, optimize=True)
    output.seek(0)
    
    # Save to storage
    saved_path = default_storage.save(filepath, ContentFile(output.read()))
    return saved_path

def delete_image(image_path):
    """
    Delete an image file from storage
    
    Args:
        image_path: Path to the image file
    """
    if image_path and default_storage.exists(image_path):
        default_storage.delete(image_path) 