# Zan Chop — Full Project Handoff Document
> For use by Antigravity (or any AI assistant) as the primary reference for understanding, continuing, and advising on this project. This document covers everything except the bot conversation flow, which is provided separately.

---

## 1. What We Are Building

**Zan Chop** (also referred to internally as **ZanGo**) is a **WhatsApp-native campus food ordering platform** targeting university students at the **University of Cape Coast (UCC)** in Ghana.

There is no mobile app. There is no website for end users. Everything — browsing restaurants, customising orders, paying, tracking delivery, and managing a vendor store — happens entirely inside **WhatsApp**, through a bot powered by the **Meta WhatsApp Cloud API**.

### The Core Problem Being Solved
Campus students have no reliable, centralised way to order food from campus vendors. Vendors have no system to manage orders, track earnings, or communicate delivery status. Zan Chop closes both gaps through a single WhatsApp number.

### The Two User Types

**Buyers (Students)**
- Message the Zan Chop WhatsApp number
- Get onboarded with name and campus delivery zone
- Browse vendors, view menus, customise orders (add-ons, special instructions)
- Select delivery zone and landmark or choose pickup
- Pay via Paystack link
- Payment is held in escrow and released after delivery confirmation via OTP
- Track order status through the lifecycle

**Vendors (Sellers)**
- Onboard via WhatsApp
- Must be **manually approved** by the Zan Chop admin before getting access
- Manage their menu (add, edit, delete products with images)
- Set delivery zones and pricing per zone
- Manage incoming orders and update order status
- Earnings accumulate in a platform wallet (withdrawal flow is architectured for but NOT built at MVP)

### MVP Scope
- Launching with **3–5 vendors maximum**
- All MVP vendors already have their own delivery riders — no third-party rider logistics needed yet
- Target launch: **within 1 week from project start**
- Real users, real WhatsApp number, real Paystack payments — no sandbox shortcuts

---

## 2. Current Build Status

### What Has Been Completed
- Full Flask-based Python backend (`main.py`) built by the co-developer
- WhatsApp Cloud API webhook receiver (`/webhook` GET + POST)
- Full buyer onboarding state machine
- Vendor onboarding with seller request flow (manual admin approval)
- Admin panel with seller registration form, approval, and stats
- Product management for vendors (add, edit, delete, image upload)
- Order management for vendors (accept, preparing, on the way, cancel)
- Buyer browse, search, cart, checkout, and order tracking flows
- Paystack payment initialization and callback handler (`/payment/callback`)
- Paystack webhook listener (`/payment/webhook`)
- Delivery zones mapped to UCC/Cape Coast campus subareas with landmark suggestions
- OTP-based delivery confirmation
- Session management using a flat JSON file (`sessions.json`)
- SQLite database (`prim_store.db`) with full schema
- Railway deployment live at `https://zango.up.railway.app`
- Meta webhook verified and connected
- Landing page at root (`/`) showing live marketplace stats

### What Is NOT Yet Built (Pending)
- PostgreSQL migration (critical — see Section 6)
- Vendor wallet withdrawal flow (architectured, not implemented)
- Automated call fallback for unresponsive vendors (designed, not implemented)
- WhatsApp message templates for order notifications (not yet submitted to Meta)
- Business verification with Meta (opted to launch unverified at MVP)

---

## 3. Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Bot/messaging | Meta WhatsApp Cloud API | Direct, no intermediary, production-grade |
| Backend language | Python | Co-developer's primary language |
| Web framework | Flask | Already in use by co-developer |
| Server | Gunicorn | WSGI server for Flask on Railway |
| Database (current) | SQLite | Temporary — must migrate before launch |
| Database (target) | PostgreSQL | Railway-hosted, persistent, scalable |
| Session/state | JSON flat file (`sessions.json`) | Temporary — should move to Redis or PostgreSQL |
| Payments | Paystack | Ghana-market payment processor, escrow logic |
| Hosting | Railway | Fast deployment, GitHub-connected, free tier viable at MVP |
| Local dev tunneling | ngrok | Dev only, replaced by Railway URL in production |
| LLM/AI | None | Explicitly ruled out at MVP — adds latency, cost, complexity without clear value |
| Automation tools | None (n8n etc. ruled out) | Python backend handles all automation natively |

