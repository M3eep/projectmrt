from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='ocr-home'),
    path('about/', views.about, name='ocr-about'),
    path('upload/', views.upload, name='ocr-upload'),
]
