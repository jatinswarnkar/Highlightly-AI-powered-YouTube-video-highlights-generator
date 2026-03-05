# Generated manually for Razorpay migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('highlights', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='stripe_customer_id',
            new_name='razorpay_customer_id',
        ),
        migrations.RenameField(
            model_name='profile',
            old_name='stripe_subscription_id',
            new_name='razorpay_subscription_id',
        ),
    ]
