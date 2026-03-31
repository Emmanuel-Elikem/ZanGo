# ZanChop — Development Plan & Phases

> **This is the master roadmap. Check this before every session to understand current priority.**
> Last updated: 2026-03-31

---

## Current Status Summary

| Component              | Status                                     |
| ---------------------- | ------------------------------------------ |
| Flask backend          | ✅ Complete (prototype)                    |
| WhatsApp webhook       | ✅ Verified and connected                  |
| Buyer onboarding flow  | ✅ Functional (chatbot style)              |
| Vendor onboarding + approval | ✅ Functional                        |
| Product management     | ✅ Functional                              |
| Order flow             | ✅ Functional                              |
| Paystack payments      | ✅ Integrated                              |
| OTP delivery confirmation | ✅ Functional                           |
| Admin panel            | ✅ Functional                              |
| Railway deployment     | ✅ Live at zango.up.railway.app            |
| **PostgreSQL migration** | ❌ **LAUNCH BLOCKER**                    |
| **Session persistence** | ❌ **LAUNCH BLOCKER**                     |
| **Cloud image storage** | ❌ **LAUNCH BLOCKER**                    |
| Meta business verification | 🔄 In progress (not a hard blocker)  |
| WhatsApp message templates | ❌ Not submitted yet                  |
| Automated call fallback | ❌ Designed, not built                   |
| Vendor wallet withdrawal | ❌ Designed, not built                   |
| WhatsApp Flows UX      | ❌ Post-MVP (requires verified account)    |

---

## Phase 0: Pre-Launch Critical Fixes 🔴 NOW

> **These must be done before any real users touch the system.**
> All 3 items are launch blockers — data is lost on every Railway redeploy.

### P0.1: PostgreSQL Migration
**Why:** SQLite on Railway is ephemeral — every code push wipes all data.
**Steps:**
1. Add `psycopg2-binary` to `requirements.txt`
2. Create `get_db_connection()` helper using `DATABASE_URL` env var
3. Rewrite all SQLite calls to use psycopg2 (`?` → `%s`, `AUTOINCREMENT` → `SERIAL`)
4. Add PostgreSQL service in Railway dashboard
5. Run `init_db()` against PostgreSQL to create schema
6. Test all CRUD operations

**External action required:** Add PostgreSQL in Railway → see [ZanChop-External-Setup-Guide.md](ZanChop-External-Setup-Guide.md)

**Testing:** Run `cli.py` test suite against new DB. Verify user creation, session lookup, order create/update.

---

### P0.2: Session Persistence (PostgreSQL sessions table)
**Why:** `sessions.json` is on the same ephemeral filesystem — wipes with every deploy.
**Steps:**
1. Create `sessions` table in PostgreSQL (see [ZanChop-Database-Schema.md](ZanChop-Database-Schema.md))
2. Replace all reads/writes to `sessions.json` with PostgreSQL queries
3. Add UPSERT logic: `INSERT INTO sessions ... ON CONFLICT (phone) DO UPDATE SET ...`
4. Session expiry: add cleanup job for sessions older than 48h

---

