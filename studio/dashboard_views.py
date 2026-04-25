import random
import hashlib
import re
import os
from urllib.parse import urlencode
from django.shortcuts import render, redirect
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta, timezone as dt_timezone
from .models import Account, WebOTP, MediaAsset, PaymentReceipt
from .tasks import send_telegram_message
from .payment_service import analyze_ln_receipt

PROVIDER_KEY_FIELDS = (
    "openai_api_key",
    "gemini_api_key",
    "kling_api_token",
    "elevenlabs_api_key",
)

PROVIDER_KEY_LABELS = {
    "openai_api_key": "OpenAI",
    "gemini_api_key": "Gemini",
    "kling_api_token": "Kling",
    "elevenlabs_api_key": "ElevenLabs",
}


def _collect_provider_keys_from_post(request):
    provider_keys = {}
    for field in PROVIDER_KEY_FIELDS:
        value = (request.POST.get(field) or "").strip()
        if value:
            provider_keys[field] = value
    return provider_keys


def _subscription_price_for_mode(key_mode):
    if key_mode == 'platform_keys':
        return settings.PLATFORM_KEYS_PRICE_SATS
    return settings.OWN_KEYS_PRICE_SATS


def _normalize_key_mode(raw_value):
    if raw_value == 'platform_keys':
        return 'platform_keys'
    return 'own_keys'


def _normalize_payment_method(raw_value):
    if raw_value == 'cash':
        return 'cash'
    return 'lightning'


def _is_owner_chat_id(chat_id):
    value = str(chat_id or '').strip()
    if not value:
        return False
    candidates = {
        str(getattr(settings, 'TELEGRAM_CHAT_ID', '') or '').strip(),
        str(getattr(settings, 'APPROVAL_CHAT_ID', '') or '').strip(),
        str(os.environ.get('TELEGRAM_CHAT_ID', '') or '').strip(),
        str(os.environ.get('APPROVAL_CHAT_ID', '') or '').strip(),
    }
    candidates.discard('')
    return value in candidates


def _file_sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_receipt_token(value):
    return re.sub(r'[^a-z0-9]', '', str(value or '').lower())


def _receipt_is_recent(analysis, max_age_days):
    raw_iso = str((analysis or {}).get('receipt_datetime_iso') or '').strip()
    if not raw_iso:
        return bool((analysis or {}).get('is_recent_receipt'))

    try:
        parsed = datetime.fromisoformat(raw_iso.replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt_timezone.utc)
        now = timezone.now()
        age = now - parsed.astimezone(dt_timezone.utc)
        if age.total_seconds() < -600:
            return False
        return age <= timedelta(days=max_age_days)
    except Exception:
        return bool((analysis or {}).get('is_recent_receipt'))


def _duplicate_receipt_reason(current_receipt_id, receipt_sha256, invoice_or_hash):
    normalized_invoice = _normalize_receipt_token(invoice_or_hash)
    prior = PaymentReceipt.objects.filter(status='approved').exclude(id=current_receipt_id)
    for receipt in prior.only('id', 'analysis'):
        prev = receipt.analysis or {}
        if receipt_sha256 and prev.get('receipt_sha256') == receipt_sha256:
            return 'This receipt screenshot was already used for a previous subscription.'
        prev_invoice = _normalize_receipt_token(prev.get('detected_invoice_or_hash'))
        if normalized_invoice and prev_invoice and normalized_invoice == prev_invoice:
            return 'This Lightning payment hash/invoice was already used previously.'
    return ''


def _expire_subscription_if_needed(account):
    if account.status != 'approved':
        return

    if account.subscription_paid_until is None or account.subscription_paid_until <= timezone.now():
        account.status = 'expired'
        account.save(update_fields=['status'])


def _resolve_account_for_auth(chat_id):
    account = Account.objects.filter(telegram_chat_id=chat_id).first()
    if not account:
        return None, 'Account not found. Please register first.'

    if account.status == 'rejected':
        return None, 'Your account access was rejected by admin.'

    if account.status == 'pending':
        return None, 'Your account is pending admin approval.'

    return account, None

