# deploy_rules.md — How Code Reaches Production (Influencer Studio)

> **Single source of truth for deployments.** Shares server with Moral Stories Studio. See `../deploy_rules.md` for the main app's deploy rules.

---

## Environments

| Environment | Branch | URL | Auto-Deploy? | Who Can Deploy? |
|-------------|--------|-----|-------------|-----------------|
| Production | `main` | (shared server, no separate domain) | Yes (push triggers) | Solo dev |

Shares server `147.93.28.172` with Moral Stories Studio. Influencer Studio runs on its own Gunicorn port and systemd services.

---

## Repositories

| Repo | Type | Local Path | Git Remote |
|------|------|-----------|------------|
| influencer_studio | Backend (Django 4.2) | `./influencer_studio/` | (nested git repo under `youtube_automation/`) |

---

## Deployment Process

Push to `main` triggers `influencer_studio/.github/workflows/deploy.yml`:

1. **GitHub Actions runner checks out code**
2. **SSH key loaded** from `${{ secrets.HOSTINGER_SSH_KEY }}`
3. **rsync files** to `/var/www/html/influencer_studio/` (excludes `.git/`, `venv/`, `db.sqlite3`, `.env`, `media/`)
4. **SSH into server** and run deploy script:
   ```bash
   cd /var/www/html/influencer_studio
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python manage.py makemigrations studio
   python manage.py migrate
   python manage.py collectstatic --noinput
   systemctl restart influencer-studio.service
   systemctl restart influencer-studio-celery.service
   ```

### Migration Files Rule

**Create migration files locally BEFORE pushing/deploying:**

```bash
python manage.py makemigrations studio
git add studio/migrations/XXXX_*.py
git commit -m "migration: description of change"
git push origin main
```

CI/CD runs `python manage.py migrate` which applies pending migrations. The deploy script also runs `makemigrations studio` as a safety net, but local migration creation is the canonical workflow.

### Systemd Services on Server

| Service | Restart Command | Purpose |
|---------|----------------|---------|
| `influencer-studio.service` | `systemctl restart influencer-studio.service` | Gunicorn web server |
| `influencer-studio-celery.service` | `systemctl restart influencer-studio-celery.service` | Celery worker |

---

## Pipeline Triggers

| Trigger | What Happens |
|---------|-------------|
| Push to `main` | Auto-deploy via GitHub Actions |

---

## Forbidden Actions

- Never make direct changes to the server. No SCP, no SSH edits. All deploys via GitHub Actions.
- Never commit `.env`, API keys, bot tokens, or credentials. All secrets in server `.env`.
- Never deploy without running migrations. Always create migration files locally.
- Never force push to `main`.
- Never edit `db.sqlite3` directly. Use migrations or Django shell.
- Never leak tenant data between accounts. Always verify `account=` FK filtering.

---

## Rollback Procedure

1. **Identify bad commit:** `git log --oneline -5` (inside `influencer_studio/`)
2. **Revert:** `git revert <bad-commit-hash>`
3. **Push:** `git push origin main`
4. **Auto-deploy triggers** with reverted code
5. **Monitor:** Check service status after deploy

---

## Post-Deploy Checklist

- Services running: `systemctl status influencer-studio influencer-studio-celery`
- No errors: `journalctl -u influencer-studio --since "5 min ago" | grep -i error`
- Telegram bot responds: Send test message
- Celery worker picking up tasks: `systemctl status influencer-studio-celery`
