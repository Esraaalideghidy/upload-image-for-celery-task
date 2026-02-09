from .models import UploadImage
from rest_framework import serializers


class UploadImageRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadImage
        fields = ['id', 'image', 'uploaded_at', 'status']

class UploadImageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadImage
        fields = ['image']