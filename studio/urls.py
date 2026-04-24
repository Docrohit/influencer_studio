from django.urls import path
from . import views, dashboard_views

urlpatterns = [
    # Telegram Webhooks & API callbacks
    path('api/telegram/webhook/', views.telegram_webhook, name='telegram_webhook'),
    path('api/kling/callback/', views.kling_callback, name='kling_callback'),
    path('api/admin/approval/', views.admin_approve_account, name='admin_approval'),
    
    # Web Dashboard
    path('', dashboard_views.login_view, name='login'),
    path('verify/', dashboard_views.verify_otp_view, name='verify_otp'),
    path('dashboard/', dashboard_views.dashboard_view, name='dashboard'),
    path('logout/', dashboard_views.logout_view, name='logout'),
]