# ZanChop — AI Agent Quick Reference

> **This is the root quick-reference file for AI assistants working on ZanChop.**
> Read this file at the start of every session. Full documentation is in `.agent/docs/`.

---

## 🎯 What This Project Is

**ZanChop** (also called ZanGo internally) is a **WhatsApp-native campus food ordering platform** for **University of Cape Coast (UCC), Ghana**. There is no app, no website for end users — everything happens inside **WhatsApp** via the Meta WhatsApp Cloud API.

- **Buyers (students):** Browse vendors, order food, pay via Paystack, track delivery
- **Vendors:** Manage menus, receive orders, update status, earn through the platform
- **Backend:** Python/Flask on Railway — pure state machine bot (no LLM)

---

## 🚨 Non-Negotiable Rules

1. **Flask only — not FastAPI.** Do not suggest migrating.
2. **No LLM in the bot.** Pure state machine. Speed > intelligence.
3. **Always fetch live API docs** before writing Meta/Paystack/Railway integration code.
4. **All secrets via `os.getenv()`.** Never hardcode. Never commit `.env` files.
5. **Test in terminal before handing off.** Syntax check → import check → manual webhook test.
6. **Guide external steps.** When the user must do something in a dashboard, write out exact steps.
7. **Production code only.** No pseudocode, no `print()`, no dead code.

---

## 📚 Full Documentation Index

All detailed docs live in `.agent/docs/`:

| Doc | Purpose |
|-----|---------|
| [ZanChop.agent.md](.agent/docs/ZanChop.agent.md) | Master reference (extended version of this file) |
| [ZanChop-Architecture.md](.agent/docs/ZanChop-Architecture.md) | System design, infrastructure, state machine |
| [ZanChop-Bot-Flow.md](.agent/docs/ZanChop-Bot-Flow.md) | All states, messages, notification templates |
| [ZanChop-Database-Schema.md](.agent/docs/ZanChop-Database-Schema.md) | All tables, columns, indexes, migration checklist |
| [ZanChop-API-Integrations.md](.agent/docs/ZanChop-API-Integrations.md) | Meta, Paystack, Africa's Talking, Railway setup |
| [ZanChop-Coding-Standards.md](.agent/docs/ZanChop-Coding-Standards.md) | Python/Flask conventions, error handling, testing |
| [ZanChop-Dev-Plan.md](.agent/docs/ZanChop-Dev-Plan.md) | Phases, current priorities, next actions |
| [ZanChop-Mistakes-Log.md](.agent/docs/ZanChop-Mistakes-Log.md) | Known bugs, lessons learned |
| [ZanChop-External-Setup-Guide.md](.agent/docs/ZanChop-External-Setup-Guide.md) | Step-by-step external platform setup |

**Original project docs (keep for reference, do not delete):**
- `ZanGo_about.md` — Project overview and full context
- `ZanGo_bot_flow.md` — Detailed WhatsApp Flow design and conversation mockups

---

## 🔴 Current Launch Blockers (Phase 0)

| Blocker | Issue | Fix |
|---------|-------|-----|
| PostgreSQL migration | SQLite is ephemeral on Railway | See Dev-Plan P0.1 |
| Session persistence | sessions.json gets wiped on redeploy | See Dev-Plan P0.2 |
| Cloud image storage | Product images wiped on redeploy | See Dev-Plan P0.3 |

---

## ⚡ Tech Stack at a Glance

```
Bot:      Meta WhatsApp Cloud API (Graph API v18+)
Backend:  Python 3 / Flask / Gunicorn
DB:       PostgreSQL (target) — currently SQLite (ephemeral)
Payments: Paystack (GHS — Ghana Cedis)
Hosting:  Railway (https://zango.up.railway.app)
Sessions: PostgreSQL sessions table (target) — currently sessions.json
Storage:  Cloudinary (target) — currently static/uploads/
Voice:    Africa's Talking (future — Phase 2)
```

---

## ✅ Quick Checklist

Before any task:
1. Check [ZanChop-Mistakes-Log.md](.agent/docs/ZanChop-Mistakes-Log.md)
2. Check [ZanChop-Dev-Plan.md](.agent/docs/ZanChop-Dev-Plan.md) for current phase

After any code change:
```bash
python -m py_compile app.py && echo "✅ No syntax errors"
python -c "import app; print('✅ Imports OK')"
```
