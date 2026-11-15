from pathlib import Path

from django.core.exceptions import ValidationError

from config.validators import validate_image_upload


def validate_pdf_upload(upload):
    if Path(upload.name).suffix.lower() != '.pdf':
        raise ValidationError('Resume files must use the PDF format.')
    if upload.size > 5 * 1024 * 1024:
        raise ValidationError('Resume files must be 5 MB or smaller.')

    position = upload.tell()
    try:
        upload.seek(0)
        if not upload.read(5).startswith(b'%PDF-'):
            raise ValidationError('The uploaded resume is not a valid PDF file.')
    finally:
        upload.seek(position)
