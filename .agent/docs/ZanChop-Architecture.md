# ZanChop — System Architecture

> **Read this before any backend, database, deployment, or infrastructure work.**

---

## 1. High-Level System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USERS (WhatsApp)                         │
│           Buyers (Students)          Vendors (Sellers)           │
└────────────────────────────┬────────────────────────────────────┘
                             │ Messages, button taps, Flow responses
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Meta WhatsApp Cloud API                         │
│         (Graph API v18+, Webhook POST to /webhook)               │
└────────────────────────────┬────────────────────────────────────┘
                             │ Webhook events (text, button_reply, nfm_reply)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Flask App — Railway                             │
│                   app.py (main module)                           │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  /webhook    │  │ /payment/    │  │      /admin/*         │  │
│  │ GET: verify  │  │ callback     │  │  (web admin panel)    │  │
│  │ POST: events │  │ /payment/    │  │                       │  │
│  └──────┬───────┘  │ webhook      │  └──────────────────────┘  │
│         │          └──────┬───────┘                             │
│         ▼                 ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               State Machine Router                       │   │
│  │  process_message() → routes to correct handler           │   │
│  │                                                           │   │
│  │  handle_onboarding()   handle_buyer_flow()               │   │
│  │  handle_seller_flow()  handle_admin_flow()               │   │
│  └──────────────────────────────┬────────────────────────┘   │
│                                 │                              │
│  ┌────────────────────┐  ┌─────┴─────────────┐               │
│  │ whatsapp_cloud_    │  │  PostgreSQL DB      │               │
│  │ helper.py          │  │  (Target) /         │               │
│  │ (send messages)    │  │  SQLite (Current)   │               │
│  └─────────┬──────────┘  └───────────────────┘               │
│            │                                                   │
└────────────┼───────────────────────────────────────────────────┘
             │ Graph API calls
             ▼
   Meta WhatsApp Cloud API → Delivered to user's WhatsApp
```

---

## 2. Webhook Architecture

### GET /webhook — Verification Handshake
Meta calls this once when you configure the webhook URL. Reads:
- `hub.mode` → must equal `"subscribe"`
- `hub.verify_token` → must match `VERIFY_TOKEN` env var
- `hub.challenge` → returned verbatim if valid

### POST /webhook — All Incoming Events
Receives all WhatsApp activity. The payload is parsed to extract:
- `message.type` — `text`, `interactive`, `image`, `audio`
- `message.interactive.type` — `button_reply` or `nfm_reply` (Flow response)
- `from` field → normalized phone number (key for session lookup)

### POST /payment/webhook — Paystack Events
Receives `charge.success` events from Paystack as a backup delivery mechanism.
Must verify `x-paystack-signature` header using HMAC-SHA512 with `PAYSTACK_SECRET_KEY`.

### GET /payment/callback — Paystack Redirect
User is redirected here after completing payment in browser.
Verifies payment with Paystack API, updates order, notifies buyer + vendor.

---

## 3. State Machine Design

Every conversation is stateful. The state is stored per phone number:

```python
session = {
  "state": "buyer_menu",        # Current state string
  "data": { ... },              # Contextual scratchpad (e.g., cart items, selected vendor)
  "cart": [ ... ]               # Active cart items
}
```

### State Naming Convention
```
# Onboarding
"new_user"
"buyer_onboarding_name"
"buyer_onboarding_zone"

# Buyer states
"buyer_menu"
"buyer_browsing"
"buyer_cart"
"buyer_checkout"
"buyer_tracking"

# Seller states
"seller_menu"
"seller_products"
"seller_orders"
"seller_settings"

# Admin states
"admin_menu"
"admin_approve_seller"
```

### Key Routing Functions (in app.py)
| Function                | Purpose                                              |
| ----------------------- | ---------------------------------------------------- |
| `process_message()`     | Entry point — dispatches to correct handler          |
| `handle_onboarding()`   | New user registration (buyer or seller)              |
| `handle_buyer_flow()`   | All buyer states: browse, cart, checkout, track      |
| `handle_seller_flow()`  | All seller states: products, orders, wallet, zones   |
| `handle_admin_flow()`   | Admin management: approve sellers, view stats        |

---

## 4. WhatsApp Flows Architecture

> ⚠️ **WhatsApp Flows require a verified Meta Business Account.**
> The prototype uses the traditional chatbot model with list/button messages.
> Flows are the **target UX** for post-MVP when business verification is complete.

### What Are WhatsApp Flows?
Multi-screen interactive forms that open as overlays inside WhatsApp. The user fills fields, taps "Next," and submits — all without flooding the chat.

### Flow → Backend Communication
When a Flow is completed, WhatsApp sends an `nfm_reply` webhook event.
The backend receives a JSON payload containing all screen field values.

### Planned Flows (post-MVP)
| Flow Name             | Screens | Triggered By        | User    |
| --------------------- | ------- | ------------------- | ------- |
| `buyer_registration`  | 2       | "Buy Food" button   | Buyer   |
| `food_ordering`       | 5       | "Order Food" button | Buyer   |
| `order_tracking`      | 2       | "My Orders" button  | Buyer   |
| `seller_registration` | 2       | "Sell Food" button  | Seller  |
| `product_management`  | 2       | "My Products"       | Seller  |
| `status_update`       | 1       | "Update Status"     | Seller  |
| `wallet`              | 1       | "Wallet" button     | Seller  |
| `delivery_zones`      | 2       | "Delivery Zones"    | Seller  |
| `store_profile`       | 1       | "Store Profile"     | Seller  |

### MVP Alternative (Current Implementation)
Traditional chatbot: sequential list/button messages + text inputs.
Each user action sends a message → bot replies → user acts → bot replies...

---

## 5. Infrastructure & Deployment

### Railway (Production Hosting)
- **Project:** ZanGo on Railway dashboard
- **Service:** Web service connected to GitHub repo
- **Start command (Procfile):** `web: gunicorn app:app --bind 0.0.0.0:$PORT`
- **Deploy trigger:** Push to `main` branch auto-deploys
- **Live URL:** `https://zango.up.railway.app`

### Environment Variables (Railway Variables tab)
See full reference in [ZanChop-API-Integrations.md](ZanChop-API-Integrations.md).

### Critical Migration Requirements (Pre-Launch Blockers)

| Item          | Current (Broken)       | Target (Production)           | Priority  |
| ------------- | ---------------------- | ----------------------------- | --------- |
| Database      | SQLite (`prim_store.db`) | PostgreSQL on Railway        | 🔴 P0    |
| Sessions      | `sessions.json` flat file | PostgreSQL `sessions` table | 🔴 P0    |
| File storage  | `static/uploads/` local | Cloudinary or AWS S3         | 🟠 P1    |

**Why SQLite is a launch blocker:**
- Railway filesystem is **ephemeral** — every redeploy wipes everything
- SQLite does not support concurrent connections safely under load
- Every code push kills all user data, vendor data, and orders

---

## 6. Performance Architecture

### Latency Priorities
The bot must feel instant. These design decisions enforce low latency:

1. **No LLM in the critical path.** Pure state machine, zero model inference time.
2. **Session lookup is O(1).** Phone number is the key. Will be indexed in PostgreSQL.
3. **Database queries use specific SELECT fields.** Never `SELECT *` on hot paths.
4. **Paystack payment link is generated async where possible.** Link is sent in the same response, not a follow-up.
5. **Webhook handler returns 200 immediately** before doing heavy processing. Vendor is notified after fast DB writes.

### 30-Second Vendor Timeout
- When an order is paid, a background job starts a 30-second countdown
- If vendor hasn't responded (accepted/rejected), send a timeout alert
- Implementation: APScheduler (Python) or Railway Worker service
- **This must NOT block the webhook response.** Run in a background thread.

---

## 7. Order Lifecycle State Machine

```
awaiting_payment → paid → accepted → preparing → on_the_way → delivered
                                 ↘
                              cancelled (from any active state)
```

| Transition               | Trigger                     | Who Acts         |
| ------------------------ | --------------------------- | ---------------- |
| → `awaiting_payment`     | Order placed                | System           |
| → `paid`                 | Paystack confirms payment   | System (webhook) |
| → `accepted`             | Vendor taps Accept          | Vendor           |
| → `preparing`            | Vendor taps Preparing       | Vendor           |
| → `on_the_way`           | Vendor taps On The Way      | Vendor           |
| → `delivered`            | Buyer enters OTP            | Buyer            |
| → `cancelled`            | Vendor rejects / timeout    | Vendor / System  |

---

## 8. Delivery Zone System

Hardcoded in `app.py` as `DELIVERY_ZONES` dict.
7 zones covering Cape Coast / UCC campus:

| Zone Name                       | Key Landmarks                              |
| --------------------------------- | ------------------------------------------ |
| UCC Science / Main Campus         | Sam Jonah Library, Main Gate, Students Rep |
| UCC North / Ayensu / Casford      | Ayensu, Casford, Scholars                  |
| UCC South / Oguaa / Adehye        | Oguaa Hall, Adehye                         |
| Amamoma / Apewosika               | Amamoma community                          |
| OLA / Bakano / Town Centre        | Kotokuraba market                          |
| Pedu / CCTU / Abura               | CCTU junction, Pedu junction               |
| Kwaprow / Duakor / Ntsin          | Duakor, Ntsin village                      |

**Delivery fees:** All set to `GH₵ 0.00` at MVP (free). `calculate_delivery_fee()` is a stub.
