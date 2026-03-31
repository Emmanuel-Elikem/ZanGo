# ZanChop — API Integrations Reference

> **Always fetch live API docs before writing integration code. Never rely on memory for API specifics.**
> Live doc URLs are listed alongside each integration.

---

## 1. Meta WhatsApp Cloud API

**Live docs root:** https://developers.facebook.com/docs/whatsapp/cloud-api/

### Account Setup
- **Meta Developer Account:** Created and owned by Elikem (product owner)
- **App Type:** Business app (Other → Business during app creation)
- **WhatsApp Business Account (WABA):** Created and linked
- **Business Verification:** NOT completed. MVP operates unverified.

### Unverified Account Limits
| Limit Type                             | Value                          |
| -------------------------------------- | ------------------------------ |
| Business-initiated conversations       | 250 per rolling 24-hour period |
| User-initiated conversations           | Unlimited (within 24h window)  |
| WhatsApp Flows availability            | ❌ Requires verified account  |
| WhatsApp message templates (utility)  | ✅ Can submit, limited volume  |

### Environment Variables
```
WHATSAPP_ACCESS_TOKEN          # Permanent System User token (NOT dashboard temp token)
WHATSAPP_PHONE_NUMBER_ID       # From App Dashboard → WhatsApp → API Setup
WHATSAPP_WABA_ID               # WhatsApp Business Account ID
VERIFY_TOKEN                   # Custom string for webhook verification
WHATSAPP_WEBHOOK_VERIFY_TOKEN  # Same value as VERIFY_TOKEN (legacy + new name, both set)
```

> ⚠️ The current code reads `os.getenv("VERIFY_TOKEN")`. Both env vars are set in Railway for compatibility.
> When refactoring, standardise to `WHATSAPP_WEBHOOK_VERIFY_TOKEN` only.

### Generating a Permanent System User Token
1. Go to **Meta Business Manager** → business.facebook.com
2. Navigate to **Business Settings** → **Users** → **System Users**
3. Create a System User (or use existing)
4. Click **Generate Token**
5. Select the app and grant permissions:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
6. Copy the token and save to Railway Variables as `WHATSAPP_ACCESS_TOKEN`
7. ⚠️ This token does NOT expire — keep it secret, never commit to GitHub

### Webhook Configuration Steps
1. Go to **Meta Developer Dashboard** → Your App → **WhatsApp** → **Configuration**
2. Set **Webhook URL** to: `https://zango.up.railway.app/webhook`
3. Set **Verify Token** to: value of `VERIFY_TOKEN` env var
4. Click **Verify and Save**
5. Subscribe to fields: `messages`, `message_template_status_update`
6. Status should show: ✅ Verified

### Message Types Used
| Method                    | API Call                              | Max Items   |
| ------------------------- | ------------------------------------- | ----------- |
| `send_whatsapp_message()` | POST /messages (type: text)           | N/A         |
| `send_interactive_list()` | POST /messages (type: interactive list) | 10 rows/section |
| `send_interactive_buttons()` | POST /messages (type: interactive buttons) | 3 buttons |
| `send_whatsapp_image()`   | POST /messages (type: image + caption) | 1 image    |

### Conversation Pricing (Meta)
Pricing: https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing/conversation-based-pricing/
- **Service conversations** (user-initiated): cheapest
- **Utility conversations** (business-initiated via templates): slightly more
- **Marketing**: NOT used by ZanChop

### Message Templates
For proactive notifications (order status updates), pre-approved templates are required.

**Template submission process:**
1. Meta Developer Dashboard → WhatsApp → **Message Templates**
2. Click **Create Template**
3. Choose **Category:** Utility (for order updates)
4. Write template with variables: e.g. `Your order {{1}} is now {{2}}. Track here: {{3}}`
5. Submit for review — usually approved within minutes to hours
6. Reference by template name in API calls

**Templates needed at launch:**
- `order_paid_notification` — sent to buyer when payment confirmed
- `order_accepted_notification` — sent to buyer when vendor accepts
- `order_on_the_way_notification` — sent to buyer when food is on the way
- `order_delivered_notification` — sent to buyer when delivered
- `order_cancelled_notification` — sent to buyer when order is cancelled
- `new_order_vendor_notification` — sent to vendor for new orders (if unverified account allows)

---

## 2. Paystack

**Live docs:** https://paystack.com/docs/

### Account Type
Standard Paystack account registered for Ghana (GHS).

### Environment Variables
```
PAYSTACK_SECRET_KEY       # From Paystack Dashboard → Settings → API Keys & Webhooks
PAYSTACK_CALLBACK_URL     # https://zango.up.railway.app/payment/callback
```

### Payment Flow (current implementation)
1. Buyer confirms order → backend calls `initiate_paystack_payment()`
2. Paystack API returns `authorization_url`
3. Bot sends URL to buyer as plain text link
4. Buyer taps link, completes payment in mobile browser
5. Paystack redirects to `PAYSTACK_CALLBACK_URL?reference=...`
6. Server calls `verify_paystack_payment(reference)` → confirms payment
7. Paystack ALSO sends `charge.success` to `/payment/webhook` as backup

