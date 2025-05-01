from django.core.exceptions import ValidationError
import re
import html
import os


def sanitize_input(value):
    """Sanitize input to prevent XSS and SQL injection"""
    if not isinstance(value, str):
        return value

    # Remove HTML tags
    value = html.escape(value)

    # Remove SQL injection patterns
    sql_patterns = [
        r'SELECT.*FROM',
        r'INSERT INTO',
        r'UPDATE.*SET',
        r'DELETE FROM',
        r'DROP TABLE',
        r'UNION SELECT',
    ]

    for pattern in sql_patterns:
        value = re.sub(pattern, '', value, flags=re.IGNORECASE)

    return value


def validate_product_data(data):
    """Centralized validation for product data"""
    # Validate and sanitize title
    if 'title' in data:
        title = sanitize_input(data['title'])
        if len(title) < 3:
            raise ValidationError("Title must be at least 3 characters long")
        if len(title) > 100:
            raise ValidationError("Title must be less than 100 characters")
        data['title'] = title

    # Validate and sanitize description
    if 'description' in data:
        description = sanitize_input(data['description'])
        if len(description) < 10:
            raise ValidationError("Description must be at least 10 characters long")
        if len(description) > 1000:
            raise ValidationError("Description must be less than 1000 characters")
        data['description'] = description

    # Validate price
    if 'price' in data:
        try:
            price = float(data['price'])
            if price <= 0:
                raise ValidationError("Price must be greater than 0")
            if price > 1000000:  # Maximum price limit
                raise ValidationError("Price is too high")
            data['price'] = price
        except (ValueError, TypeError):
            raise ValidationError("Price must be a valid number")

    # Validate condition
    if 'condition' in data:
        condition = data['condition']
        if condition not in ['A', 'B', 'C']:
            raise ValidationError("Invalid condition value")

    return data


def validate_image(value):
    """Validate image file"""
    if not value:
        return value

    # Check file type
    allowed_types = ['image/jpeg', 'image/png', 'image/gif']
    if value.content_type not in allowed_types:
        raise ValidationError('Unsupported file type. Only JPEG, PNG and GIF are allowed.')

    # Check file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError('Unsupported file extension. Only .jpg, .jpeg, .png and .gif are allowed.')

    # Check file size (5MB limit)
    if value.size > 5 * 1024 * 1024:
        raise ValidationError('File size cannot exceed 5MB.')

    return value
