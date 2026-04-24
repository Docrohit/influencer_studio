import random
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timedelta
from .models import Account, WebOTP, MediaAsset
from .tasks import send_telegram_message

def generate_otp():
    return str(random.randint(100000, 999999))

def login_view(request):
    """
    Step 1: User enters their Telegram Chat ID.
    System generates a 6-digit OTP and sends it via Telegram Bot.
    """
    if request.method == 'POST':
        chat_id = request.POST.get('chat_id')
        try:
            account = Account.objects.get(telegram_chat_id=chat_id, status='approved')
            
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
            
        except Account.DoesNotExist:
            return render(request, 'studio/login.html', {'error': 'Account not found or not approved.'})

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
                
                request.session['account_id'] = str(account.id)
                request.session['chat_id'] = chat_id
                
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
    influencer = account.influencers.filter(is_active=True).first()
    assets = MediaAsset.objects.filter(influencer__account=account).order_by('-created_at')

    return render(request, 'studio/dashboard.html', {
        'account': account,
        'influencer': influencer,
        'assets': assets
    })

def logout_view(request):
    request.session.flush()
    return redirect('login')
