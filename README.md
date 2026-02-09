# Upload Image for Celery Task

### 📝 Description
This Django project demonstrates **asynchronous image uploading** using Celery. Users can upload images without waiting for the upload or processing to complete. The system immediately responds with a confirmation message (`Thank you`) while the image is processed in the background.

---

### ⚙️ Features
-Upload images asynchronously with Django + Celery using Redis in Docker.
-Immediate response to users after upload request (no waiting).
-Background processing of images (saving, resizing, validation).
-Download or view uploaded images.
-Demonstrates real-world use of task queues for long-running operations.

---

### 🛠️ Technologies Used
- Python 3.x
- Django 4.x
- Celery (Background Tasks)
- Redis / RabbitMQ (Celery broker)

---

### 📁 Project Structure

project/
├── project/ # Django project settings
├── upload_image/ # Django app for image upload
├── media/ # Uploaded images storage
├── manage.py # Django management script
├── requirements.txt # Project dependencies
├── .env # Environment variables (NOT included in repo)
└── .gitignore # Git ignore file
