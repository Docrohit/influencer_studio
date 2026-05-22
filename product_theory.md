# Product Theory — AI Influencer Studio

> **Purpose:** The "why" behind the architecture. This app shares the same product vision as Moral Stories Studio (see `../product_theory.md`). Read both before touching code.

---

## What Does This Product Do?

AI Influencer Studio lets users create and control a consistent AI character ("influencer") via Telegram. Upload a base image, and the system generates new scenes with that character in different environments, outfits, and poses. Character consistency is maintained by passing reference images to Gemini 3.1 Flash. Users can also animate scenes into videos (image-to-video, motion control) and edit existing generations.

**Key users:** Content creators, marketers, influencers who want an AI character that looks consistent across all media.
**Key use cases:**
1. Register a character from a base image → extract traits (age, race, gender, vibe)
2. Generate new scenes ("walking in a ballroom", "sitting at a cafe")
3. Apply reference images (clothes, pose, background)
4. Turn scenes into videos (image-to-video or motion-controlled)
5. Edit/inpaint specific regions of generated images

---

## Why This Stack?

| Choice | Why | What We Avoided |
|--------|-----|-----------------|
| Django 4.2 | Same framework as Moral Stories. Consistent skills, admin, ORM. | New framework — unnecessary learning curve |
| Gemini 3.1 Flash | Best character consistency for multi-image reference generation (up to 4 ref images) | Stable Diffusion — requires GPU, character consistency is harder |
| Kling API | Image-to-video + Motion Control (copy movement from reference video) | Runway/Pika — no API at the time, motion control unique to Kling |
| Telegram Bot | Same UI pattern as Moral Stories. Users already in Telegram ecosystem. | Web dashboard — built but Telegram is primary interaction |
| SQLite | Zero-ops. Works on single server. Same DB pattern as Moral Stories. | Same reasoning — PostgreSQL is overkill for solo dev |
| Lightning Network | Built-in payment/subscription system via BTC Lightning | Stripe — more complex, fiat-only, higher fees |

---

## Why This Architecture?

### What Kind of System Is This?

| Pattern | Applied? | Where/How |
|---------|----------|-----------|
| Monolith | Yes | Single Django app `studio/` with models, views, services, tasks |
| Service Layer | Yes | `gemini_service.py`, `kling_service.py`, `voice_service.py` encapsulate provider APIs |
| Event-Driven | Partial | Celery tasks for async generation, Kling callback webhooks |
| BYOK (Bring Your Own Keys) | Yes | Each `Account` can store own API keys. Two modes: `own_keys` or `platform_keys` |

### Key Decisions & Their Rationale

| Date | Decision | Why | Trade-off |
|------|----------|-----|-----------|
| 2025 | Django + Celery same stack as Moral Stories | Skill reuse. Consistent deployment, debugging, admin panel. | Must maintain two Django projects on same server |
| 2025 | Gemini 3.1 Flash for character consistency | Gemini supports passing up to 4 reference images natively. Character stays consistent without fine-tuning. | Gemini can be inconsistent; still needs guardrails in prompts |
| 2025 | Lightning Network payments | BTC-native. No bank, no Stripe, no KYC. Low fees. | Users must understand Lightning. Smaller user base than credit card. |
| 2025 | BYOK architecture from day one | Tenants can use their own API keys (OpenAI, Gemini, Kling, ElevenLabs) or pay platform subscription for shared keys. | More complex key routing. Must validate keys on onboarding. |
| 2025 | Web dashboard + Telegram hybrid | Telegram for generation, web dashboard for gallery/browsing. OTP login via Telegram bot. | Two interfaces to maintain. OTP flow is fragile. |

---

## Layer Philosophy (The "Where Should This Go?" Guide)

1. **Does it handle HTTP requests/Telegram webhooks?** → `studio/views.py`
2. **Does it parse user intent from natural language?** → `studio/llm_parser.py`
3. **Does it call Gemini/Kling/ElevenLabs API?** → `studio/gemini_service.py`, `studio/kling_service.py`, `studio/voice_service.py`
4. **Does it need to run async (image/video gen takes minutes)?** → `studio/tasks.py`
5. **Does it handle payments/Lightning?** → `studio/payment_service.py`
6. **Does it serve the web dashboard?** → `studio/dashboard_views.py`

---

## Forbidden Patterns

| Pattern | Why Forbidden | What To Do Instead |
|---------|--------------|-------------------|
| Direct server edits | Drift. Lost on next deploy. | Push to main → GitHub Actions deploys |
| Hardcoded API keys | Security. Leaked on commit. | `.env` + `os.environ.get()` |
| Raw SQL | Bypasses ORM. Not portable. | Django ORM only |
| Skipping key validation on BYOK | Tenant will get cryptic API errors, think the system is broken | Validate all keys on submission with a test API call |
| Multi-tenant data leaks | Tenant A's images must never appear to Tenant B | Always filter by `account=` FK |

---

## The "Don't Build Against These" List (Future Plans)

| When | What's Changing | What You Should Do Today |
|------|----------------|-------------------------|
| 2026 | Agentic architecture across both apps — autonomous decision making for content | Keep services modular and independently testable |
| 2026 | PostgreSQL migration | Keep ORM queries clean. No raw SQL. |
| 2026 | Web dashboard enhancements (gallery, feed, analytics) | Keep API endpoints RESTful. Use templates/DRF consistently. |
| 2026 | More video providers beyond Kling (Veo, Seedance) | Abstract video generation behind a common interface |

---

## What Breaks Most Often?

| Area | Why It Breaks | What To Watch For |
|------|--------------|------------------|
| **Character consistency** | Gemini loses character traits when scene description is too different from reference | Always pass all reference images. Keep scene prompts aligned with base character traits. |
| **Kling video generation** | Timeouts, task status polling failures, balance exhaustion | Set reasonable timeouts. Handle all Kling task states (processing, succeeded, failed). |
| **Intent parser** | LLM misclassifies complex user commands | Test against all 6 intent types. Add counter-examples in prompt. |
| **Lightning payments** | Payment verification fails, users don't understand Lightning | Provide clear instructions. Have fallback payment methods ready. |

---

## Known Tech Debt

| Item | Why It's Debt | Plan To Fix |
|------|--------------|-------------|
| OTG-based web dashboard login | Fragile. OTP can expire, get lost. | Add persistent session/token auth as alternative |
| Gemini character consistency not always reliable | Requires prompt gymnastics. No real fine-tuning. | Evaluate newer models as they release. Consider LoRA fine-tuning option. |
| Kling callback webhook requires public URL | Must use ngrok/Cloudflare tunnel for local dev | Document clearly in RUNBOOK. Consider polling as fallback. |
| No test suite | Zero tests for services, tasks, models, views | Add Django TestCase tests for core flows |

---

## The "One Pager" (TL;DR for Onboarding)

- This product lets users create and control **consistent AI characters** via Telegram.
- We chose **Django + Gemini 3.1 Flash + Kling** because it shares the Moral Stories stack and has the best character consistency features.
- Code flows: **Telegram webhook → LLM intent parser → Celery task → Gemini/Kling API → result sent to Telegram or web dashboard**.
- NEVER: hardcode secrets, edit server directly, leak tenant data, skip key validation on BYOK.
- ALWAYS: follow existing patterns, filter by account FK, test before push, create migrations locally.
- The most dangerous thing you can do: expose one tenant's images to another tenant.