### Critical Stack Note: Flask, Not FastAPI
The original plan specified FastAPI. The co-developer built in Flask. The decision was made to keep Flask rather than migrate, because:
- The code is already working
- Flask is fully capable for this use case
- Migration would cost time the 1-week timeline cannot afford
- FastAPI's async performance advantage is not needed at MVP scale

Do not suggest migrating to FastAPI. Flask is the stack going forward.

---

## 4. Architecture Overview

### High-Level Flow

```
WhatsApp User
     │
     ▼
Meta WhatsApp Cloud API
     │  (webhook POST to /webhook)
     ▼
Flask App on Railway (main.py)
     │
     ├── Session lookup (sessions.json / future: PostgreSQL)
     ├── User lookup (SQLite / future: PostgreSQL)
     ├── State machine routing
     │     ├── handle_onboarding()
     │     ├── handle_buyer_flow()
     │     ├── handle_seller_flow()
     │     └── handle_admin_flow()
     │
     ├── whatsapp_cloud_helper.py  ← sends messages back via Graph API
     │
     └── Paystack API (payment init + verify)
```

### Webhook Architecture
- **GET /webhook** — Meta verification handshake. Reads `hub.mode`, `hub.verify_token`, `hub.challenge` query params. Returns challenge if token matches.
- **POST /webhook** — Receives all incoming messages. Parses message type (text, interactive button/list reply, image, audio). Routes to `process_message()`.
- **POST /payment/webhook** — Paystack webhook for `charge.success` events
- **GET /payment/callback** — Paystack redirect after payment, renders HTML confirmation page

### Session State Machine
Every user's conversation state is stored in `sessions.json` as a dictionary keyed by normalized phone number. Each session has:
```json
{
  "state": "buyer_menu",
  "data": { ... },
  "cart": [ ... ]
}
```
The `state` string determines which handler branch processes the next message. All state transitions are explicit — there is no ambiguity or LLM interpretation.

### Message Sending
All outbound messages go through `whatsapp_cloud_helper.py`, which wraps the Meta Graph API. Key message types used:
- `send_whatsapp_message()` — plain text
- `send_interactive_list()` — list picker (up to 10 rows per section)
- `send_interactive_buttons()` — reply buttons (max 3)
- `send_whatsapp_image()` — image with caption

### Phone Number Normalisation
All phone numbers are stored and compared without the `+` prefix. The `normalize_phone()` function strips the `+`. This is applied consistently on storage and lookup to avoid duplicate user records.

---

## 5. Meta WhatsApp Cloud API — Setup Status

### Account Structure
- **Meta Developer Account**: Created and owned by Elikem (the product owner)
- **App type**: Business app (created via Other → Business during app creation)
- **WhatsApp Business Account (WABA)**: Created and linked to the app
- **Business verification**: NOT completed. Operating as unverified account at MVP.

### Unverified Account Limitations
- Maximum **250 business-initiated conversations per 24-hour rolling period**
- This limit applies only to messages the platform sends first (e.g. order notifications via templates)
- User-initiated conversations (student messages the bot first) are **unlimited** and free within the 24-hour service window
- For MVP with 3–5 vendors and a small student cohort, 250 is workable
- Verification should be pursued post-launch via Meta Business Manager → Business Settings → Security Center

### Credentials (Stored in Railway Environment Variables)
```
WHATSAPP_ACCESS_TOKEN        # Permanent system user token (not the temp dashboard token)
WHATSAPP_PHONE_NUMBER_ID     # From App Dashboard → WhatsApp → API Setup
WHATSAPP_WABA_ID             # WhatsApp Business Account ID
WHATSAPP_WEBHOOK_VERIFY_TOKEN  # Custom string used for webhook verification
VERIFY_TOKEN                 # Same value as above — legacy env var name used in current code
```

> **Important**: The current code reads `os.getenv("VERIFY_TOKEN")` not `WHATSAPP_WEBHOOK_VERIFY_TOKEN`. Both are set in Railway for compatibility. When refactoring, standardise to one name.

### Access Token
The token used is a **permanent System User token**, not the temporary token from the dashboard (which expires in under 24 hours). It was generated via:
Meta Business Manager → Business Settings → Users → System Users → Generate Token
Permissions granted: `whatsapp_business_messaging`, `whatsapp_business_management` only.

### Webhook Configuration
- **Webhook URL**: `https://zango.up.railway.app/webhook`
- **Verify Token**: value of `VERIFY_TOKEN` env var
- **Subscribed fields**: `messages`, `message_template_status_update`
- Status: **Verified and active**