def register_view(request):
    """
    Allow users to input their Chat ID and their custom Bot Token.
    Triggers approval flow to the Admin.
    """
    if request.method == 'POST':
        chat_id = (request.POST.get('chat_id') or '').strip()
        bot_token = (request.POST.get('bot_token') or '').strip()
        selected_key_mode = _normalize_key_mode(request.POST.get('key_mode'))
        provider_keys = _collect_provider_keys_from_post(request)

        context = {
            'chat_id': chat_id,
            'bot_token': bot_token,
            'selected_key_mode': selected_key_mode,
            'platform_price_sats': settings.PLATFORM_KEYS_PRICE_SATS,
            'own_price_sats': settings.OWN_KEYS_PRICE_SATS,
        }

        if not chat_id or not bot_token:
            context['error'] = 'Telegram Chat ID and Bot Token are required.'
            return render(request, 'studio/register.html', context)

        # Create or update account
        account, created = Account.objects.get_or_create(
            telegram_chat_id=chat_id,
            defaults={'bot_token': bot_token, 'status': 'pending', 'key_mode': selected_key_mode}
        )

        if selected_key_mode == 'own_keys':
            unresolved_fields = [
                field for field in PROVIDER_KEY_FIELDS
                if not (provider_keys.get(field) or getattr(account, field))
            ]
            if unresolved_fields:
                missing_labels = ', '.join(PROVIDER_KEY_LABELS[field] for field in unresolved_fields)
                context['error'] = f'Please add your API keys for own mode: {missing_labels}.'
                return render(request, 'studio/register.html', context)

        # If it already existed but they are updating the token
        changed_fields = []
        if not created:
            if account.bot_token != bot_token:
                account.bot_token = bot_token
                changed_fields.append('bot_token')
            if account.status != 'pending':
                account.status = 'pending'
                changed_fields.append('status')

        if account.key_mode != selected_key_mode:
            account.key_mode = selected_key_mode
            changed_fields.append('key_mode')

        for field, value in provider_keys.items():
            if getattr(account, field) != value:
                setattr(account, field, value)
                changed_fields.append(field)

        if changed_fields:
            account.save(update_fields=changed_fields)
            
        # Ping Admin for approval
        from .views import trigger_admin_approval_request
        trigger_admin_approval_request(account)
        
        return render(request, 'studio/register.html', {
            'message': 'Success! Your request has been sent to the admin. Once approved, your bot will be automatically linked.',
            'selected_key_mode': selected_key_mode,
            'platform_price_sats': settings.PLATFORM_KEYS_PRICE_SATS,
            'own_price_sats': settings.OWN_KEYS_PRICE_SATS,
        })

    return render(request, 'studio/register.html', {
        'selected_key_mode': 'platform_keys',
        'platform_price_sats': settings.PLATFORM_KEYS_PRICE_SATS,
        'own_price_sats': settings.OWN_KEYS_PRICE_SATS,
    })

def generate_otp():
    return str(random.randint(100000, 999999))

