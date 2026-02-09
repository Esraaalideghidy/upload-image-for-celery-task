from celery import shared_task
from django.apps import apps
from django.core.files.base import ContentFile
from .service import optimize_image, cleanup_temp_file, get_webp_filename


@shared_task
def upload_image_task(image_id: str, temp_path: str, original_name: str):
    """Process image in background: resize + convert to webp."""
    ImageModel = apps.get_model('upload_image', 'UploadImage')
    try:
        obj = ImageModel.objects.get(pk=image_id)
    except ImageModel.DoesNotExist:
        return {'error': 'not found'}

    obj.status = 'processing'
    obj.save()

    try:
        # Optimize image (resize + convert to WebP)
        buffer = optimize_image(temp_path, max_width=1920, quality=85)
        webp_name = get_webp_filename(original_name)

        # Save to ImageField
        obj.image.save(webp_name, ContentFile(buffer.read()), save=False)
        obj.status = 'completed'
        obj.save()

        # Cleanup
        cleanup_temp_file(temp_path)

        return {'id': str(obj.id), 'status': obj.status}

    except Exception as e:
        obj.status = 'failed'
        obj.save()
        cleanup_temp_file(temp_path)
        return {'error': str(e)}
