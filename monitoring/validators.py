from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_IMAGE_SIZE_MB = 2
MAX_IMAGE_SIZE = MAX_IMAGE_SIZE_MB * 1024 * 1024


def _is_new_upload(file):
    return not getattr(file, "_committed", False)


def validate_image_size(file):
    if not _is_new_upload(file):
        return
    if file.size > MAX_IMAGE_SIZE:
        raise ValidationError(
            f"La imagen pesa {file.size / 1024 / 1024:.1f} MB. "
            f"El máximo permitido es {MAX_IMAGE_SIZE_MB} MB."
        )


def validate_image_content(file):
    if not _is_new_upload(file):
        return
    try:
        file.seek(0)
        with Image.open(file) as image:
            image_format = image.format
            image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        raise ValidationError(
            "El archivo no es una imagen válida o está dañado."
        )
    finally:
        file.seek(0)

    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise ValidationError(
            "Formato de imagen no permitido. Use JPG, PNG o WEBP."
        )
