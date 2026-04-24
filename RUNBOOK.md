# Influencer Studio - Runbook

## 1. Environment Setup

Create a `.env` file in the `influencer_studio` root directory (next to `manage.py`):

```env
# AI APIs
OPENAI_API_KEY="sk-..."
GEMINI_API_KEY="AIza..."
KLING_API_TOKEN="ey..."
ELEVENLABS_API_KEY="sk_d3bd0076eaaec57aa2951f13b6b0fbc53c52802d20d58e6d"

# Telegram Bots
TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjkl..."
APPROVAL_BOT_TOKEN="987654321:ZYXwvuTSRqpo..."
APPROVAL_CHAT_ID="your_admin_chat_id"

# Django settings
DJANGO_SECRET_KEY="your-secret-key"
DEBUG=True
```

## 2. Dependencies
Install the required Python packages and ensure `ffmpeg` is installed on your system (for merging video and audio).

1. Install Python packages:
   ```bash
   pip install django celery redis requests openai google-genai pillow python-dotenv
   ```
2. Install FFmpeg (Mac):
   ```bash
   brew install ffmpeg
   ```
3. Make migrations and migrate the database:
   ```bash
   python manage.py makemigrations studio
   python manage.py migrate
   ```
3. Create a superuser (optional, for admin panel):
   ```bash
   python manage.py createsuperuser
   ```

## 3. Running the Application

You will need 3 terminal windows to run the full stack locally:

**Terminal 1: Redis Server (for Celery)**
```bash
redis-server
```

**Terminal 2: Celery Worker**
```bash
celery -A influencer_studio worker -l INFO
```

**Terminal 3: Django Dev Server**
```bash
python manage.py runserver
```

## 4. Webhooks (Local Testing)
Since Telegram and Kling require public URLs to hit your webhooks, you must use a tunneling service like Ngrok or Cloudflare Tunnels locally.

```bash
ngrok http 8000
```
*Copy the `https://xxxx.ngrok.app` URL.*

1. **Set Telegram Webhook:**
   In your browser, visit:
   `https://api.telegram.org/bot<YOUR_TELEGRAM_BOT_TOKEN>/setWebhook?url=https://xxxx.ngrok.app/api/telegram/webhook/`

2. **Kling Callbacks:**
   When triggering Kling via the API (in `tasks.py`), ensure you pass your ngrok URL to the `callback_url` parameter:
   `callback_url="https://xxxx.ngrok.app/api/kling/callback/"`

## 5. Usage Flow

1. Open your Telegram bot and press `/start` or send any message.
2. The bot will tell you your account is pending.
3. The Admin Bot will receive a ping. (Approve via n8n or manually set your account status to 'approved' in the Django shell).
4. Send an image to the bot and say: `"Use this and save her as Maaya"`.
5. The LLM will parse this as `ADD_INFLUENCER` and save Maaya to your account.
6. Send a text message: `"Make her walk in a ballroom"`.
7. The LLM parses this as `GENERATE_SCENE`, calls Gemini Nano Banana, and sends the picture back.
8. Go to `http://localhost:8000/`, enter your Telegram Chat ID, get the OTP from the bot, and view your gallery!
