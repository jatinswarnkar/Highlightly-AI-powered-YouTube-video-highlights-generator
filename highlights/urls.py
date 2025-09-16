from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("start/", views.start_highlights, name="start_highlights"),
    path("progress/", views.check_progress, name="check_progress"),
]