def login_view(request):
    """
    Step 1: User enters their Telegram Chat ID.
    System generates a 6-digit OTP and sends it via Telegram Bot.
    """
    if request.method == 'POST':
        chat_id = (request.POST.get('chat_id') or '').strip()
        account, error = _resolve_account_for_auth(chat_id)
        if error:
            return render(request, 'studio/login.html', {
                'error': error,
                'chat_id': chat_id,
            })

        _expire_subscription_if_needed(account)

        if not account.is_subscription_active() or account.status != 'approved':
            query = urlencode({'chat_id': chat_id, 'key_mode': account.key_mode})
            return redirect(f"/billing/?{query}")

        # Invalidate old OTPs
        WebOTP.objects.filter(account=account, is_used=False).update(is_used=True)

        # Generate new OTP
        otp = generate_otp()
        WebOTP.objects.create(
            account=account,
            otp_code=otp,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        # Send via Telegram
        send_telegram_message(chat_id, f"🔐 Your Influencer Studio Web Login Code is: {otp}\n\nThis code expires in 10 minutes.")

        # Set chat_id in session for the next step
        request.session['pending_chat_id'] = chat_id
        return redirect('verify_otp')

    return render(request, 'studio/login.html')

def verify_otp_view(request):
    """
    Step 2: User enters the 6-digit OTP they received on Telegram.
    """
    chat_id = request.session.get('pending_chat_id')
    if not chat_id:
        return redirect('login')

    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        try:
            account = Account.objects.get(telegram_chat_id=chat_id)
            valid_otp = WebOTP.objects.filter(
                account=account, 
                otp_code=otp_input, 
                is_used=False, 
                expires_at__gt=timezone.now()
            ).first()

            if valid_otp:
                # Success! Mark used and log them in
                valid_otp.is_used = True
                valid_otp.save()

                if not account.is_subscription_active() or account.status != 'approved':
                    return redirect(f"/billing/?{urlencode({'chat_id': chat_id, 'key_mode': account.key_mode})}")
                
                request.session['account_id'] = str(account.id)
                request.session['chat_id'] = chat_id
                request.session.pop('pending_provider_keys', None)
                request.session.pop('pending_key_mode', None)
                
                return redirect('dashboard')
            else:
                return render(request, 'studio/verify_otp.html', {'error': 'Invalid or expired OTP.'})
                
        except Account.DoesNotExist:
            return redirect('login')

    return render(request, 'studio/verify_otp.html', {'chat_id': chat_id})

def dashboard_view(request):
    """
    Step 3: The main gallery/dashboard.
    Shows the user's active influencer and all generated media assets.
    """
    account_id = request.session.get('account_id')
    if not account_id:
        return redirect('login')
        
    account = Account.objects.get(id=account_id)
    _expire_subscription_if_needed(account)
    if account.status != 'approved':
        request.session.flush()
        return redirect(f"/billing/?{urlencode({'chat_id': account.telegram_chat_id, 'key_mode': account.key_mode})}")

    influencer = account.influencers.filter(is_active=True).first()
    assets = MediaAsset.objects.filter(influencer__account=account).order_by('-created_at')

    return render(request, 'studio/dashboard.html', {
        'account': account,
        'influencer': influencer,
        'assets': assets,
        'platform_price_sats': settings.PLATFORM_KEYS_PRICE_SATS,
        'own_price_sats': settings.OWN_KEYS_PRICE_SATS,
    })


def billing_view(request):
    chat_id = (request.GET.get('chat_id') or request.POST.get('chat_id') or '').strip()
    selected_key_mode = _normalize_key_mode(request.GET.get('key_mode') or request.POST.get('key_mode'))
    selected_payment_method = _normalize_payment_method(request.GET.get('payment_method') or request.POST.get('payment_method'))
    lightning_address = (request.GET.get('lightning_address') or request.POST.get('lightning_address') or '').strip()
    wallet_connect_uri = (request.GET.get('wallet_connect_uri') or request.POST.get('wallet_connect_uri') or '').strip()

    context = {
        'chat_id': chat_id,
        'selected_key_mode': selected_key_mode,
        'selected_payment_method': selected_payment_method,
        'platform_price_sats': settings.PLATFORM_KEYS_PRICE_SATS,
        'own_price_sats': settings.OWN_KEYS_PRICE_SATS,
        'subscription_days': settings.SUBSCRIPTION_DURATION_DAYS,
        'payment_payee': settings.PLATFORM_PAYMENT_PAYEE,
        'ln_invoice': settings.PLATFORM_LN_INVOICE,
        'ln_qr_image_url': settings.PLATFORM_LN_QR_IMAGE_URL,
        'lightning_address': lightning_address,
        'wallet_connect_uri': wallet_connect_uri,
    }

    if request.method == 'POST':
        receipt_image = request.FILES.get('receipt_image')
        if not chat_id:
            context['error'] = 'Please enter your Telegram Chat ID.'
            return render(request, 'studio/billing.html', context)

        account, error = _resolve_account_for_auth(chat_id)
        if error:
            context['error'] = error
            return render(request, 'studio/billing.html', context)

        account_updates = []
        if lightning_address and account.lightning_address != lightning_address:
            account.lightning_address = lightning_address
            account_updates.append('lightning_address')
        if wallet_connect_uri and account.wallet_connect_uri != wallet_connect_uri:
            account.wallet_connect_uri = wallet_connect_uri
            account_updates.append('wallet_connect_uri')
        if account_updates:
            account.save(update_fields=account_updates)

        if selected_payment_method == 'cash':
            now = timezone.now()
            if _is_owner_chat_id(chat_id):
                previous_mode = account.key_mode
                previous_expiry = account.subscription_paid_until

                account.key_mode = selected_key_mode
                account.status = 'approved'
                if previous_mode == selected_key_mode and previous_expiry and previous_expiry > now:
                    base_time = previous_expiry
                else:
                    base_time = now
                account.subscription_paid_until = base_time + timedelta(days=settings.SUBSCRIPTION_DURATION_DAYS)
                account.save(update_fields=['key_mode', 'status', 'subscription_paid_until'])

                send_telegram_message(
                    chat_id,
                    f"✅ Cash payment marked by admin. Subscription active until {account.subscription_paid_until.strftime('%Y-%m-%d %H:%M UTC')}.",
                )
                context['message'] = (
                    f'Cash payment recorded. Subscription active until '
                    f'{account.subscription_paid_until.strftime("%Y-%m-%d %H:%M UTC")}. '
                    'You can login now.'
                )
                return render(request, 'studio/billing.html', context)

            account.key_mode = selected_key_mode
            account.status = 'pending'
            account.save(update_fields=['key_mode', 'status'])
            from .views import trigger_admin_approval_request
            trigger_admin_approval_request(
                account,
                extra_payload={
                    'event': 'cash_payment',
                    'payment_method': 'cash',
                    'requested_key_mode': selected_key_mode,
                    'expected_sats': _subscription_price_for_mode(selected_key_mode),
                    'message': 'Cash payment submitted; approve to activate subscription renewal.',
                },
            )
            send_telegram_message(chat_id, '🧾 Cash payment request submitted. Waiting for admin approval.')
            context['message'] = 'Cash payment marked. Waiting for admin approval before activation.'
            return render(request, 'studio/billing.html', context)

        if not receipt_image:
            context['error'] = 'Please upload your Lightning payment receipt image.'
            return render(request, 'studio/billing.html', context)

        expected_sats = _subscription_price_for_mode(selected_key_mode)
        max_age_days = int(getattr(settings, 'PAYMENT_RECEIPT_MAX_AGE_DAYS', 2))
        receipt = PaymentReceipt.objects.create(
            account=account,
            image=receipt_image,
            status='pending',
        )

        try:
            analysis = analyze_ln_receipt(
                image_path=receipt.image.path,
                expected_sats=expected_sats,
                expected_payee=settings.PLATFORM_PAYMENT_PAYEE,
                expected_invoice=settings.PLATFORM_LN_INVOICE,
                max_age_days=max_age_days,
            )
        except Exception as e:
            receipt.status = 'rejected'
            receipt.reviewer_note = f'Auto-review error: {e}'
            receipt.reviewed_at = timezone.now()
            receipt.save(update_fields=['status', 'reviewer_note', 'reviewed_at'])
            context['error'] = f'Unable to verify receipt automatically: {e}'
            return render(request, 'studio/billing.html', context)

        raw_detected_amount = str(analysis.get('detected_amount_sats') or '0')
        normalized_amount = ''.join(ch for ch in raw_detected_amount if ch.isdigit())
        detected_amount = int(normalized_amount or 0)
        receipt_sha256 = _file_sha256(receipt.image.path)
        analysis['receipt_sha256'] = receipt_sha256
        analysis['max_age_days_enforced'] = max_age_days
        recent_receipt = _receipt_is_recent(analysis, max_age_days=max_age_days)
        duplicate_reason = _duplicate_receipt_reason(
            current_receipt_id=receipt.id,
            receipt_sha256=receipt_sha256,
            invoice_or_hash=analysis.get('detected_invoice_or_hash'),
        )
        is_approved = (
            bool(analysis.get('is_valid_payment'))
            and bool(analysis.get('payment_completed'))
            and bool(analysis.get('is_lightning_receipt'))
            and bool(analysis.get('payee_match'))
            and detected_amount >= expected_sats
            and recent_receipt
            and not duplicate_reason
        )

        if duplicate_reason:
            analysis['reason'] = duplicate_reason
        elif not recent_receipt:
            analysis['reason'] = (
                analysis.get('reason')
                or f'Receipt date is missing or too old. Upload a receipt from the last {max_age_days} day(s).'
            )

        now = timezone.now()
        receipt.analysis = analysis
        receipt.sats_amount = detected_amount
        receipt.reviewed_at = now

        if is_approved:
            previous_mode = account.key_mode
            previous_expiry = account.subscription_paid_until

            account.key_mode = selected_key_mode
            account.status = 'approved'

            if previous_mode == selected_key_mode and previous_expiry and previous_expiry > now:
                base_time = previous_expiry
            else:
                base_time = now

            account.subscription_paid_until = base_time + timedelta(days=settings.SUBSCRIPTION_DURATION_DAYS)
            account.save(update_fields=['key_mode', 'status', 'subscription_paid_until'])

            receipt.status = 'approved'
            receipt.reviewer_note = 'Auto-approved by Gemini receipt validation.'

            send_telegram_message(
                chat_id,
                (
                    f"✅ Payment verified: {detected_amount} sats. "
                    f"Your {selected_key_mode.replace('_', ' ')} subscription is active until "
                    f"{account.subscription_paid_until.strftime('%Y-%m-%d %H:%M UTC')}."
                ),
            )

            context['message'] = (
                f'Payment verified. Subscription active until '
                f'{account.subscription_paid_until.strftime("%Y-%m-%d %H:%M UTC")}. You can login now.'
            )
            if selected_key_mode == 'own_keys' and not account.has_all_own_provider_keys():
                context['message'] += ' Add your provider keys from registration before generating.'
        else:
            receipt.status = 'rejected'
            receipt.reviewer_note = analysis.get('reason') or 'Receipt did not pass verification checks.'
            if account.status == 'approved' and not account.is_subscription_active():
                account.status = 'expired'
                account.save(update_fields=['status'])

            send_telegram_message(
                chat_id,
                f"❌ We could not auto-verify your payment receipt. Upload a fresh receipt (within {max_age_days} day(s)) showing payee, amount in sats, successful transfer status, and date/time.",
            )
            context['error'] = receipt.reviewer_note

        receipt.save(update_fields=['analysis', 'sats_amount', 'reviewed_at', 'status', 'reviewer_note'])

    return render(request, 'studio/billing.html', context)

def logout_view(request):
    request.session.flush()
    return redirect('login')
