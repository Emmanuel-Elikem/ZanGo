# ZanChop — External Setup Guide

> This guide documents every step that requires going outside of code — into dashboards, external platforms, or third-party services. Read the relevant section before starting any integration work.

---

## 1. Railway — Hosting & Infrastructure

**Dashboard:** https://railway.app/dashboard

### Add PostgreSQL Database
1. Log into Railway dashboard
2. Open the **ZanGo project**
3. Click **+ New Service** (top right or in canvas)
4. Select **Database** → **PostgreSQL**
5. Wait ~30 seconds for provisioning
6. Click on the PostgreSQL service → go to **Variables** tab
7. Confirm `DATABASE_URL` is listed — Railway auto-injects this into all services
8. In your Flask service → **Variables** tab → confirm `DATABASE_URL` appears
9. **Docs:** https://docs.railway.app/databases/postgresql

### Set Environment Variables
1. Railway dashboard → ZanGo project → your Flask service
2. Click **Variables** tab
3. Add each env var from the list below (click **+ New Variable** for each):

```
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_WABA_ID=
VERIFY_TOKEN=
WHATSAPP_WEBHOOK_VERIFY_TOKEN=      # Same value as VERIFY_TOKEN

PAYSTACK_SECRET_KEY=
PAYSTACK_CALLBACK_URL=https://zango.up.railway.app/payment/callback

ADMIN_PHONE=                        # Your WhatsApp number without '+'
ADMIN_ACCESS_CODE=                  # Secret code for admin bot access
PUBLIC_URL=https://zango.up.railway.app

DATABASE_URL=                       # Auto-injected when PostgreSQL is added
```

4. After adding all vars → Railway auto-redeploys the service

### Monitor Deployments
- Railway dashboard → Your service → **Deployments** tab
- Click a deployment to see live logs
- Green = success, Red = failed (check logs for error)

---

## 2. Meta Developer Dashboard — WhatsApp Setup

**Dashboard:** https://developers.facebook.com/apps/

### Enable WhatsApp on Your App
1. Log into developers.facebook.com
2. Open your app (should already exist)
3. In the left sidebar, look for **WhatsApp** → **API Setup**
4. If WhatsApp is not added: **Add Product** → **WhatsApp**

### Get Your Phone Number ID and WABA ID
1. App Dashboard → **WhatsApp** → **API Setup**
2. Under "From" section, find **Phone Number ID** — copy this → `WHATSAPP_PHONE_NUMBER_ID`
3. Under "From" section, find **WhatsApp Business Account ID** — copy this → `WHATSAPP_WABA_ID`

### Configure the Webhook
1. App Dashboard → **WhatsApp** → **Configuration**
2. Click **Edit** next to "Webhook"
3. Set **Callback URL:** `https://zango.up.railway.app/webhook`
4. Set **Verify token:** your chosen `VERIFY_TOKEN` value
5. Click **Verify and Save** — Meta will call your webhook to verify
6. After saving, click **Subscribe** to webhook fields
7. Enable: `messages`, `message_template_status_update`

### Generate a Permanent System User Token
1. Go to **Meta Business Manager:** https://business.facebook.com
2. Navigate to **Business Settings** (gear icon, top left)
3. Click **Users** → **System Users**
4. Click **Add** → create a system user with "Admin" role
5. Click the system user → **Generate New Token**
6. Select your app from the dropdown
7. Grant these permissions ONLY:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
8. Click **Generate Token**
9. **Copy the token immediately** — you won't see it again
10. Save as `WHATSAPP_ACCESS_TOKEN` in Railway Variables
11. **Docs:** https://developers.facebook.com/docs/whatsapp/business-management-api/get-started

### Add a Real Phone Number (for production)
1. App Dashboard → **WhatsApp** → **API Setup**
2. Click **Add phone number**
3. Enter the phone number (must be a real SIM you own)
4. Choose verification method: SMS or Voice call
5. Enter the verification code received
6. After verification, update `WHATSAPP_PHONE_NUMBER_ID` in Railway to the new number's ID

### Create Message Templates
1. App Dashboard → **WhatsApp** → **Message Templates**
2. Click **Create Template**
3. Fill in:
   - **Category:** Utility (for order notifications)
   - **Name:** e.g. `order_accepted_notification` (lowercase, underscores)
   - **Language:** English (or local language if needed)
4. Write template body with variables: `{{1}}`, `{{2}}`, etc.
   - Example: `Your order {{1}} has been accepted by {{2}} and is being prepared. 🍽️`
