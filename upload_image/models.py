import uuid
from django.db import models

# Create your models here.


class UploadImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='pending')
    def __str__(self):
        return self.image.name