### WhatsApp UI Constraints
The bot uses only these interactive message types, which work on unverified accounts:
- **List Messages** — for menus with many options (up to 10 rows per section)
- **Reply Buttons** — for simple choices (max 3 buttons)
- **Text messages** — fallback when interactive messages fail

**WhatsApp Flows** (richer form-like UI) requires a verified Meta Business Account. This is a post-launch upgrade path, not an MVP feature.

### Conversation Pricing
Meta charges per **conversation session**, not per message. A session opens when the first message is sent and lasts 24 hours. Within that window, unlimited messages are free. Key categories:
- **Service conversations** (user-initiated): cheapest category
- **Utility conversations** (business-initiated order updates via templates): slightly more expensive
- **Marketing conversations**: most expensive — NOT used by Zan Chop

Always consult live pricing at: `https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing/conversation-based-pricing/`

---

## 6. Database — Critical Migration Required

### Current State (Broken for Production)
The app currently uses **SQLite** stored as `prim_store.db` on Railway's filesystem. This is a launch blocker because:
- Railway's filesystem is **ephemeral** — every redeploy wipes it
- Every code push destroys all data: users, vendors, orders, sessions, everything
- SQLite does not support concurrent connections safely under load

### Target State: PostgreSQL on Railway
Railway offers a hosted PostgreSQL service that can be attached to the project in minutes. This gives:
- Persistent data that survives deploys
- Proper concurrent connection handling
- Easy backup and restore

### Migration Steps (Must Be Done Before Any Real Users)
1. In Railway dashboard → New Service → Database → PostgreSQL
2. Railway auto-injects `DATABASE_URL` environment variable into the app
3. Add `psycopg2-binary` to `requirements.txt`
4. Replace all `sqlite3.connect(DB_FILE)` calls with a PostgreSQL connection using `DATABASE_URL`
5. Replace SQLite-specific syntax (e.g. `AUTOINCREMENT` → `SERIAL`, `PRAGMA table_info` → `information_schema.columns`)
6. Run `init_db()` once against PostgreSQL to create the schema

### Session Storage
Currently sessions are stored in `sessions.json` — a flat file on the same ephemeral filesystem. This also gets wiped on every deploy. Sessions should be moved to:
- A `sessions` table in PostgreSQL (simplest), OR
- Redis (Railway also offers this) for faster read/write

This is a secondary priority after the PostgreSQL migration but must be done before stable user-facing operation.

---

## 7. Payments — Paystack Integration

### Configuration
```
PAYSTACK_SECRET_KEY       # From Paystack dashboard
PAYSTACK_CALLBACK_URL     # https://zango.up.railway.app/payment/callback
```

### Payment Flow
1. Buyer confirms order → `initiate_paystack_payment()` called
2. Paystack returns an `authorization_url`
3. Bot sends the URL to the buyer as a plain text link in WhatsApp
4. Buyer taps link, completes payment in browser
5. Paystack redirects to `/payment/callback?reference=...`
6. Server verifies payment via `verify_paystack_payment(reference)`
7. If verified: order status updated to `paid`, OTP generated, buyer notified, vendor notified
8. Paystack also sends a webhook to `/payment/webhook` for `charge.success` as backup

### Escrow Logic
Payment is captured by Paystack at checkout. The vendor does NOT receive funds immediately. The platform holds the balance (escrow) until delivery is confirmed. Vendor wallet accumulation and withdrawal are architectured but not implemented at MVP.

### Ghana-Specific Note
Paystack supports Ghana Cedis (GHS). All amounts in the database are stored in GHS. Paystack API expects amounts in **pesewas** (kobo equivalent) — so multiply by 100 when calling the API. This is already handled in `initiate_paystack_payment()`.

---

## 8. Delivery Zones

Delivery zones are hardcoded in `main.py` as `DELIVERY_ZONES` — a dictionary mapping zone names to metadata including a base fee and a list of landmark suggestions.

### Current Zones (Cape Coast / UCC)
1. UCC Science / Main Campus
2. UCC North / Ayensu / Casford
3. UCC South / Oguaa / Adehye
4. Amamoma / Apewosika
5. OLA / Bakano / Town Centre
6. Pedu / CCTU / Abura
7. Kwaprow / Duakor / Ntsin

Each zone has a list of specific landmarks (e.g. "Sam Jonah Library", "Ayensu", "Kotokuraba") that buyers can select as their delivery drop-off point.

