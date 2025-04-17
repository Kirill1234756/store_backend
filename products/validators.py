from django.core.exceptions import ValidationError
import re
import html


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


def validate_price(value):
    """Validate price input"""
    if not isinstance(value, (int, float)):
        raise ValidationError('Price must be a number')
    if value < 0:
        raise ValidationError('Price cannot be negative')
    if value > 1000000:  # Maximum price limit
        raise ValidationError('Price is too high')


def validate_name(value):
    """Validate product name"""
    value = sanitize_input(value)
    if len(value) < 3:
        raise ValidationError('Name is too short')
    if len(value) > 100:
        raise ValidationError('Name is too long')
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', value):
        raise ValidationError('Name contains invalid characters')


def validate_description(value):
    """Validate product description"""
    value = sanitize_input(value)
    if len(value) < 10:
        raise ValidationError('Description is too short')
    if len(value) > 1000:
        raise ValidationError('Description is too long')


def validate_image(value):
    """Validate image upload"""
    if not value:
        raise ValidationError('No image provided')

    # Check file size (max 5MB)
    if value.size > 5 * 1024 * 1024:
        raise ValidationError('Image size too large')

    # Check file type
    allowed_types = ['image/jpeg', 'image/png', 'image/gif']
    if value.content_type not in allowed_types:
        raise ValidationError('Invalid image type')

    # Check file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    if not any(value.name.lower().endswith(ext) for ext in allowed_extensions):
        raise ValidationError('Invalid file extension')
