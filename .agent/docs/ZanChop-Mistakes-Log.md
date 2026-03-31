# ZanChop — Mistakes Log

> **Read this before every session.** If you encounter a bug or make a mistake, log it here immediately.
> Pattern: what went wrong, why, and how to avoid it next time.

---

## Known Issues in Current Prototype

### 🔴 CRITICAL: Ephemeral Storage
**What:** SQLite (`prim_store.db`) and sessions (`sessions.json`) are stored on Railway's temporary filesystem.
**Effect:** Every Railway redeploy wipes all user data, vendor data, orders, and sessions. Users are completely reset.
**Fix:** Migrate to PostgreSQL (sessions table) before any real user traffic.
**Status:** Not fixed — see Phase 0 in [ZanChop-Dev-Plan.md](ZanChop-Dev-Plan.md)

---

### 🔴 CRITICAL: Product Images Are Ephemeral
**What:** Vendor-uploaded product images are saved to `static/uploads/` on Railway's filesystem.
**Effect:** Every redeploy deletes all product photos. Vendor store looks empty after any deploy.
**Fix:** Migrate image uploads to Cloudinary or AWS S3.
**Status:** Not fixed — see Phase 0 in [ZanChop-Dev-Plan.md](ZanChop-Dev-Plan.md)

---

### 🟠 IMPORTANT: Dual Env Var Names for Verify Token
**What:** The webhook verify token is read as `os.getenv("VERIFY_TOKEN")` in code, but the more descriptive name is `WHATSAPP_WEBHOOK_VERIFY_TOKEN`. Both are set in Railway.
**Effect:** Confusion when configuring env vars for new deployments or developer handoffs.
**Fix:** Standardise to one name in a future refactor. Currently — set BOTH in Railway Variables.
**Status:** Both set in Railway, functional but confusing.

---

### 🟠 IMPORTANT: Gunicorn, NOT uvicorn
**What:** Flask is a WSGI app. uvicorn is an ASGI server.
**Effect:** uvicorn crashes the Flask app. Must use Gunicorn.
**Fix:** Procfile: `web: gunicorn app:app --bind 0.0.0.0:$PORT`
**Status:** Correctly set. Do not change.

---

### 🟡 NOTE: SQLite Placeholders vs PostgreSQL
**What:** SQLite uses `?` as query parameter placeholders. PostgreSQL (psycopg2) uses `%s`.
**Effect:** After PostgreSQL migration, queries with `?` will fail silently or throw errors.
**Fix:** Replace every `?` with `%s` in all SQL queries during migration.
**Pattern to search:** `grep -n "?" app.py | grep -v "#"`

---

### 🟡 NOTE: Paystack Amount in Pesewas
**What:** Paystack expects amounts in pesewas (GHS × 100), not GHS.
**Effect:** If you pass `25.00` instead of `2500`, the buyer pays 100× less than intended.
**Fix:** Already handled in `initiate_paystack_payment()` — DO NOT break this multiplication.
**Check before any payment code changes:** The line `amount * 100` must remain.

---

### 🟡 NOTE: WhatsApp Flows Require Verified Business Account
**What:** WhatsApp Flows (multi-screen overlays) are only available to Meta-verified business accounts.
**Effect:** Any code that tries to send a Flow message to an unverified account will fail.
**Fix:** Don't build Flows until Meta business verification is complete. Use list/button messages instead.
**Status:** Known design decision — Phase 3 after verification.

---

### 🟠 IMPORTANT: FastAPI + uvicorn in requirements.txt
**What:** `requirements.txt` contains `fastapi` and `uvicorn[standard]` even though the app uses Flask/Gunicorn.
**Effect:** Unnecessary dependencies bloat the deployment. More critically, uvicorn is an ASGI server — if something accidentally imports or starts it, Flask will crash (Flask is WSGI only).
**Fix:** Remove `fastapi` and `uvicorn[standard]` from `requirements.txt`. Keep `gunicorn` only.
**Status:** Discovered 2026-03-31. Needs cleanup.

---

### 🟡 NOTE: Interactive List Row Limit
**What:** WhatsApp interactive list messages support max 10 rows per section and max 3 sections.
**Effect:** If a vendor has more than 10 products, a single list message can't show all of them.
**Fix:** Paginate the list — add a "Show more..." row that triggers the next page of results.
**Status:** Current prototype may break for vendors with large menus. Must fix before scale.

---

### 🟡 NOTE: Interactive Button Limit
**What:** WhatsApp reply button messages support max 3 buttons.
**Effect:** Seller main menu needs 6 options — can only show 3 per message.
**Fix:** Send two consecutive messages, each with 3 buttons. Already designed this way.
**Status:** Handled in design. Confirm implementation follows this pattern.

---

## Template for New Entries

```
### 🔴/🟠/🟡 SEVERITY: SHORT TITLE
**What:** Brief description of the bug/mistake
**Effect:** What goes wrong for the user or system
**Fix:** How to resolve it
**Status:** Fixed / Not fixed / In progress
**Date discovered:** YYYY-MM-DD
```

Severity guide:
- 🔴 Critical — breaks core functionality or causes data loss
- 🟠 Important — significant UX degradation or security concern
- 🟡 Note — minor issue, edge case, or stylistic concern