### Delivery Fee Logic
Currently all delivery fees are set to `0.0` (free for MVP). The `calculate_delivery_fee()` function exists as a stub and always returns 0. When vendor-set zone pricing is implemented, this function will calculate fees based on seller zone vs buyer zone distance/rank.

### Vendor-Set Pricing (Future)
Vendors who operate their own delivery riders will eventually be able to set custom fees per zone. This is architectured in the data model (the `DELIVERY_ZONES` structure has a `rank` field for distance-based pricing) but not yet exposed in the vendor UI.

---

## 9. Order Lifecycle

Orders move through these states:

```
awaiting_payment → paid → accepted → preparing → on_the_way → delivered
                                                             ↘ cancelled (from any active state)
```

| State | Trigger | Who Acts |
|---|---|---|
| `awaiting_payment` | Order placed, payment link sent | System |
| `paid` | Paystack confirms payment | System (webhook/callback) |
| `accepted` | Vendor taps Accept in dashboard | Vendor |
| `preparing` | Vendor taps Preparing | Vendor |
| `on_the_way` | Vendor taps On The Way | Vendor |
| `delivered` | Buyer enters OTP to confirm handoff | Buyer |
| `cancelled` | Vendor or system cancels | Vendor |

OTP is generated at payment confirmation and stored in `confirmation_code` on the order record. It is shared with the buyer and must be entered by the buyer when the order arrives.

---

## 10. Automated Call Fallback (Designed, Not Built)

One key platform feature is an automated voice call to the vendor if they do not acknowledge an incoming order within approximately **30 seconds**.

### Design Decision
- The team agreed on a ~30 second timeout window before triggering the call
- The call must be triggered by the platform system, not initiated manually
- This requires a voice API — **Africa's Talking** is the recommended provider for Ghana (Twilio Voice is an alternative but more expensive)

### Implementation Notes for When This Is Built
- A background job or delayed task must watch for orders stuck in `paid` state with no `accepted` update after 30 seconds
- On Railway, this can be done with APScheduler (Python) or a separate Railway worker service
- The voice call should say something like: "You have a new order on Zan Chop. Please open WhatsApp and accept it now."
- Before implementing: fetch current Africa's Talking Voice API docs at `https://developers.africastalking.com/docs/voice`
- Meta's own calling API exists but requires user call permissions (gated feature) — Africa's Talking is simpler for outbound calls to vendors

---

## 11. Vendor Wallet (Architectured, Not Built)

Vendor earnings accumulate on the platform. The wallet system is designed as follows:

- Every paid and delivered order credits the vendor's wallet balance
- The platform holds funds (escrow) until delivery confirmed
- Vendor can see their balance in the seller dashboard
- Withdrawal triggers an OTP to the vendor's phone before processing
- Actual payout mechanism (mobile money, bank transfer) TBD

**This is NOT built at MVP.** The database schema supports it via order records and a future `wallets` table. Do not build this until the core order flow is stable and verified.

---

## 12. Environment Variables — Full Reference

All of these must be set in Railway's Variables tab. Never committed to GitHub.

```
# WhatsApp / Meta
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_WABA_ID=
WHATSAPP_WEBHOOK_VERIFY_TOKEN=
VERIFY_TOKEN=                    # Same value as above — legacy name in current code

# Paystack
PAYSTACK_SECRET_KEY=
PAYSTACK_CALLBACK_URL=           # https://zango.up.railway.app/payment/callback

# Platform config
ADMIN_PHONE=                     # WhatsApp number of the Zan Chop admin (no + prefix)
ADMIN_ACCESS_CODE=               # Secret code admin uses to authenticate in the bot
PUBLIC_URL=                      # https://zango.up.railway.app

# Database (after PostgreSQL migration)
DATABASE_URL=                    # Auto-injected by Railway when PostgreSQL service is added

# Optional
MOMO_RECEIVER_NUMBER=            # Mobile money number shown in help/support messages
```

---

## 13. Codebase Structure

```
/
├── main.py                  # Entire application — Flask app, all routes, all flow handlers
├── whatsapp_cloud_helper.py # WhatsApp API wrapper — all outbound message functions
├── requirements.txt         # Python dependencies
├── Procfile                 # Railway start command: web: gunicorn main:app --bind 0.0.0.0:$PORT
├── prim_store.db            # SQLite database (EPHEMERAL — must migrate to PostgreSQL)
├── sessions.json            # Session state store (EPHEMERAL — must migrate)
└── static/
    ├── images/
    └── uploads/             # Uploaded product/shop images (EPHEMERAL — must migrate to cloud storage)
```

