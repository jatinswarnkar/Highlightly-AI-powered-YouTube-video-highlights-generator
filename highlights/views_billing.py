import razorpay
import hmac
import hashlib
import json
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Profile

# Initialise Razorpay client
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

# Plan ID mapping
RAZORPAY_PLAN_IDS = {
    "pro": settings.RAZORPAY_PLAN_ID_PRO,
    "agency": settings.RAZORPAY_PLAN_ID_AGENCY,
}


def pricing_view(request):
    """Render a standalone pricing page for upgrades."""
    return render(request, "highlights/pricing.html", {
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
    })


@login_required
def create_subscription(request, plan):
    """
    Create a Razorpay Subscription for the given plan.
    Returns JSON with subscription_id for the frontend checkout popup.
    """
    if plan not in RAZORPAY_PLAN_IDS:
        return JsonResponse({"error": "Invalid plan selected"}, status=400)

    plan_id = RAZORPAY_PLAN_IDS[plan]
    if not plan_id:
        return JsonResponse(
            {"error": "Plan not configured. Please set RAZORPAY_PLAN_ID in .env"},
            status=500,
        )

    try:
        subscription = razorpay_client.subscription.create({
            "plan_id": plan_id,
            "total_count": 12,  # 12 billing cycles (1 year of monthly)
            "quantity": 1,
            "notes": {
                "plan_type": plan,
                "user_id": str(request.user.id),
                "email": request.user.email or "",
            },
        })

        return JsonResponse({
            "subscription_id": subscription["id"],
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "plan": plan,
            "user_name": request.user.get_full_name() or request.user.username,
            "user_email": request.user.email or "",
        })

    except Exception as e:
        print(f"Razorpay Subscription Error: {str(e)}")
        return JsonResponse(
            {"error": "Unable to create subscription. Please try again."},
            status=500,
        )


@login_required
@csrf_exempt
def verify_payment(request):
    """
    Verify the Razorpay payment signature after checkout.
    Activates the user's plan on successful verification.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_subscription_id = data.get("razorpay_subscription_id")
    razorpay_signature = data.get("razorpay_signature")
    plan_type = data.get("plan_type", "pro")

    if not all([razorpay_payment_id, razorpay_subscription_id, razorpay_signature]):
        return JsonResponse({"error": "Missing payment details"}, status=400)

    # Verify signature using HMAC SHA256
    # For subscriptions: generated_signature = hmac_sha256(payment_id + "|" + subscription_id, secret)
    generated_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        f"{razorpay_payment_id}|{razorpay_subscription_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if generated_signature != razorpay_signature:
        return JsonResponse({"error": "Payment verification failed"}, status=400)

    # Signature verified — activate the plan
    profile = request.user.profile
    profile.plan = plan_type
    profile.razorpay_subscription_id = razorpay_subscription_id
    profile.save()

    return JsonResponse({
        "success": True,
        "plan": plan_type,
        "redirect_url": reverse("checkout_success"),
    })


@login_required
def checkout_success(request):
    return render(request, "highlights/checkout_success.html")


@login_required
def checkout_cancel(request):
    return render(request, "highlights/checkout_cancel.html")


@csrf_exempt
def razorpay_webhook(request):
    """
    Webhook endpoint for Razorpay to notify about subscription lifecycle events.
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    payload = request.body
    sig_header = request.META.get("HTTP_X_RAZORPAY_SIGNATURE", "")
    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

    # Verify webhook signature
    if webhook_secret:
        expected_signature = hmac.new(
            webhook_secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, sig_header):
            return HttpResponse(status=400)

    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    event_type = event.get("event", "")

    if event_type == "subscription.activated":
        handle_subscription_activated(event)
    elif event_type == "subscription.charged":
        handle_subscription_charged(event)
    elif event_type in ("subscription.cancelled", "subscription.completed"):
        handle_subscription_ended(event)

    return HttpResponse(status=200)


def handle_subscription_activated(event):
    """Handle when a subscription becomes active."""
    entity = event.get("payload", {}).get("subscription", {}).get("entity", {})
    sub_id = entity.get("id")
    notes = entity.get("notes", {})
    plan_type = notes.get("plan_type", "pro")
    user_id = notes.get("user_id")

    if user_id:
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(id=int(user_id))
            profile = user.profile
            profile.plan = plan_type
            profile.razorpay_subscription_id = sub_id
            profile.save()
        except (User.DoesNotExist, ValueError):
            pass


def handle_subscription_charged(event):
    """Handle recurring charge — keep subscription active."""
    # Subscription continues, nothing special needed unless you track invoices
    pass


def handle_subscription_ended(event):
    """Handle when a subscription is cancelled or completed."""
    entity = event.get("payload", {}).get("subscription", {}).get("entity", {})
    sub_id = entity.get("id")

    if sub_id:
        try:
            profile = Profile.objects.get(razorpay_subscription_id=sub_id)
            profile.plan = "free"
            profile.razorpay_subscription_id = None
            profile.save()
        except Profile.DoesNotExist:
            pass
