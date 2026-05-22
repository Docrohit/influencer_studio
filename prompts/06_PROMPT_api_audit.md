# Prompt 6: API Audit — Generate API_info.md

**Who uses this:** Junior devs (or senior devs onboarding), once per project or after major API changes.

**What it does:** Produces a comprehensive `API_info.md` file that documents every endpoint, its purpose, auth, consumers, LLM usage, background processing, and known gaps. This file becomes auto-loaded by AI tools alongside AGENTS.md.

**Copy-paste into your AI tool:**

```
You are auditing this project's entire API surface. Your job is to create a comprehensive API_info.md file that every developer and AI tool can reference.

---

## PHASE 1: Discover All Endpoints

Scan the ENTIRE codebase for API endpoints. Leave nothing out.

### Backend APIs
- Django: scan urls.py files, views.py, viewsets, APIView classes
- Express: scan route files, router definitions, app.use()
- Next.js: scan pages/api/, app/api/, route handlers
- Laravel: scan routes/api.php, routes/web.php
- Flask/FastAPI: scan @app.route, @router.get/post decorators
- Go: scan mux.HandleFunc, router definitions
- PHP: scan index.php, api.php, router files

### Frontend API Consumers
- React: scan fetch(), axios, useQuery, useMutation, apiClient calls
- Next.js: scan server actions, getServerSideProps, route handlers
- Vue: scan axios, fetch in components/stores
- Django templates: scan {% url %}, fetch/axios in template JS
- Any API client files (e.g., api.js, client.ts, apiService.ts)

### External API Calls
- Scan for calls TO external services (Stripe, Twilio, OpenAI, Gemini, AWS SDK, etc.)

---

## PHASE 2: For EVERY Endpoint, Document These Fields

Create a markdown file with this structure:

```markdown
# API_info.md — Complete API Reference for {PROJECT_NAME}

> Auto-generated. Update when APIs change. Read by AI tools alongside AGENTS.md.

## Base URLs

| Environment | Base URL |
|---|---|
| Dev | {DEV_URL} |
| QA/Staging | {QA_URL} |
| Production | {PROD_URL} |

---

## Authentication

| Method | Details |
|---|---|
| {JWT / Session / API Key / OAuth2 / None} | {Where token is sent (header/cookie), format, expiry} |

---

## Endpoint Catalog

### {CATEGORY — e.g., "User Management"}

| # | Method | Full URL | Auth | Purpose | Frontend Consumer |
|---|---|---|---|---|---|
| 1 | GET | `/api/users/` | JWT | List all users | `src/pages/Users.jsx` → `useQuery('users')` |
| 2 | POST | `/api/users/` | JWT | Create user | `src/components/UserForm.jsx` → `apiClient.post()` |

For EACH endpoint, expand into a detailed card:

### `{METHOD} {FULL_URL}`

- **Purpose:** {1-2 sentences — what does this endpoint actually do?}
- **Request Body:** {JSON schema or form data fields}
- **Response:** {JSON structure, status codes}
- **Auth required:** {Yes/No — what auth}
- **LLM call?** {Yes/No — if yes, which model, what task}
- **Response type:** {Quick (<500ms) / Medium / Long background process}
  - If long: {what Celery/queue task? How to check status?}
- **Calls other APIs?** {Yes/No — list which ones}
- **Frontend consumer:** {Specific component, hook, or page}
  - {File path} → line {N}
- **Direct consumer (no frontend)?** {Webhook / Cron / Script / Third-party}
- **Known gaps/errors:** {Any silent failures, missing error handling, TODO comments, known bugs}
```

---

## PHASE 3: Cross-Cutting Analysis

After documenting ALL endpoints, add these sections:

```markdown
---

## LLM Usage Summary

| Endpoint | LLM Model | Purpose | Sync/Async | Fallback? |
|---|---|---|---|---|
| POST /api/generate/ | Gemini 2.0 | Generate product descriptions | Async (Celery) | Falls back to GPT-4o if Gemini fails |
| GET /api/search/ | OpenAI Ada | Semantic search embeddings | Sync | No fallback |

---

## Background / Long-Running APIs

| Endpoint | Queue/Task | Avg Duration | Status Check Endpoint |
|---|---|---|---|
| POST /api/batch/generate-campaign/ | Celery `process_batch_campaign_orchestrator` | 3-5 min | GET /api/batch/{id}/status/ |
| POST /api/export/report/ | Celery `generate_report_task` | 30-60s | GET /api/export/{id}/status/ |

---

## API Chain Map (Who Calls Whom)

```
POST /api/checkout/
  → calls Stripe API (external)
  → calls POST /api/inventory/reserve/ (internal)
  → triggers Celery task send_confirmation_email
  → email task calls SendGrid API (external)

GET /api/dashboard/
  → calls GET /api/analytics/summary/ (internal)
  → calls GET /api/users/active-count/ (internal)
  → caches result in Redis (5 min TTL)
```

---

## Known Gaps & Silent Errors

| Endpoint | Issue | Severity | Fix Plan |
|---|---|---|---|
| POST /api/upload/ | Doesn't validate file type — accepts anything | Medium | Add mimetype validation |
| GET /api/search/ | Empty query returns 500 instead of 400 | High | Add input validation at controller |
| POST /api/generate-campaign/ | Silent failure if Celery worker is down — returns 200 but nothing happens | Critical | Add worker health check before queuing |

---

## Unused / Dead APIs

| Endpoint | Evidence It's Unused | Action |
|---|---|---|
| GET /api/v1/legacy/reports/ | No frontend references found, v2 exists | Mark deprecated, remove in Q3 |

---

## API Conventions (Enforced)

- **URL pattern:** {kebab-case / camelCase / snake_case}
- **Versioning:** {/api/v1/ or header-based}
- **Pagination:** {cursor-based / offset-limit / page-number}
- **Error format:** `{ "error": "message", "code": "ERROR_CODE" }`
- **Success format:** `{ "data": {...}, "meta": {...} }`
- **Rate limiting:** {Yes/No — limits?}
- **CORS:** {configured for which origins?}
```

---

## PHASE 4: Verify

After writing the file:

1. Count endpoints: "I found {N} unique endpoints across {M} categories."
2. Check for gaps: "I could NOT find a frontend consumer for {K} endpoints."
3. Ask me: "Are these accurate? Did I miss any endpoints?"

Write the file as `API_info.md` in the project root.

This file should exist alongside AGENTS.md and product_theory.md. AI tools will read it automatically.
```
