from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("start/", views.start_highlights, name="start_highlights"),
    path("progress/<str:job_id>/", views.check_progress),
    path("result/<str:job_id>/", views.job_result),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("signup/", views.signup_view, name="signup"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    
    # Billing
    path("pricing/", views.pricing_view, name="pricing"),
    path("api/create-subscription/<str:plan>/", views.create_subscription, name="create_subscription"),
    path("api/verify-payment/", views.verify_payment, name="verify_payment"),
    path("checkout/success/", views.checkout_success, name="checkout_success"),
    path("checkout/cancel/", views.checkout_cancel, name="checkout_cancel"),
    path("webhooks/razorpay/", views.razorpay_webhook, name="razorpay_webhook"),
    
    # Google OAuth shortcut
    path("auth/google/", RedirectView.as_view(url="/accounts/google/login/?process=login"), name="google_login"),
]
