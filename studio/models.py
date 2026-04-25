from django.db import models
from django.utils import timezone
import uuid

class Account(models.Model):
    """
    Represents a tenant/creator using the Telegram bot.
    Approvals are managed via the central YouTube Approvals Bot.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('expired', 'Disapproved (Expired)'),
        ('rejected', 'Rejected'),
    ]

    KEY_MODE_CHOICES = [
        ('own_keys', 'Use Own Keys'),
        ('platform_keys', 'Use Platform Keys'),
    ]

    telegram_chat_id = models.CharField(max_length=100, unique=True)
    telegram_username = models.CharField(max_length=100, null=True, blank=True)
    bot_token = models.CharField(max_length=255, null=True, blank=True, help_text="Custom bot token if they bring their own bot")
    openai_api_key = models.CharField(max_length=255, null=True, blank=True)
    gemini_api_key = models.CharField(max_length=255, null=True, blank=True)
    kling_api_token = models.CharField(max_length=255, null=True, blank=True)
    elevenlabs_api_key = models.CharField(max_length=255, null=True, blank=True)
    lightning_address = models.CharField(max_length=255, null=True, blank=True)
    wallet_connect_uri = models.CharField(max_length=1000, null=True, blank=True)
    key_mode = models.CharField(max_length=20, choices=KEY_MODE_CHOICES, default='own_keys')
    subscription_paid_until = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.telegram_username or self.telegram_chat_id} ({self.status})"

    def is_subscription_active(self):
        return self.subscription_paid_until is not None and self.subscription_paid_until > timezone.now()

    def has_all_own_provider_keys(self):
        return all([
            self.openai_api_key,
            self.gemini_api_key,
            self.kling_api_token,
            self.elevenlabs_api_key,
        ])

class Influencer(models.Model):
    """
    The core character. Character consistency relies on passing these base images
    and traits to Gemini 3.1 Flash / Kling.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='influencers')
    name = models.CharField(max_length=100)
    
    # Core reference images for Gemini character consistency (up to 4 allowed by Gemini)
    base_image_url_1 = models.URLField(max_length=1000)
    base_image_url_2 = models.URLField(max_length=1000, null=True, blank=True)
    
    # Extracted traits by LLM upon creation to maintain "aura" and "personality"
    traits = models.JSONField(default=dict, help_text="Stores age, race, gender, hair_color, vibe, etc.")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.account.telegram_username}"

class MediaAsset(models.Model):
    """
    Tracks all generated images and videos for the dashboard.
    """
    INTENT_CHOICES = [
        ('make', 'Make Influencer'),
        ('add', 'Add Influencer'),
        ('tweak', 'Tweak Influencer'),
        ('scene', 'Generate Scene'),
        ('video', 'Turn to Video'),
        ('reference', 'Reference Apply'),
        ('edit', 'Edit Image'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    influencer = models.ForeignKey(Influencer, on_delete=models.CASCADE, related_name='assets')
    intent_type = models.CharField(max_length=20, choices=INTENT_CHOICES)
    
    # Inputs
    user_prompt = models.TextField()
    llm_enhanced_prompt = models.TextField(null=True, blank=True)
    input_reference_image = models.URLField(max_length=1000, null=True, blank=True)
    input_reference_video = models.URLField(max_length=1000, null=True, blank=True)
    narration_text = models.TextField(null=True, blank=True, help_text="Text to be spoken over the video")
    
    # Output
    media_type = models.CharField(max_length=10, choices=[('image', 'Image'), ('video', 'Video')])
    output_url = models.URLField(max_length=1000, null=True, blank=True)
    status = models.CharField(max_length=20, default='processing') # processing, success, failed
    
    # Provider Info
    provider = models.CharField(max_length=50, help_text="e.g., gemini-3.1-flash, kling-v2-6, gpt-image-2")
    provider_task_id = models.CharField(max_length=255, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

class WebOTP(models.Model):
    """
    For frontend dashboard login via Telegram Bot.
    """
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()


class PaymentReceipt(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='payment_receipts')
    image = models.ImageField(upload_to='payment_receipts/')
    sats_amount = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    analysis = models.JSONField(default=dict, blank=True)
    reviewer_note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Receipt {self.id} - {self.account.telegram_chat_id} ({self.status})"