### Critical: GHS vs Pesewas
- Store all prices in **GHS** in the database
- When calling Paystack API, multiply by **100** (Paystack uses pesewas, like kobo)
- Already handled in `initiate_paystack_payment()` — don't break this

### Webhook Signature Verification
Every POST to `/payment/webhook` from Paystack includes `x-paystack-signature` header.
Must verify with HMAC-SHA512:
```python
import hmac, hashlib
computed = hmac.new(
    PAYSTACK_SECRET_KEY.encode('utf-8'),
    request.data,
    hashlib.sha512
).hexdigest()
assert computed == request.headers.get('x-paystack-signature')
```

### Paystack Dashboard Setup
1. Go to https://dashboard.paystack.com
2. Navigate to **Settings** → **API Keys & Webhooks**
3. Copy **Secret Key** (live mode — not test mode for production)
4. Set **Webhook URL** to: `https://zango.up.railway.app/payment/webhook`
5. Enable event: `charge.success`
6. Set **Callback URL** to: `https://zango.up.railway.app/payment/callback`

### Escrow Logic
- Payment is captured at checkout
- Vendor does NOT receive funds immediately
- Platform holds the balance until delivery confirmed (OTP verified)
- Vendor wallet credited after `delivered` status
- **Withdrawal flow: NOT built at MVP**

---

## 3. Africa's Talking (Future — Automated Call Fallback)

**Live docs:** https://developers.africastalking.com/docs/voice

> ⚠️ This is NOT built at MVP. Design decision made — build AFTER core order flow is stable.

### Purpose
If a vendor doesn't respond to a new order within 30 seconds, the system places an automated voice call to the vendor's phone saying:
> "You have a new order on Zan Chop. Please open WhatsApp and accept it now."

### Why Africa's Talking (not Twilio)
- Better Ghana support and pricing
- Lower per-minute rates for Ghana outbound calls
- Twilio is more expensive for Ghana Voice

### Implementation Plan (when building)
1. **Before coding:** Fetch live AT Voice API docs at the URL above
2. Sign up at https://africastalking.com → Create account → Get API Key
3. Environment variables needed:
   ```
   AT_API_KEY=           # Africa's Talking API Key
   AT_USERNAME=          # Africa's Talking username (or 'sandbox' for testing)
   AT_SENDER_PHONE=      # Outbound caller ID (must be registered with AT)
   ```
4. Install SDK: `pip install africastalking`
5. Background job (APScheduler): watch orders stuck in `paid` for 30s → trigger call
6. Call text: configurable string in env var
7. Log call result (answered, not answered, failed) in orders table

---

## 4. Railway (Hosting & Database)

**Live docs:** https://docs.railway.app/

### Adding PostgreSQL to Railway Project
1. Go to Railway dashboard → Your Project → **New Service**
2. Select **Database** → **PostgreSQL**
3. Railway automatically creates `DATABASE_URL` env var and injects it into all services in the project
4. No manual URL copying needed — it's auto-injected

### Adding Redis (for future session caching)
1. Railway dashboard → **New Service** → **Database** → **Redis**
2. Railway injects `REDIS_URL` automatically

### Railway Volumes (for session data in non-PostgreSQL path)
Volumes persist across deploys. Can use to persist `sessions.json` as a temporary fix before full PostgreSQL migration.
However — PostgreSQL is the proper solution. Use volumes only as an emergency bridge.

### Deployment Checklist
- [ ] All env vars set in Railway → Variables
- [ ] Procfile present: `web: gunicorn app:app --bind 0.0.0.0:$PORT`
- [ ] `requirements.txt` up to date
- [ ] No hardcoded env values in code
- [ ] PostgreSQL service attached and `DATABASE_URL` injected

---

## 5. Cloudinary (Future — Cloud Image Storage)

**Live docs:** https://cloudinary.com/documentation/python_integration

> ⚠️ Not built at MVP. Needed before vendor onboarding at scale.
> Current `static/uploads/` is wiped on every Railway redeploy.

### Setup When Building
1. Create Cloudinary account at https://cloudinary.com
2. Get credentials from **Dashboard**:
   ```
   CLOUDINARY_CLOUD_NAME=
   CLOUDINARY_API_KEY=
   CLOUDINARY_API_SECRET=
   ```
3. Install: `pip install cloudinary`
4. On image upload: save to Cloudinary, store returned `secure_url` in `products.image_url`
5. Delete local file after upload

---

## 6. ngrok (Local Development Tunneling)

**Live docs:** https://ngrok.com/docs

### Purpose
When developing locally, Meta can't reach `localhost`. ngrok creates a public HTTPS tunnel.

### Usage
```bash
ngrok http 5000
# Gets a URL like: https://abc123.ngrok.io
# Use this URL as your webhook URL in Meta dashboard during dev
```

### ngrok Webhook URL Updates
Every time you restart ngrok, you get a new URL.
You must update the webhook URL in Meta Developer Dashboard each time.
Use a paid ngrok account with a static domain to avoid this pain.
