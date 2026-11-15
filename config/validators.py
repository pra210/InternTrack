from pathlib import Path

from django.core.exceptions import ValidationError


def validate_image_upload(upload):
    extension = Path(upload.name).suffix.lower()
    if extension not in {'.jpg', '.jpeg', '.png', '.webp'}:
        raise ValidationError('Upload a JPG, PNG, or WEBP image.')
    if upload.size > 3 * 1024 * 1024:
        raise ValidationError('Image files must be 3 MB or smaller.')
