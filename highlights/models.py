from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    plan = models.CharField(max_length=20, default="free", choices=[("free", "Free"), ("pro", "Pro Creator"), ("agency", "Agency")])
    minutes_used = models.IntegerField(default=0)
    
    # Razorpay billing fields
    razorpay_customer_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_subscription_id = models.CharField(max_length=100, blank=True, null=True)

    def get_minutes_limit(self):
        if self.plan == "agency":
            return 600
        elif self.plan == "pro":
            return 150
        return 60 # Free tier

    def __str__(self):
        return f"{self.user.username} - {self.plan}"

# Signal to auto-create profile when a User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class HighlightClip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="clips")
    video_url = models.CharField(max_length=500)
    thumbnail_url = models.CharField(max_length=500, blank=True, null=True)
    ai_caption = models.TextField(blank=True, null=True)
    ai_hashtags = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Clip {self.id} for {self.user.username}"
