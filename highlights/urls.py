from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("start/", views.start_highlights, name="start_highlights"),
    path("progress/<str:job_id>/", views.check_progress),
    path("result/<str:job_id>/", views.job_result),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("signup/", views.signup_view, name="signup"),
]
