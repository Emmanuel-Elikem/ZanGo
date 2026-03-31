# ZanChop — Coding Standards

> **Read this file before writing any Python/Flask code for ZanChop.**

---

## 1. Python Conventions

### General Rules
- **Python version:** 3.10+
- **No `print()` in production code.** Use `app.logger.info()`, `app.logger.warning()`, `app.logger.error()`
- **All environment variables via `os.getenv()`.** Never hardcode tokens, passwords, or URLs.
- **Type hints on all function signatures** where feasible
- **Docstrings on every function** — at minimum a one-liner

### Naming
| Type       | Convention      | Example                          |
| ---------- | --------------- | -------------------------------- |
| Variables  | `snake_case`    | `order_total`, `buyer_phone`     |
| Functions  | `snake_case`    | `get_user_by_phone()`, `send_order_notification()` |
| Classes    | `PascalCase`    | `PaystackClient`, `SessionManager` |
| Constants  | `UPPER_SNAKE`   | `DELIVERY_ZONES`, `ORDER_STATES` |
| Files      | `snake_case.py` | `session_manager.py`, `paystack_helper.py` |

### Error Handling
```python
# ✅ Always wrap external API calls
try:
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()
except requests.Timeout:
    app.logger.error(f"[Paystack] Timeout on {url}")
    return None
except requests.HTTPError as e:
    app.logger.error(f"[Paystack] HTTP error: {e.response.status_code} — {e.response.text}")
    return None
except Exception as e:
    app.logger.error(f"[Paystack] Unexpected error: {e}")
    return None

# ❌ Never swallow errors silently
try:
    do_something()
except:
    pass
```

### Timeouts on All HTTP Requests
```python
# ✅ Always set timeout
requests.post(url, json=data, timeout=10)

# ❌ Never skip timeout — can hang the webhook handler indefinitely
requests.post(url, json=data)
```

---

## 2. Flask Conventions

### Route Organization
Group routes by concern with clear comments:

```python
# ═══════════════════════════════
# WEBHOOK ROUTES
# ═══════════════════════════════
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    ...

# ═══════════════════════════════
# PAYMENT ROUTES
# ═══════════════════════════════
@app.route('/payment/callback', methods=['GET'])
def payment_callback():
    ...
```

### Webhook Handler Must Return 200 Immediately
Meta expects a `200 OK` within 5 seconds or it retries.
Run heavy processing in a background thread:

```python
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    # Start processing in background — don't block
    threading.Thread(target=process_webhook, args=(data,), daemon=True).start()
    return 'OK', 200
```

### Database Connections
```python
# ✅ Use context manager for DB connections
def get_db():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    return conn

def get_user_by_phone(phone):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE phone = %s", (phone,))
            return cur.fetchone()

# ❌ Never leave connections open
conn = sqlite3.connect(DB_FILE)
user = conn.execute(...)
# forgot to close!
```

### Response Format Consistency
All API responses (not WhatsApp bot responses) should return JSON:
```python
return jsonify({"success": True, "data": result}), 200
return jsonify({"success": False, "error": "User not found"}), 404
```

---

## 3. WhatsApp Message Guidelines

### Interactive Messages Only Where Possible
- Use `send_interactive_buttons()` for 2–3 choices (fastest for users)
- Use `send_interactive_list()` for 4–10 choices (vendors list, menu items)
- Fall back to text only when interactive messages fail or for simple confirmations

### Message Copy Guidelines
- Keep messages short and scannable — users read on mobile
- Use emojis sparingly but purposefully (✅, ❌, 🔔, 🚗, etc.)
- Always include a clear next action (button or instruction)
- Avoid walls of text — break with line breaks

### Phone Number Normalisation
```python
def normalize_phone(phone: str) -> str:
    """Strip '+' prefix for consistent storage and lookup."""
    return phone.lstrip('+')

# ✅ Always normalise before storage or lookup
phone = normalize_phone(incoming_phone)

# ❌ Never store raw numbers with '+'
db.execute("INSERT INTO users (phone) VALUES (%s)", (raw_phone,))
```

---

## 4. Session Management

### Current (Temporary) — sessions.json
The session dict is keyed by normalized phone number:
```python
{
  "233241234567": {
    "state": "buyer_menu",
    "data": {},
    "cart": []
  }
}
```

### Target — PostgreSQL `sessions` table
Same structure but persisted in PostgreSQL `sessions` table (see Database Schema doc).

### Session Read/Write Pattern
```python
def get_session(phone: str) -> dict:
    """Get session for a phone number. Returns default if not found."""
    # Current: read from sessions.json
    # Target: SELECT from sessions WHERE phone = %s
    return sessions.get(phone, {"state": "new_user", "data": {}, "cart": []})

def save_session(phone: str, session: dict) -> None:
    """Persist session for a phone number."""
    # Current: write to sessions.json
    # Target: UPSERT into sessions WHERE phone = %s
    sessions[phone] = session
    save_sessions_file()
```

---

## 5. Security Rules

- **Never log full session data** containing user personal info — log only phone and state
- **Never log full Paystack payload** — it may contain card details
- **Validate Paystack webhook signatures** on every POST to `/payment/webhook`
- **Validate Meta webhook verify_token** on every GET to `/webhook`
- **Admin access code** must be stored in env var, never in code
- **All secrets in Railway Variables** — never in code, never in `.env` files committed to GitHub
- **Add `.env*` to `.gitignore`** — confirm this before every push

---

## 6. Testing Approach

### Terminal Tests (Before Handing Off to User)
```bash
# 1. Syntax check — runs after every significant change
python -m py_compile app.py && echo "✅ No syntax errors"

# 2. Import check — catches missing dependencies
python -c "import app" && echo "✅ Imports OK"

# 3. DB connection test
python -c "
import os
import psycopg2
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
print('✅ DB connected')
conn.close()
"

# 4. Webhook simulation (with local Flask + ngrok)
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{"entry":[{"changes":[{"value":{"messages":[{"from":"233241234567","type":"text","text":{"body":"hi"}}]}}]}]}'
```

### What "Done" Means
A feature is NOT done until:
1. `python -m py_compile app.py` passes 
2. The feature has been manually tested via curl or ngrok
3. Edge cases are handled (no DB record, invalid state, missing env var)
4. User has tested it against the real WhatsApp bot
