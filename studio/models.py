from django.db import models
from django.utils import timezone
import uuid

class Account(models.fields.Model):
    """
    Represents a tenant/creator using the Telegram bot.
    Approvals are managed via the central YouTube Approvals Bot.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    telegram_chat_id = models.CharField(max_length=100, unique=True)
    telegram_username = models.CharField(max_length=100, null=True, blank=True)
    bot_token = models.CharField(max_length=255, null=True, blank=True, help_text="Custom bot token if they bring their own bot")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.telegram_username or self.telegram_chat_id} ({self.status})"

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
