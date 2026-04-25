from django.urls import path
from . import views, dashboard_views

urlpatterns = [
    # Telegram Webhooks & API callbacks
    path('api/telegram/webhook/', views.telegram_webhook, name='telegram_webhook'),
    path('api/telegram/webhook/<str:custom_chat_id>/', views.telegram_webhook, name='custom_telegram_webhook'),
    path('api/kling/callback/', views.kling_callback, name='kling_callback'),
    path('api/admin/approval/', views.admin_approve_account, name='admin_approval'),
    
    # Web Dashboard
    path('', dashboard_views.login_view, name='login'),
    path('register/', dashboard_views.register_view, name='register'),
    path('billing/', dashboard_views.billing_view, name='billing'),
    path('verify/', dashboard_views.verify_otp_view, name='verify_otp'),
    path('dashboard/', dashboard_views.dashboard_view, name='dashboard'),
    path('logout/', dashboard_views.logout_view, name='logout'),
]
