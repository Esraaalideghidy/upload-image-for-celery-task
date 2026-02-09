import os
import uuid
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from django.utils.timezone import now
import requests


# ================================ Validation ================================

def validate_image(image, size_limit_mb=10, acceptable_ratios=None, tolerance=0.05,
                   min_width=None, max_width=None, min_height=None, max_height=None):
    """
    Validate image size, dimensions, and aspect ratio.

    Args:
        image: The uploaded image file
        size_limit_mb: Maximum file size in MB
        acceptable_ratios: List of tuples like [(1,1), (16,9)] or None to skip
        tolerance: Allowed deviation from aspect ratio
        min_width, max_width: Width limits in pixels
        min_height, max_height: Height limits in pixels

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # Check file size
    if image.size > size_limit_mb * 1024 * 1024:
        errors.append(f"Image size must be less than {size_limit_mb} MB.")

    # Open image for dimension checks
    img = Image.open(image)
    img_width, img_height = img.width, img.height

    # Check dimensions
    if min_width and img_width < min_width:
        errors.append(f"Image width must be at least {min_width}px.")
    if max_width and img_width > max_width:
        errors.append(f"Image width must be at most {max_width}px.")
    if min_height and img_height < min_height:
        errors.append(f"Image height must be at least {min_height}px.")
    if max_height and img_height > max_height:
        errors.append(f"Image height must be at most {max_height}px.")

    # Check aspect ratio
    if acceptable_ratios:
        aspect_ratio = img_width / img_height
        ratio_match = any(
            abs(aspect_ratio - (r[0] / r[1])) <= tolerance
            for r in acceptable_ratios
        )
        if not ratio_match:
            ratio_strs = [f"{r[0]}:{r[1]}" for r in acceptable_ratios]
            errors.append(f"Image aspect ratio must be one of: {', '.join(ratio_strs)}")

    image.seek(0)  # Reset file pointer
    return errors


# ================================ Optimization ================================

def optimize_image(image_source, max_width=1920, quality=85):
    """
    Optimize image: resize + convert to WebP.

    Args:
        image_source: Path string or file-like object
        max_width: Maximum width in pixels
        quality: WebP quality 1-100

    Returns:
        tuple: (BytesIO buffer, suggested filename)
    """
    with Image.open(image_source) as img:
        # Convert to RGB for WebP compatibility
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Resize if too wide
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Save as WebP
        buffer = BytesIO()
        img.save(buffer, format='WEBP', quality=quality)
        buffer.seek(0)

        return buffer


def convert_to_webp(image, quality=85):
    """Convert image to WebP format."""
    img = Image.open(image)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    buffer = BytesIO()
    img.save(buffer, format='WEBP', quality=quality)
    buffer.seek(0)
    return buffer


# ================================ File Helpers ================================

def generate_unique_filename(original_name, prefix="img"):
    """Generate unique filename with UUID and timestamp."""
    extension = original_name.rsplit('.', 1)[-1] if '.' in original_name else 'webp'
    timestamp = now().strftime('%Y%m%d%H%M%S')
    return f"{prefix}_{uuid.uuid4().hex[:8]}_{timestamp}.{extension}"


def save_temp_file(image_file, temp_dir):
    """Save uploaded file to temp directory."""
    os.makedirs(temp_dir, exist_ok=True)
    temp_filename = f"{uuid.uuid4()}_{image_file.name}"
    temp_path = os.path.join(temp_dir, temp_filename)

    with open(temp_path, 'wb') as f:
        for chunk in image_file.chunks():
            f.write(chunk)

    return temp_path


def cleanup_temp_file(temp_path):
    """Delete temp file if exists."""
    if temp_path and os.path.exists(temp_path):
        os.remove(temp_path)


def get_webp_filename(original_name):
    """Convert filename to .webp extension."""
    name_without_ext = original_name.rsplit('.', 1)[0] if '.' in original_name else original_name
    return f"{name_without_ext}.webp"


# ================================ URL Download ================================

def download_and_save_image(url, instance, image_field_name='image'):
    """
    Download image from URL, convert to WebP, and save to model.

    Args:
        url: Image URL
        instance: Model instance to save to
        image_field_name: Name of the ImageField

    Returns:
        bool: Success status
    """
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            return False

        # Optimize and convert to WebP
        buffer = optimize_image(BytesIO(response.content))

        # Generate filename from URL
        url_filename = url.split('/')[-1].split('?')[0]
        webp_name = get_webp_filename(url_filename)

        # Save to model
        image_field = getattr(instance, image_field_name)
        image_field.save(webp_name, ContentFile(buffer.read()), save=True)

        return True
    except Exception:
        return False