### P0.3: Cloud Image Storage (Cloudinary)
**Why:** `static/uploads/` is on Railway's ephemeral filesystem.
**Steps:**
1. Create Cloudinary account
2. Add `cloudinary` to `requirements.txt`
3. Set env vars: `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
4. Replace `save_image_locally()` → `upload_to_cloudinary()`
5. Store returned `secure_url` in `products.image_url`

**External action required:** Create Cloudinary account → see [ZanChop-External-Setup-Guide.md](ZanChop-External-Setup-Guide.md)

---

## Phase 1: Launch Preparation 🟠 NEXT

> After Phase 0 is done, these prepare for actual go-live with real users.

### P1.1: Get Real Phone Number on Meta Account
The test number provided by Meta has limitations (only 5 test recipient numbers).
**Steps:**
1. Purchase a Ghana SIM card or port an existing number
2. Register it in **Meta Developer Dashboard** → WhatsApp → **Phone Numbers** → Add Phone Number
3. Verify via SMS or voice call
4. Update webhook to point to new number's Phone Number ID
5. Update `WHATSAPP_PHONE_NUMBER_ID` env var in Railway

---

### P1.2: Submit WhatsApp Message Templates
Proactive order notifications require pre-approved templates.
**Templates to create:**
- `order_paid` — payment confirmed, order placed
- `order_accepted` — vendor accepted, preparing
- `order_on_the_way` — food dispatched
- `order_delivered` — delivered, ask for rating
- `order_cancelled` — order cancelled, refund processing

**External action required:** → see [ZanChop-External-Setup-Guide.md](ZanChop-External-Setup-Guide.md) → Meta Template Section

---

### P1.3: End-to-End Test (Full Buyer Flow)
Complete journey test with real phone:
- [ ] New user messages bot → Welcome screen
- [ ] Tap Buy Food → Registration
- [ ] Browse vendors → View menu
- [ ] Add to cart → Customise
- [ ] Checkout → Paystack link sent
- [ ] Complete payment → Vendor notified
- [ ] Vendor accepts → Buyer notified "Preparing"
- [ ] Vendor: On The Way → Buyer notified
- [ ] Buyer enters OTP → Order marked Delivered
- [ ] Vendor wallet balance updated

---

### P1.4: Onboard First 3 Vendors
Manually onboard 3 real vendors via admin panel:
- [ ] Vendor creates account via WhatsApp
- [ ] Admin reviews and approves in admin panel
- [ ] Vendor adds products with images
- [ ] Vendor sets delivery zones
- [ ] Vendor tests receiving a test order

---

## Phase 2: Reliability & Vendor Experience 🟡 POST-LAUNCH

> After stable launch with real users.

### P2.1: 30-Second Vendor Timeout (Automated Alert)
Background job watches for orders stuck in `paid` without acceptance.
- Use APScheduler (`pip install apscheduler`)
- Set up as in-process scheduler (not a separate Railway service at this scale)
- After 30s: send timeout alert to vendor with Accept/Reject buttons
- Log timeout events for analytics

### P2.2: Automated Call Fallback (Africa's Talking)
If vendor still doesn't respond after timeout alert:
- Place outbound voice call via Africa's Talking Voice API
- Message: "You have a new order on Zan Chop. Please open WhatsApp and accept it now."
- Log call outcome (answered, voicemail, failed)
- After call + additional grace period with no response → auto-cancel + refund

**External action required:** Africa's Talking account → see [ZanChop-External-Setup-Guide.md](ZanChop-External-Setup-Guide.md)

### P2.3: Order Rating System
After delivery, buyer prompted to rate their experience.
- Star rating (1–5) via interactive buttons
- Optional text comment
- Stored against order record
- Feeds into seller rating displayed during browse

---

## Phase 3: UX Upgrade to WhatsApp Flows 🔵 AFTER META VERIFICATION

> This phase requires Meta Business Verification (can be pursued in parallel).

### P3.1: Meta Business Verification
**Process:**
1. Go to **Meta Business Manager** → business.facebook.com
2. Navigate to **Business Settings** → **Security Center**
3. Click **Start Verification**
4. Submit: business documents (registration certificate), website, phone number
5. Verification takes 1–5 business days

### P3.2: Build and Deploy WhatsApp Flows
Once verified, build each Flow defined in [ZanChop-Bot-Flow.md](ZanChop-Bot-Flow.md):
- Buyer Registration Flow (replaces chatbot onboarding)
- Food Ordering Flow (replaces browse → cart → checkout message chain)
- Order Tracking Flow
- Seller Registration Flow
- Product Management Flow
- Status Update Flow

**Testing:** Each Flow must be tested in WhatsApp before going live.

---

## Phase 4: Scale & Expand 🟢 FUTURE

- Multi-campus expansion beyond UCC
- Vendor-set delivery zone pricing (zone rank pricing algorithm)
- Analytics dashboard for Zan Chop admin
- Third-party rider logistics integration
- Vendor wallet withdrawal (MTN MoMo, bank transfer)
- Push notification improvements (rich media templates)
- Proactive marketing campaigns (with template limits in mind)
