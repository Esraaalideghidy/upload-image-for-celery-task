import os
from django.conf import settings
from django.http import FileResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from upload_image import serializers
from .models import UploadImage
from .service import validate_image, save_temp_file
from . import tasks


class UploadImageViewSet(viewsets.ModelViewSet):
    queryset = UploadImage.objects.all()

    serializer_class_name = {
        'list': 'UploadImageRetrieveSerializer',
        'retrieve': 'UploadImageRetrieveSerializer',
        'create': 'UploadImageCreateSerializer',
        'upload_image': 'UploadImageRetrieveSerializer',
    }

    def get_serializer_class(self):
        serializer_name = self.serializer_class_name.get(self.action, 'UploadImageRetrieveSerializer')
        return getattr(serializers, serializer_name)

    @action(detail=False, methods=['get', 'post'], url_path='upload-image', parser_classes=[MultiPartParser, FormParser])
    def upload_image(self, request):
        """
        GET  /images/upload-image/ - List all images
        POST /images/upload-image/ - Upload image asynchronously
        """
        if request.method == 'GET':
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        if request.method == 'POST':
            image_file = request.FILES.get('image')
            if not image_file:
                return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate image
            errors = validate_image(image_file, size_limit_mb=10)
            if errors:
                return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

            # Save to temp file
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
            temp_path = save_temp_file(image_file, temp_dir)

            # Create record with pending status
            instance = UploadImage.objects.create(status='pending')

            # Send to Celery for background processing
            tasks.upload_image_task.delay(str(instance.id), temp_path, image_file.name)

            # Return response immediately
            return Response({
                'id': str(instance.id),
                'status': 'pending',
                'message': 'شكرًا لك على رفع الصورة! جاري المعالجة...'
            }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['get'], url_path='download-image')
    def download_image(self, request, pk=None):
        """
        GET /images/{id}/download-image/ - Download image
        """
        image = self.get_object()

        if not image.image:
            return Response({'error': 'Image not ready yet'}, status=status.HTTP_404_NOT_FOUND)

        if image.status != 'completed':
            return Response({
                'error': 'Image still processing',
                'status': image.status
            }, status=status.HTTP_202_ACCEPTED)

        file_path = image.image.path
        filename = os.path.basename(file_path)

        response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
        return response

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /images/{id}/ - Delete image (file + database record)
        """
        image = self.get_object()

        # Delete the file from storage if it exists
        if image.image:
            file_path = image.image.path
            if os.path.exists(file_path):
                os.remove(file_path)

        # Delete the database record
        image.delete()

        return Response({
            'message': 'تم حذف الصورة بنجاح'
        }, status=status.HTTP_204_NO_CONTENT)

