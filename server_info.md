# server_info.md — Server Reference (Influencer Studio)

> **READ-ONLY reference.** NEVER modify server files directly. Use Git → Deploy pipeline for all changes.
> Shares server with Moral Stories Studio. See `../server_info.md` for the main app's server details.

---

## Server Access

| Detail | Value |
|--------|-------|
| Host / IP | `147.93.28.172` |
| SSH User | `root` |
| SSH Key | `~/.ssh/hostinger.pem` |
| SSH Command | `ssh -i ~/.ssh/hostinger.pem root@147.93.28.172` |

---

## Environments on This Server

| Environment | Code Path | Branch | Services |
|-------------|-----------|--------|----------|
| Production | `/var/www/html/influencer_studio/` | `main` | influencer-studio, influencer-studio-celery |

---

## Services (systemd)

| Service Name | Restart | Check Status | Logs |
|-------------|---------|--------------|------|
| `influencer-studio.service` | `systemctl restart influencer-studio.service` | `systemctl status influencer-studio.service --no-pager` | `journalctl -u influencer-studio -f` |
| `influencer-studio-celery.service` | `systemctl restart influencer-studio-celery.service` | `systemctl status influencer-studio-celery.service --no-pager` | `journalctl -u influencer-studio-celery -f` |

---

## Key Paths

| Item | Path |
|------|------|
| Project root | `/var/www/html/influencer_studio/` |
| Virtual env | `/var/www/html/influencer_studio/venv/` |
| Environment file | `/var/www/html/influencer_studio/.env` |
| Database | `/var/www/html/influencer_studio/db.sqlite3` |
| Media files | `/var/www/html/influencer_studio/media/` |

---

## Database

| Detail | Value |
|--------|-------|
| Type | SQLite |
| File | `/var/www/html/influencer_studio/db.sqlite3` |
| Connect | `python manage.py shell` or `python manage.py dbshell` |

---

## Health Checks

| Check | Command |
|-------|---------|
| Service status | `systemctl status influencer-studio --no-pager` |
| Celery status | `systemctl status influencer-studio-celery --no-pager` |
| Recent errors | `journalctl -u influencer-studio --since "10 min ago" --no-pager` |
| Disk usage | `df -h` |
| Memory usage | `free -m` |

---

## Operational Rules

1. **SSH is READ-ONLY.** View logs, check status. NEVER edit code directly.
2. **All code changes** go through: `git push origin main` → GitHub Actions deploy → restart services.
3. **Never edit `db.sqlite3` directly.** Use migrations or Django shell.
4. **If you find a server issue**, fix it in code, not on the server.
