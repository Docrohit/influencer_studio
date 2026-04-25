from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('studio', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='openai_api_key',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='account',
            name='gemini_api_key',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='account',
            name='kling_api_token',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='account',
            name='elevenlabs_api_key',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='account',
            name='lightning_address',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='account',
            name='wallet_connect_uri',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='account',
            name='key_mode',
            field=models.CharField(choices=[('own_keys', 'Use Own Keys'), ('platform_keys', 'Use Platform Keys')], default='own_keys', max_length=20),
        ),
        migrations.AddField(
            model_name='account',
            name='subscription_paid_until',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='account',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending Approval'), ('approved', 'Approved'), ('expired', 'Disapproved (Expired)'), ('rejected', 'Rejected')], default='pending', max_length=20),
        ),
        migrations.CreateModel(
            name='PaymentReceipt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='payment_receipts/')),
                ('sats_amount', models.PositiveIntegerField(default=0)),
                ('status', models.CharField(choices=[('pending', 'Pending Review'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('analysis', models.JSONField(blank=True, default=dict)),
                ('reviewer_note', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_receipts', to='studio.account')),
            ],
        ),
    ]
