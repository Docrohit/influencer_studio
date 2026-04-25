from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_chat_id', models.CharField(max_length=100, unique=True)),
                ('telegram_username', models.CharField(blank=True, max_length=100, null=True)),
                ('bot_token', models.CharField(blank=True, help_text='Custom bot token if they bring their own bot', max_length=255, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending Approval'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Influencer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('base_image_url_1', models.URLField(max_length=1000)),
                ('base_image_url_2', models.URLField(blank=True, max_length=1000, null=True)),
                ('traits', models.JSONField(default=dict, help_text='Stores age, race, gender, hair_color, vibe, etc.')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='influencers', to='studio.account')),
            ],
        ),
        migrations.CreateModel(
            name='MediaAsset',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('intent_type', models.CharField(choices=[('make', 'Make Influencer'), ('add', 'Add Influencer'), ('tweak', 'Tweak Influencer'), ('scene', 'Generate Scene'), ('video', 'Turn to Video'), ('reference', 'Reference Apply'), ('edit', 'Edit Image')], max_length=20)),
                ('user_prompt', models.TextField()),
                ('llm_enhanced_prompt', models.TextField(blank=True, null=True)),
                ('input_reference_image', models.URLField(blank=True, max_length=1000, null=True)),
                ('input_reference_video', models.URLField(blank=True, max_length=1000, null=True)),
                ('narration_text', models.TextField(blank=True, help_text='Text to be spoken over the video', null=True)),
                ('media_type', models.CharField(choices=[('image', 'Image'), ('video', 'Video')], max_length=10)),
                ('output_url', models.URLField(blank=True, max_length=1000, null=True)),
                ('status', models.CharField(default='processing', max_length=20)),
                ('provider', models.CharField(help_text='e.g., gemini-3.1-flash, kling-v2-6, gpt-image-2', max_length=50)),
                ('provider_task_id', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('influencer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assets', to='studio.influencer')),
            ],
        ),
        migrations.CreateModel(
            name='WebOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('otp_code', models.CharField(max_length=6)),
                ('expires_at', models.DateTimeField()),
                ('is_used', models.BooleanField(default=False)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='studio.account')),
            ],
        ),
    ]
