# ZanChop — Master Agent Reference

> **Project:** ZanChop (also known as ZanGo internally)
> **Type:** WhatsApp-native campus food ordering platform
> **Target Market:** University of Cape Coast (UCC), Ghana — students & local food vendors
> **Status:** Prototype complete. Pre-launch. Migrating to production infrastructure.

---

## 🎯 Quick Reference

| Attribute        | Value                                                              |
| ---------------- | ------------------------------------------------------------------ |
| **Language**     | Python 3.x                                                         |
| **Framework**    | Flask                                                              |
| **WSGI Server**  | Gunicorn                                                           |
| **Messaging**    | Meta WhatsApp Cloud API (Graph API v18+)                           |
| **DB (Current)** | SQLite (`prim_store.db`) — EPHEMERAL, must migrate                 |
| **DB (Target)**  | PostgreSQL on Railway                                              |
| **Sessions**     | `sessions.json` flat file — EPHEMERAL, must migrate to PostgreSQL  |
| **Payments**     | Paystack (Ghana GHS)                                               |
| **File Storage** | Local `static/uploads/` — EPHEMERAL, must migrate to cloud        |
| **Hosting**      | Railway (`https://zango.up.railway.app`)                           |
| **Bot UX**       | WhatsApp Flows (multi-screen overlays) + Interactive Messages      |

---

## 🚨 Critical Rules — Non-Negotiable

1. **Flask, not FastAPI.** The co-developer wrote the prototype in Flask. Never suggest migrating.
2. **No LLM in the bot at MVP.** Pure state machine. LLM adds latency, cost, and unpredictability.
3. **Always fetch live API docs.** Never rely on memory for Meta, Paystack, Africa's Talking, or Railway API specifics.
4. **No sandbox shortcuts.** Real WhatsApp number, real Paystack keys, real vendors.
5. **WhatsApp-first thinking.** Every feature must be expressible through WhatsApp interactive messages.
6. **Write production-quality code only.** No pseudocode, no commented-out dead code, no debug prints in production.
7. **Test in terminal before handing off.** Run the test scripts, verify DB integrity, verify webhook responses locally before telling the user anything is done.
8. **Guide external steps explicitly.** Whenever an action requires the user to go to an external dashboard (Meta, Paystack, Railway, Africa's Talking), write out the exact step-by-step instructions and include the relevant documentation URL.

---

## 📚 Documentation Index

Read these before any task:

| Document                         | When to Read                                       |
| -------------------------------- | -------------------------------------------------- |
| [ZanChop.agent.md](ZanChop.agent.md) | **Every session** — this file                  |
| [ZanChop-Architecture.md](ZanChop-Architecture.md) | Any backend or data work               |
| [ZanChop-Bot-Flow.md](ZanChop-Bot-Flow.md) | Any WhatsApp message or Flow changes           |
| [ZanChop-Database-Schema.md](ZanChop-Database-Schema.md) | Any data model or query changes      |
| [ZanChop-API-Integrations.md](ZanChop-API-Integrations.md) | Any Meta, Paystack, Africa's Talking work |
| [ZanChop-Coding-Standards.md](ZanChop-Coding-Standards.md) | Every code change                     |
| [ZanChop-Dev-Plan.md](ZanChop-Dev-Plan.md) | Understand phases and what's next                  |
| [ZanChop-Mistakes-Log.md](ZanChop-Mistakes-Log.md) | Before every task — avoid known issues     |
| [ZanChop-External-Setup-Guide.md](ZanChop-External-Setup-Guide.md) | Setting up any external service  |

---

## 📂 Project Structure

```
ZanGo/
├── app.py                      # Main Flask app — all routes + state machine handlers
├── whatsapp_cloud_helper.py    # WhatsApp Graph API wrapper (all outbound messages)
├── twilio_helper.py            # Legacy Twilio helper (may be deprecated)
├── cli.py                      # CLI utilities for testing / seeding
├── migrate_db.py               # DB migration script
├── reset_dev_data.py           # Wipe and re-seed dev data
├── requirements.txt            # Python dependencies
├── Procfile                    # Gunicorn start command
├── prim_store.db               # SQLite DB — EPHEMERAL (replace with PostgreSQL)
├── sessions.json               # Session store — EPHEMERAL (replace with PostgreSQL)
├── .env.bymoi                  # Local env vars — NEVER commit
├── static/
│   └── uploads/                # Product images — EPHEMERAL (replace with Cloudinary/S3)
└── .agent/
    └── docs/                   # All agent documentation lives here
```

---

## 🌿 Git Workflow

| Type    | Branch Pattern           | Example                        |
| ------- | ------------------------ | ------------------------------ |
| Feature | `feature/<description>`  | `feature/postgres-migration`   |
| Bug Fix | `bugfix/<description>`   | `bugfix/payment-callback-race` |
| Hotfix  | `hotfix/<description>`   | `hotfix/webhook-verify-token`  |

**Commit format:** `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

---

## ✅ Pre-Task Checklist

Before starting ANY task:
1. Read [ZanChop-Mistakes-Log.md](ZanChop-Mistakes-Log.md)
2. Read the relevant section docs (see index above)
3. Check the [ZanChop-Dev-Plan.md](ZanChop-Dev-Plan.md) for current phase and priority
4. If touching external APIs — fetch live docs first (URLs in [ZanChop-API-Integrations.md](ZanChop-API-Integrations.md))

---

## ✅ Post-Task Checklist

After completing ANY task:
- [ ] `python -m py_compile app.py` — no syntax errors
- [ ] `python cli.py test` (or equivalent) — logic tested in terminal
- [ ] No `print()` in production code — use `app.logger`
- [ ] All env vars accessed via `os.getenv()` — never hardcoded
- [ ] Webhook tested with ngrok or Railway deploy
- [ ] Mistakes logged if any bugs were found
- [ ] External setup steps documented if required
- [ ] User confirmation received before moving to next feature

---

## 🇬🇭 Ghana Context (Always Consider)

| Scenario                    | Why It Matters                                  |
| --------------------------- | ----------------------------------------------- |
| Mobile Money primary        | MTN MoMo first, Vodafone Cash second, card last |
| GHS currency                | All amounts in GHS. Paystack expects kobo × 100 |
| Low-bandwidth devices       | Keep message sizes small, avoid heavy payloads  |
| WhatsApp-first culture      | Users prefer WhatsApp over apps or browser      |
| UCC campus geography        | 7 distinct delivery zones with landmarks        |
| Vendors have own riders     | No third-party logistics at MVP                 |