### Critical Observation: Static File Storage
Product and shop images uploaded by vendors are saved to `static/uploads/` on Railway's filesystem. Like the database, this is wiped on every redeploy. For production, uploaded images must be stored in cloud object storage (e.g. Cloudinary, AWS S3, or similar). This is a post-MVP concern but must be addressed before vendor onboarding at scale.

---

## 14. Key Architectural Decisions & Rationale

| Decision | What Was Chosen | Why |
|---|---|---|
| No LLM in the bot | Pure state machine | Latency, cost, and structured menu data make NLP unnecessary |
| No n8n | Python handles automation | Avoids extra maintenance layer and latency |
| Flask over FastAPI | Flask | Co-developer's existing code, no time to migrate |
| Gunicorn over uvicorn | Gunicorn | Flask is WSGI, not ASGI — uvicorn caused crashes |
| No WhatsApp Flows at MVP | List/button UI only | Flows require verified Meta Business Account |
| Tap-only UX | Interactive messages only | No free-text input except for names, addresses, search queries |
| Manual vendor approval | Admin reviews all sellers | Ensures quality control at launch with small cohort |
| Paystack over other processors | Paystack | Best Ghana support, reliable escrow flow |
| Railway over Heroku/Render | Railway | Fast setup, GitHub integration, PostgreSQL available |

---

## 15. Mandatory Rules for This Project

These are non-negotiable constraints that apply to every decision, suggestion, and code change:

1. **MVP launches in 1 week for real users.** No speculative features. Every suggestion must be evaluated against this timeline.

2. **No sandbox shortcuts.** The platform must use a real WhatsApp phone number, real Paystack keys, and real vendor accounts. Nothing that only works in a test environment.

3. **Always fetch live API docs before writing integration code.** Never rely on memory for Meta, Paystack, Africa's Talking, or Railway API specifics. Relevant doc roots:
   - Meta Cloud API: `https://developers.facebook.com/docs/whatsapp/cloud-api/`
   - Paystack: `https://paystack.com/docs/`
   - Africa's Talking: `https://developers.africastalking.com/docs/`
   - Railway: `https://docs.railway.app/`

4. **WhatsApp-first thinking.** Every feature must be expressible through WhatsApp interactive messages. Never suggest UI that requires a browser or app unless absolutely necessary with clear justification.

5. **Build lean, but never into a corner.** MVP is small, but architecture must scale to 50+ vendors and multiple campuses without requiring rewrites.

6. **Production-quality code only.** No pseudocode, no demos, no commented-out dead code left in production files.

---

## 16. Immediate Next Actions (Before Launch)

In priority order:

1. **Migrate database from SQLite to PostgreSQL** — launch blocker
2. **Migrate sessions from JSON file to PostgreSQL or Redis** — launch blocker
3. **Migrate static file uploads to cloud storage** — launch blocker for vendor images
4. **Get a real phone number** registered on the Meta account to replace the test number
5. **Submit Meta business verification** — run in parallel, not a blocker for soft launch
6. **End-to-end test** full buyer flow: onboard → browse → order → pay → vendor accepts → deliver → OTP confirm
7. **Onboard first 3 vendors** manually via admin panel
8. **Create and submit WhatsApp utility templates** for order notifications (paid, accepted, on_the_way status updates)

---

## 17. More info

- Vendor wallet withdrawal flow
- Automated call fallback for unresponsive vendors (Africa's Talking Voice API)
- WhatsApp Flows for richer UI (requires Meta business verification I think)
- Third-party rider logistics
- Multi-campus expansion beyond UCC
- Vendor-set delivery zone pricing
- Analytics dashboard for Zan Chop admin
- Cloud image storage migration (Cloudinary or S3 or preferred choice)

ALL THESE INFO CAN CHANGE DEPENDING ON WE SCALING, OUR FLOW OR ARCHITECURE OR ANY IMPROVEMENTS ADN ALWAYS REMEMBER TO UPDATE THIS FILE WHENVER THERE ARE CHANGES
---

*This document was prepared as a complete project handoff. The bot conversation flow (onboarding scripts, menu navigation, state transitions, and message copy) is provided as a separate document.*