5. Click **Submit**
6. Status changes to "Approved" (usually within minutes to hours)
7. Use the template name + namespace in your API calls

### Submit for Business Verification
> Do this in parallel with development, not as a blocker.
1. Go to https://business.facebook.com
2. **Business Settings** → **Security Center**
3. Click **Start Verification**
4. Complete the steps:
   - Verify business phone number
   - Verify business email
   - Upload business documents (Ghana business registration certificate)
   - Website verification (add DNS record or meta tag)
5. Wait 1–5 business days for Meta review
6. Unlocks: WhatsApp Flows, higher message limits

---

## 3. Paystack — Payment Processing

**Dashboard:** https://dashboard.paystack.com

### Get API Keys
1. Log into Paystack dashboard
2. Navigate to **Settings** (gear icon, left sidebar)
3. Click **API Keys & Webhooks**
4. Copy **Secret Key** (starts with `sk_live_...` for live mode)
5. Save as `PAYSTACK_SECRET_KEY` in Railway Variables
6. **Never use test keys in production.** `sk_test_...` will not process real money.

### Set Webhook URL
1. In same API Keys & Webhooks page
2. Scroll to **Webhook URL** section
3. Enter: `https://zango.up.railway.app/payment/webhook`
4. Click **Update** to save

### Test Live Payments
1. Use a real MTN Mobile Money number in Ghana
2. Place a test order through the bot
3. Check the Paystack dashboard → **Transactions** to confirm receipt
4. Check for the `charge.success` webhook in dashboard → **Webhook Logs**

### Enable Ghana (GHS) Currency
- Paystack Ghana accounts support GHS by default
- No additional setup needed if the account is registered as a Ghana business
- Verify by checking **Settings** → **Business** → Business country = Ghana

---

## 4. Africa's Talking — Voice Call Fallback (Future)

**Dashboard:** https://account.africastalking.com

> ⚠️ Do NOT set this up until ready for Phase 2. Current focus is Phase 0.

### Create Account
1. Go to https://africastalking.com
2. Click **Get Started** → Register
3. Choose **Ghana** as your country
4. Verify email

### Get API Credentials
1. Log in → **Go to Sandbox** (for testing) or **Switch to Live** (for production)
2. In the dashboard, find **Username** — save this
3. Navigate to **Settings** → **API Key** — copy and save

### Set Up Voice Calling
1. Dashboard → **Voice** → **Phone Numbers**
2. Purchase a voice-capable number for Ghana (outbound caller ID)
3. Note: Africa's Talking requires top-up credits for outbound calls
4. Top up via the dashboard → **Billing**
5. Docs: https://developers.africastalking.com/docs/voice

### Environment Variables Needed
```
AT_API_KEY=         # Africa's Talking API key
AT_USERNAME=        # Africa's Talking username
AT_SENDER_PHONE=    # Registered outbound phone number
```

---

## 5. Cloudinary — Cloud Image Storage (Phase 0.3)

**Dashboard:** https://cloudinary.com/console

### Create Account
1. Go to https://cloudinary.com
2. Click **Sign Up Free**
3. Choose a cloud name (this appears in all URLs, e.g. `zandb`)

### Get API Credentials
1. Log in → **Dashboard** (home page)
2. Find the **API Keys** section
3. Copy:
   - **Cloud name** → `CLOUDINARY_CLOUD_NAME`
   - **API Key** → `CLOUDINARY_API_KEY`
   - **API Secret** → `CLOUDINARY_API_SECRET`
4. Save all three in Railway Variables

### Free Tier Limits
- 25GB storage
- 25GB bandwidth/month
- Sufficient for MVP with 3–5 vendors
- Docs: https://cloudinary.com/documentation/python_integration

---

## 6. ngrok — Local Development Tunneling

**Download:** https://ngrok.com/download

### Setup
1. Download ngrok for Linux
2. Create a free account at https://dashboard.ngrok.com
3. Run `ngrok config add-authtoken YOUR_TOKEN`

### Usage During Development
```bash
# In terminal 1: Start Flask
python app.py

# In terminal 2: Start ngrok
ngrok http 5000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Paste this as the webhook URL in Meta Developer Dashboard
```

### Pain Points
- Free ngrok URLs change every restart → must update Meta webhook URL each time
- Solution: buy ngrok paid plan with a static domain (~$8/month) for dev convenience
