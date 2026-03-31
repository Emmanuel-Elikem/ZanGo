# ZanChop — Bot Flow Reference

> **Read this before any WhatsApp message, state machine, or conversation flow change.**
> For full detailed flow design with screen mockups, see the original `ZanGo_bot_flow.md` at the project root.

---

## 1. Entry Point Logic

When any message arrives on the webhook:
1. Normalize the sender's phone number (strip `+`)
2. Look up session state
3. Look up user in database

```
phone received
    │
    ├── No session / state = "new_user"?
    │       → Send Welcome Message (Buy Food / Sell Food buttons)
    │
    ├── User is BUYER (role=buyer)?
    │       → handle_buyer_flow()
    │
    ├── User is SELLER (role=seller)?
    │       → handle_seller_flow()
    │
    └── User is ADMIN?
            → handle_admin_flow()
```

---

## 2. Welcome Message (New / Unregistered Users)

```
🍽️ Welcome to Zan Chop!
Your favourite food, delivered fast across Cape Coast. UCC campus and beyond.
What would you like to do?

[🛒 Buy Food]  [🏪 Sell Food]
```
Interactive buttons. Tapping launches registration.

---

## 3. Buyer States & Transitions

| State                   | What the User Sees                              | Next Possible States          |
| ----------------------- | ----------------------------------------------- | ----------------------------- |
| `new_user`              | Welcome message with Buy/Sell buttons           | → `buyer_onboarding_name`     |
| `buyer_onboarding_name` | "What's your name?" text prompt                 | → `buyer_onboarding_zone`     |
| `buyer_onboarding_zone` | Zone selection list                             | → `buyer_onboarding_address`  |
| `buyer_onboarding_address` | "Enter your address" text prompt             | → `buyer_menu`                |
| `buyer_menu`            | Main menu: Order Food / My Orders / Help        | → `buyer_browsing`, `buyer_orders`, `buyer_help` |
| `buyer_browsing`        | Vendor list picker                              | → `buyer_menu_view`           |
| `buyer_menu_view`       | Food items list for selected vendor             | → `buyer_customise`           |
| `buyer_customise`       | Portion, spice, add-ons, qty, notes             | → `buyer_cart`                |
| `buyer_cart`            | Cart review + delivery method selection         | → `buyer_checkout`            |
| `buyer_checkout`        | Order summary + payment link sent               | → `buyer_menu` (after payment)|
| `buyer_orders`          | List of past/active orders                      | → order detail view           |
| `buyer_help`            | FAQ text + support contact                      | → `buyer_menu`                |

---

## 4. Seller States & Transitions

| State                      | What the Seller Sees                            | Next Possible States            |
| -------------------------- | ----------------------------------------------- | ------------------------------- |
| `seller_onboarding_name`   | Name, phone, restaurant name prompts            | → `seller_onboarding_details`   |
| `seller_onboarding_details`| Category, location, description prompts         | → pending approval              |
| `seller_pending`           | "Application submitted, check back soon"        | Awaiting admin action           |
| `seller_menu`              | Products / Orders / Wallet / Zones / Profile    | → respective state              |
| `seller_products`          | Product list + Add/Edit buttons                 | → `seller_add_product`          |
| `seller_add_product`       | Product form fields                             | → `seller_products`             |
| `seller_orders`            | Active orders list                              | → order action (accept/reject)  |
| `seller_update_status`     | Status progression buttons for a specific order | → `seller_menu`                |
| `seller_wallet`            | Balance display + withdrawal (future)           | → `seller_menu`                 |
| `seller_zones`             | Zone list with toggles + Add zone               | → `seller_menu`                 |
| `seller_profile`           | Edit store name, description, hours, status     | → `seller_menu`                 |

---

## 5. Order Notification Messages (Push — Not Triggered by User)

These are sent proactively by the backend when order status changes:

### TO VENDOR — New Order
```
🔔 NEW ORDER! #8472
⏱️ Respond within 30 seconds

📋 Items:
• Jollof Rice (Large, Hot, Extra Meat) × 1 — GH₵ 38.00

📝 Note: "No onions, extra gravy on the side"
💰 Total: GH₵ 50.00
📍 Delivery: SRC — Hostel B Room 204

[✅ Accept]  [❌ Reject]
```

### TO BUYER — Order Confirmed (Preparing)
```
👨‍🍳 Order #8472 — Preparing!
Aunty Ama's Kitchen has accepted your order.
Estimated time: 20-30 minutes

[📦 Track Order]
```

### TO BUYER — On The Way
```
🚗 Order #8472 — On the Way!
Your food is on its way to SRC, Hostel B Room 204.

[📦 Track Order]
```

### TO BUYER — Delivered
```
✅ Order #8472 — Delivered!
Enjoy your meal! 🍽️

[⭐ Rate Order]  [🍽️ Order Again]
```

### TO BUYER — Cancelled
```
❌ Order #8472 — Cancelled
Aunty Ama's Kitchen was unable to accept your order.
Your payment of GH₵ 50.00 will be refunded within 24 hours.

[🍽️ Try Another Restaurant]  [❓ Help]
```

---

## 6. 30-Second Vendor Timeout

```
Backend timer starts when order notification sent to vendor
    │
    ├── Vendor responds within 30s → ✅ Normal flow
    │
    └── No response after 30s
            │
            ├── Send timeout alert to vendor:
            │   "⚠️ ORDER TIMEOUT! #8472
            │    You haven't responded. Customer is waiting!
            │    [✅ Accept Now]  [❌ Reject]"
            │
            └── Still no response after grace period
                    │
                    ├── (Future) Trigger Africa's Talking voice call to vendor
                    └── Auto-cancel order + notify buyer + process refund
```

---

## 7. MVP vs Target UX

| Feature              | MVP (Current)                  | Target UX (Post-Verification)         |
| -------------------- | ------------------------------ | ------------------------------------- |
| Registration         | Sequential text prompts + lists | WhatsApp Flow (2-screen form)         |
| Browsing food        | List messages                   | WhatsApp Flow (multi-screen)          |
| Cart & checkout      | Sequential messages             | WhatsApp Flow (5-screen ordering)     |
| Order tracking       | Text messages                   | WhatsApp Flow (order list + detail)   |
| Product management   | Sequential prompts              | WhatsApp Flow (product list + form)   |

---

## 8. Payload Types Handled

| `message.type`                  | Meaning                        | Handler                       |
| ------------------------------- | ------------------------------ | ----------------------------- |
| `text`                          | User typed a message           | Parse by state, route to handler |
| `interactive` → `button_reply`  | User tapped a reply button     | Route by `button_reply.id`    |
| `interactive` → `list_reply`    | User selected from list        | Route by `list_reply.id`      |
| `interactive` → `nfm_reply`     | User completed a Flow          | Parse Flow response payload   |
| `image`                         | User sent an image             | Save image if in product-add state |

---

## 9. Button & List ID Conventions

Use clear, namespaced IDs so routing is unambiguous:

```python
# Buyer main menu buttons
"btn_order_food"
"btn_my_orders"
"btn_help"

# Vendor order action buttons
"btn_accept_order_{order_id}"
"btn_reject_order_{order_id}"

# Status update buttons
"btn_status_preparing_{order_id}"
"btn_status_on_the_way_{order_id}"
"btn_status_delivered_{order_id}"
"btn_status_cancel_{order_id}"

# Zone selection list rows
"zone_ucc_main"
"zone_ucc_north"
"zone_amamoma"
# ...etc
```
