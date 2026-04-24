# AI Influencer Studio - Product Spec

## Overview
A multi-tenant AI Media SaaS running via Telegram bots. Users upload a base image of an influencer and can generate highly consistent new scenes, edit attributes, apply reference images (clothing/poses), and generate videos (standard & motion-controlled).

## Core Intents (Telegram Bot)
1. **MAKE_INFLUENCER**: Register a new character base image and extract their defining traits/aura.
2. **TWEAK_INFLUENCER**: Edit base traits (race, age, gender, ethnicity, hair color, personality vibe).
3. **GENERATE_SCENE**: Place the influencer in new environments (sitting, walking, targeted demographic setups) using Gemini Nano Banana's character consistency (supports up to 4 reference characters).
4. **TURN_TO_VIDEO**: 
   - *Image2Video*: Animate a generated scene using Kling V2/V3.
   - *Motion Control*: Supply a generated scene + a reference video to copy movements exactly using Kling Motion Control.
5. **REFERENCE_APPLY**: Supply a reference image (clothes, room, holding object) and force the influencer into that context.
6. **EDIT_IMAGE**: Inpaint/Edit specific regions of an existing generation.

## Architecture
- **Backend**: Django 6.x + Celery + Redis + SQLite.
- **Image Generation**: Gemini 3.1 Flash Image Preview (for multi-image character consistency) & GPT-Image-2.
- **Video Generation**: Kling API (`/v1/videos/image2video` & `/v1/videos/motion-control`).
- **Web Frontend**: Django Templates + TailwindCSS (OTP login via Telegram Bot).
- **Automation**: n8n workflows for cross-service routing and optional webhook integrations.

## Database Models
- `Account`: Telegram user data, bot token, approval status.
- `Influencer`: The core character profile (base images, extracted traits JSON).
- `MediaAsset`: Generated images/videos, prompts, parent influencer.
- `WebOTP`: One-time passwords for web dashboard login.
