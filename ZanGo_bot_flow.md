


# ZAN CHOP — WhatsApp Bot Flow Architecture & Conversation Design

## Using Meta WhatsApp Flows for Food Ordering

---

## 1. HIGH-LEVEL ARCHITECTURE OVERVIEW

The Zan Chop WhatsApp food ordering system is built on top of Meta's **WhatsApp Business API** and leverages the **WhatsApp Flows** feature to deliver a compact, form-like ordering experience inside the WhatsApp chat window. Instead of the traditional chatbot model — where every user choice sends a message, then the bot replies with another message, then the user replies again, creating a long scrolling conversation — the system uses WhatsApp Flows to present multi-screen, interactive forms that slide up as an overlay within WhatsApp itself. The user fills out selections, taps next, fills out more, and submits — all without flooding the chat with dozens of messages.

The architecture consists of **three layers**:

1. **WhatsApp Chat Layer** — The actual WhatsApp conversation thread. This is where the bot sends initial greeting messages, CTA (Call-To-Action) buttons that launch flows, order confirmation messages, status update notifications, and support messages. This layer is kept minimal and clean.

2. **WhatsApp Flows Layer** — These are the interactive, multi-screen forms that open as overlays inside WhatsApp when the user taps a Flow-launching button. This is where the heavy lifting happens: registration, browsing restaurants, customising food, cart management, checkout, and payment method selection all happen inside Flows. The user never leaves WhatsApp, but the experience feels like a mini-app.

3. **Backend Server Layer** — A server (Node.js, Python, or similar) that receives webhook events from WhatsApp, processes Flow responses, manages the database (users, restaurants, menus, orders, carts, payments), communicates with payment gateways (MTN Mobile Money, Vodafone Cash), and sends outbound messages/notifications back through the WhatsApp Business API.

**The core principle**: The WhatsApp chat thread acts as a notification and navigation hub. The WhatsApp Flows act as the interactive UI. The backend handles all business logic and data persistence.

---

## 2. ENTRY POINT — FIRST CONTACT

### 2.1 User Sends First Message

The entire experience begins when a user messages the Zan Chop WhatsApp Business number for the first time. They might type "Hi," "Hello," "I want to order food," or anything at all. The webhook on the backend receives this incoming message.

**What happens on the backend:**
- The backend checks its database to see if this phone number is already registered.
- If the user is **not registered**, the system sends back a **Welcome Message** with two CTA buttons.
- If the user **is already registered as a buyer**, the system sends back the **Buyer Main Menu** message.
- If the user **is already registered as a seller**, the system sends back the **Seller Main Menu** message.

### 2.2 Welcome Message (New Users)

The bot sends an **Interactive Message** (button type) that looks like this in the chat:

> 🍽️ **Welcome to Zan Chop!**
>
> Your favourite food, delivered fast across Cape Coast. UCC campus and beyond.
>
> What would you like to do?
>
> **[🛒 Buy Food]** **[🏪 Sell Food]**

These are two **reply buttons**. The user taps one.

- If they tap **"Buy Food"** → The backend launches the **Buyer Registration Flow**.
- If they tap **"Sell Food"** → The backend launches the **Seller Registration Flow**.

---

## 3. BUYER FLOW — COMPLETE JOURNEY

### 3.1 Buyer Registration Flow

When the new user taps "Buy Food," the backend sends an Interactive Message with a **Flow CTA button** that opens the Buyer Registration Flow. The message in chat says:

> Let's get you set up! Tap below to register — it takes 30 seconds.
>
> **[📝 Register Now]** ← This button launches the Flow

**The user taps "Register Now."** A WhatsApp Flow overlay slides up from the bottom of the screen, inside WhatsApp. This Flow contains **two screens**:

---

**FLOW: Buyer Registration**

**Screen 1 of 2 — "Your Details"**

| Field | Type | Details |
|---|---|---|
| Full Name | Text input | Required. Placeholder: "e.g. Kwame Mensah" |
| Phone Number | Text input (tel) | Pre-filled with their WhatsApp number. Editable. Required. |

At the bottom: **[Next →]** button.

When the user fills in their name and phone and taps "Next," the Flow advances to Screen 2.

---

**Screen 2 of 2 — "Delivery Location"**

| Field | Type | Details |
|---|---|---|
| Delivery Area | Dropdown / Single-select | Options: SRC, Superannuation, PSI, ATL, Casford, Valco, KNH, Oguaa, Adehyie |
| Street Address | Text input | Required. Placeholder: "e.g. Hostel B, Room 204" |
| Landmark | Text input | Optional. Placeholder: "e.g. Near the blue gate" |

At the bottom: **[Complete Registration ✓]** button.

When the user taps "Complete Registration," the Flow closes. The Flow response payload is sent to the backend webhook. The backend:
1. Creates a new buyer record in the database with name, phone, area, address, landmark.
2. Sends a confirmation message in the chat:

> ✅ **You're all set, Kwame!**
>
> Your delivery area: **SRC — University of Cape Coast**
>
> You can now order delicious food from restaurants near you. Tap the menu below to get started!
>
> **[🍽️ Order Food]** **[📦 My Orders]** **[❓ Help]**

These three buttons form the **Buyer Main Menu**. This same menu is sent anytime a registered buyer messages the bot or types "menu."

---

### 3.2 Buyer Main Menu

After registration (or any time a returning buyer messages the bot), the buyer sees:

> 👋 **Hey Kwame!** What are you in the mood for?
>
> **[🍽️ Order Food]** **[📦 My Orders]** **[❓ Help]**

Each button does something different:

- **"Order Food"** → Launches the **Food Ordering Flow** (the main, multi-screen ordering experience)
- **"My Orders"** → Launches the **Order Tracking Flow** (view current and past orders)
- **"Help"** → Launches the **Buyer Help Flow** (FAQs + contact support)

Let's go through each one.

---

### 3.3 Food Ordering Flow — The Core Experience

This is the heart of the entire system. When the buyer taps "Order Food," the backend sends a message with a Flow CTA:

> 🔍 Browse restaurants and pick your meal! Tap below to start.
>
> **[🍽️ Browse & Order]** ← Launches the Flow

**The user taps the button.** The Food Ordering Flow opens as an overlay. This Flow has **multiple screens** that guide the user from browsing to checkout:

---

**FLOW: Food Ordering**

**Screen 1 — "Find Food"**

This screen serves as a combination of search and restaurant browsing.

| Element | Type | Details |
|---|---|---|
| Search Bar | Text input | Optional. Placeholder: "Search for food or restaurant..." |
| Trending / Popular | Static list | Shows 3-4 trending items like "🔥 Jollof Rice," "🔥 Banku & Tilapia," "🔥 Waakye" — these are tappable quick-filters |
| Restaurant List | Selectable list | Each item shows: Restaurant emoji/icon, Restaurant name, Cuisine type (e.g. "Local Dishes • Rice Specials"), Rating (e.g. ⭐ 4.8), Delivery time estimate (e.g. "25-35 min") |

The user taps on a restaurant to select it. Options include restaurants like:
- 🍚 Aunty Ama's Kitchen — Local Dishes • Rice Specials
- 🍗 Chop Bar Plus — Grills • Banku • Kenkey
- 🥘 Cape Coast Bites — Mixed Menu • Fast Food
- 🍛 Mama's Joint — Soups • Fufu • TZ

At the bottom: **[View Menu →]** button (activates after a restaurant is selected).

---

**Screen 2 — "Menu" (Dynamic based on selected restaurant)**

This screen shows the food items available at the selected restaurant.

| Element | Type | Details |
|---|---|---|
| Restaurant Header | Static text | Shows selected restaurant name and a short description |
| Menu Items | Multi-select / Selectable list | Each item shows: Food emoji, Item name, Price (e.g. "GH₵ 25.00"), Short description. User can tap to select one or more items. A green checkmark appears on selected items. |

Example menu items for "Aunty Ama's Kitchen":
- 🍚 Jollof Rice — GH₵ 25.00 — "Smoky party-style jollof with chicken"
- 🍛 Fried Rice + Chicken — GH₵ 30.00 — "Special fried rice with grilled chicken"
- 🥘 Waakye Special — GH₵ 20.00 — "With spaghetti, gari, egg, and fish"
- 🍲 Banku & Okro Stew — GH₵ 22.00 — "With your choice of protein"
- 🍖 Grilled Tilapia — GH₵ 35.00 — "Whole tilapia with banku and pepper"

The user selects item(s). At the bottom: **[Customise Order →]** button.

---

**Screen 3 — "Customise Your Order"**

This is where the user fine-tunes their selected item(s). If multiple items were selected, this screen shows customisation for each item (or the primary/first item with an option to customise others).

| Field | Type | Details |
|---|---|---|
| Selected Item | Header text | Shows the item name and base price |
| Portion Size | Single-select radio | Options: Regular, Large (+GH₵ 5), Extra Large (+GH₵ 10) |
| Spice Level | Single-select radio | Options: Mild, Medium, Hot 🌶️, Extra Hot 🔥🔥 |
| Add-ons | Multi-select checkboxes | Options vary by item. Examples: Extra Meat (+GH₵ 8), Extra Fish (+GH₵ 10), Egg (+GH₵ 3), Plantain (+GH₵ 5), Avocado (+GH₵ 5), Extra Pepper (+GH₵ 2) |
| Quantity | Number stepper / Dropdown | Default: 1. Options: 1 through 10 |
| Special Instructions | Text input (multi-line) | Optional. Placeholder: "e.g. No onions, extra gravy on the side" |

At the bottom: **[Add to Cart 🛒]** button.

---

**Screen 4 — "Your Cart"**

This screen shows everything the user has added and allows final adjustments.

| Element | Type | Details |
|---|---|---|
| Cart Items | Dynamic list | Each item shows: Name, customisations summary (e.g. "Large • Hot • Extra Meat"), Quantity with +/- controls or a dropdown, Line total (qty × unit price), Remove ✕ button |
| Subtotal | Calculated display | Sum of all line totals |
| Delivery Method | Single-select radio | Options: 🚗 Delivery (+ GH₵ 12.00), 🏃 Pickup (Free) |
| Delivery Address | Pre-filled text | Shows their registered address. With a **[Change]** link/button that opens an inline edit or a sub-screen |
| Delivery Fee | Calculated display | GH₵ 12.00 if delivery, GH₵ 0.00 if pickup |
| **Total** | Bold calculated display | Subtotal + Delivery Fee |

At the bottom: **[Proceed to Checkout →]** button.

---

**Screen 5 — "Checkout & Payment"**

The final screen before the order is placed.

| Element | Type | Details |
|---|---|---|
| Order Summary | Static display | Shows item count, restaurant name, delivery method, total amount |
| Delivery Info | Static display | Shows delivery area, address, landmark (or "Pickup" if pickup was selected) |
| Payment Method | Single-select list | Options: 📱 MTN Mobile Money — "Pay with your MTN MoMo", 📱 Vodafone Cash — "Pay with Vodafone Cash", 💳 Bank Card — "Pay with Visa/Mastercard" |
| MoMo Number | Text input (conditional) | Appears only if MTN MoMo or Vodafone Cash is selected. Pre-filled with registered phone. Editable. |

At the bottom: **[Pay GH₵ XX.00 💰]** button.

---

**When the user taps "Pay":**

The Flow closes. The response payload (containing all order details — items, customisations, quantities, delivery info, payment method) is sent to the backend webhook.

**The backend then:**

1. Creates an order record in the database with a unique Order ID (e.g. #8472).
2. Sets the order status to **"Pending."**
3. Initiates the payment process (sends a payment prompt to the user's mobile money number if MoMo/Vodafone, or initiates a card charge).
4. Sends the buyer an **Order Confirmation Message** in the chat:

> ✅ **Order Placed Successfully!**
>
> 📋 **Order #8472**
> 🏪 Aunty Ama's Kitchen
> 🍚 Jollof Rice (Large, Hot, Extra Meat) × 1 — GH₵ 38.00
> 🚗 Delivery to: SRC, Hostel B Room 204
> 💰 Total: **GH₵ 50.00**
> 📱 Payment: MTN Mobile Money
>
> ⏳ Status: **Pending** — Waiting for restaurant to accept
>
> We'll notify you when your order is confirmed!
>
> **[📦 Track Order]** **[🍽️ Order Again]**

5. Simultaneously, the backend sends a **New Order Notification** to the seller/restaurant's WhatsApp number (see Seller Flow, Section 4).

6. Starts the **30-second order timeout timer** on the backend. If the seller doesn't accept or reject within 30 seconds, the system triggers an alert to the seller.

---

### 3.4 Order Tracking Flow

When the buyer taps "My Orders" from the main menu (or "Track Order" from the confirmation message), the backend sends a Flow CTA:

> 📦 View your orders and track their status. Tap below.
>
> **[📦 View Orders]** ← Launches the Flow

---

**FLOW: Order Tracking (Buyer)**

**Screen 1 — "My Orders"**

| Element | Type | Details |
|---|---|---|
| Filter Tabs | Single-select horizontal | Options: All, Pending, Preparing, On the Way, Delivered, Cancelled. Default: All |
| Order List | Selectable list | Each order card shows: Order ID (#8472), Restaurant name, Date & time, Item summary (e.g. "Jollof Rice × 1, Fried Rice × 2"), Total amount, Status badge (color-coded: 🟡 Pending, 🔵 Preparing, 🟠 On the Way, 🟢 Delivered, 🔴 Cancelled) |

The user taps on an order to view details. At the bottom: **[View Details →]** button.

---

**Screen 2 — "Order Details"**

| Element | Type | Details |
|---|---|---|
| Order ID | Header | e.g. "Order #8472" |
| Status | Large badge | Current status with color coding |
| Restaurant | Text | Restaurant name |
| Items | List | Full item breakdown with customisations, quantities, and line prices |
| Subtotal | Text | Line items total |
| Delivery Fee | Text | GH₵ 12.00 or Free |
| Total | Bold text | Final amount |
| Delivery Info | Text | Address and landmark |
| Special Note | Text (if any) | "No onions, extra gravy" |
| Cancel Button | Destructive button | **[❌ Cancel Order]** — Only visible if status is "Pending" |

If the user taps "Cancel Order," a confirmation prompt appears within the Flow: "Are you sure you want to cancel this order?" with **[Yes, Cancel]** and **[Go Back]** buttons. If confirmed, the Flow closes and the backend updates the order status to "Cancelled," notifies the seller, and sends a cancellation confirmation message in the chat.

---

### 3.5 Buyer Help Flow

When the buyer taps "Help," a Flow opens with FAQs and support options.

---

**FLOW: Buyer Help**

**Screen 1 — "Help & Support"**

| Element | Type | Details |
|---|---|---|
| FAQ List | Expandable/accordion-style list (or a scrollable list with items that link to Screen 2) | Common questions: "How do I place an order?", "How long does delivery take?", "How do I pay?", "Can I cancel my order?", "What areas do you deliver to?", "How do I contact support?" |
| Contact Options | Buttons at bottom | **[📞 Call Support]** — Opens phone dialer, **[💬 Chat with Support]** — Closes Flow, sends a message in chat that connects them to a live agent or shows the support number |

Since WhatsApp Flows have limited interactivity for accordions, the FAQs might be displayed as a scrollable list of question-answer pairs, or as selectable items where tapping one navigates to a detail screen showing the answer.

---

### 3.6 Change Location (Sub-flow within Cart)

If during checkout the buyer wants to change their delivery address, either:
- The Cart screen in the Flow has inline editable fields for delivery area (dropdown) and address (text input), or
- There's an additional screen in the Flow that the user navigates to by tapping "Change" next to the address, edits their delivery area (dropdown with all 9 zones), address, and landmark, then navigates back to the Cart screen.

---

### 3.7 Ongoing Order Status Updates (Push Notifications)

After an order is placed, the buyer receives **proactive WhatsApp messages** (not Flows) whenever the order status changes. These are sent by the backend using WhatsApp message templates:

**When status changes to "Preparing":**
> 👨‍🍳 **Order #8472 — Preparing!**
>
> Aunty Ama's Kitchen has accepted your order and is now preparing your food.
>
> Estimated time: 20-30 minutes
>
> **[📦 Track Order]**

**When status changes to "On the Way":**
> 🚗 **Order #8472 — On the Way!**
>
> Your food is on its way to SRC, Hostel B Room 204.
>
> **[📦 Track Order]**

**When status changes to "Delivered":**
> ✅ **Order #8472 — Delivered!**
>
> Enjoy your meal! 🍽️
>
> How was your experience?
>
> **[⭐ Rate Order]** **[🍽️ Order Again]**

**If order is cancelled (by seller or timeout):**
> ❌ **Order #8472 — Cancelled**
>
> Unfortunately, Aunty Ama's Kitchen was unable to accept your order.
>
> Your payment of GH₵ 50.00 will be refunded within 24 hours.
>
> **[🍽️ Try Another Restaurant]** **[❓ Help]**

---

## 4. SELLER FLOW — COMPLETE JOURNEY

### 4.1 Seller Registration Flow

When a new user taps "Sell Food" on the welcome message, the backend sends a Flow CTA:

> 🏪 Want to sell food on Zan Chop? Register your restaurant below!
>
> **[📝 Register Restaurant]** ← Launches the Flow

---

**FLOW: Seller Registration**

**Screen 1 of 2 — "Your Details"**

| Field | Type | Details |
|---|---|---|
| Full Name | Text input | Required. Owner/manager name. |
| Phone Number | Text input (tel) | Pre-filled with WhatsApp number. Required. |
| Restaurant Name | Text input | Required. Placeholder: "e.g. Aunty Ama's Kitchen" |

At the bottom: **[Next →]**

---

**Screen 2 of 2 — "Restaurant Info"**

| Field | Type | Details |
|---|---|---|
| Food Category | Dropdown | Options: Local Dishes, Rice Specials, Grills & BBQ, Fast Food, Soups & Stews, Mixed Menu, Pastries & Snacks, Beverages |
| Location | Text input | Required. Placeholder: "e.g. Near UCC Main Gate" |
| Description | Text area | Required. Placeholder: "Tell customers what makes your food special..." |

At the bottom: **[Submit for Approval ✓]**

---

**When the seller taps "Submit for Approval":**

The Flow closes. The backend:
1. Creates a seller record with status "pending_approval."
2. Sends a confirmation message in chat:

> 📋 **Application Submitted!**
>
> Thank you for registering **Aunty Ama's Kitchen** on Zan Chop!
>
> 📌 **What happens next:**
> 1. Our team will review your application (usually within 24 hours)
> 2. You'll receive a notification once approved
> 3. You can then set up your menu and start receiving orders
>
> **[👁️ Preview Dashboard]** **[❓ Help]**

If the seller taps "Preview Dashboard," the backend sends the Seller Main Menu (see below). In a real production system, the seller dashboard would be limited until approval is granted.

---

### 4.2 Seller Main Menu

Once approved (or for demo/preview), when the seller messages the bot:

> 🏪 **Aunty Ama's Kitchen — Seller Dashboard**
>
> What would you like to manage?
>
> **[📋 My Products]** **[📦 Orders]** **[💰 Wallet]**

And a second message (since WhatsApp limits buttons to 3 per message):

> More options:
>
> **[📍 Delivery Zones]** **[🏪 Store Profile]** **[❓ Help]**

Each button either launches a Flow or sends relevant information.

---

### 4.3 Product Management Flow

When the seller taps "My Products," the backend sends a Flow CTA:

> 📋 Manage your menu items. Tap below.
>
> **[📋 Manage Products]** ← Launches the Flow

---

**FLOW: Product Management**

**Screen 1 — "My Products"**

| Element | Type | Details |
|---|---|---|
| Product List | Scrollable list | Each product shows: Food emoji/photo placeholder, Product name, Price (GH₵), Status badge (🟢 Active / 🔴 Unavailable). Products are tappable. |
| Add New Button | Navigation button at bottom | **[+ Add New Product]** → navigates to Screen 2 |

If the seller taps an existing product, they navigate to Screen 2 with the fields pre-filled for editing.

---

**Screen 2 — "Add / Edit Product"**

| Field | Type | Details |
|---|---|---|
| Product Name | Text input | Required. Placeholder: "e.g. Jollof Rice Special" |
| Description | Text area | Required. Placeholder: "Describe the dish..." |
| Price (GH₵) | Number input | Required. |
| Category | Dropdown | Options: Rice Dishes, Soups, Grills, Local Specials, Sides, Drinks, Desserts |
| Add-ons | Text input | Optional. Comma-separated. Placeholder: "e.g. Extra Meat, Egg, Plantain" |
| Available | Toggle/Checkbox | Default: Yes/On. Allows seller to mark item as unavailable without deleting. |

At the bottom: **[Save Product ✓]**

When saved, the Flow closes. The backend updates the menu in the database and sends a toast-style confirmation in chat:

> ✅ **"Jollof Rice Special"** has been added to your menu at **GH₵ 25.00**.

---

### 4.4 Order Management — The Critical Seller Experience

This is the most important part of the seller flow. When a new order comes in, the seller receives a **proactive WhatsApp message** (not triggered by them — it's a push notification from the backend):

> 🔔 **NEW ORDER! #8472**
>
> ⏱️ **Respond within 30 seconds**
>
> 📋 **Items:**
> • Jollof Rice (Large, Hot, Extra Meat) × 1 — GH₵ 38.00
>
> 📝 **Note:** "No onions, extra gravy on the side"
>
> 💰 **Total:** GH₵ 50.00
> 📍 **Delivery:** SRC — Hostel B Room 204
>
> **[✅ Accept]** **[❌ Reject]**

These are **reply buttons** — not a Flow — because speed is critical. The seller needs to respond quickly without opening a multi-screen form.

**30-Second Timeout System:**
- The backend starts a 30-second countdown when the order notification is sent.
- If the seller doesn't tap Accept or Reject within 30 seconds, the backend sends a follow-up alert:

> ⚠️ **ORDER TIMEOUT! #8472**
>
> You haven't responded to this order. The customer is waiting!
>
> **[✅ Accept Now]** **[❌ Reject]**

- If still no response after an additional grace period (configurable), the order may be auto-cancelled or reassigned.

**If the seller taps "Accept":**
- Backend updates order status to "Preparing."
- Sends confirmation to seller:

> ✅ **Order #8472 Accepted!**
>
> Status: **Preparing** 👨‍🍳
>
> When the food is ready, update the status:
>
> **[📦 Update Status]** ← This launches a Flow

- Sends notification to buyer (status changed to "Preparing").

**If the seller taps "Reject":**
- Backend asks for confirmation or reason (optional):

> Are you sure you want to reject Order #8472?
>
> **[Yes, Reject]** **[Go Back]**

- If confirmed, order status → "Cancelled." Buyer is notified. Payment is refunded.

---

### 4.5 Status Update Flow

When the seller taps "Update Status" on an accepted order, a Flow opens:

---

**FLOW: Update Order Status**

**Screen 1 — "Update Status"**

| Element | Type | Details |
|---|---|---|
| Order Info | Static header | "Order #8472 — Currently: Preparing" |
| New Status | Single-select radio list | Shows only the **allowed next statuses** based on the current status (using the STATUS_FLOW progression rules): |

**Status Progression Rules:**
| Current Status | Allowed Next Options |
|---|---|
| Pending | Preparing, Cancelled |
| Preparing | On the Way, Cancelled |
| On the Way | Delivered |
| Delivered | *(Terminal — no further updates)* |
| Cancelled | *(Terminal — no further updates)* |

So if the current status is "Preparing," the seller sees:
- 🚗 On the Way
- ❌ Cancelled

At the bottom: **[Update ✓]**

When the seller taps "Update," the Flow closes. The backend:
1. Updates the order status in the database.
2. Sends confirmation to seller:
> ✅ Order #8472 status updated to **On the Way** 🚗
3. Sends notification to buyer with the new status.

---

### 4.6 Seller Orders Overview Flow

When the seller taps "Orders" from the main menu, a Flow opens showing all their orders:

---

**FLOW: Seller Orders**

**Screen 1 — "Your Orders"**

| Element | Type | Details |
|---|---|---|
| Filter | Dropdown or segmented control | Options: All, Pending, Preparing, On the Way, Delivered, Cancelled |
| Order List | Scrollable list | Each order shows: Order ID, Customer name, Item summary, Total, Status badge (color-coded), Time placed. Tappable for details. |

Tapping an order could either:
- Navigate to a detail screen within the Flow showing full order info with an "Update Status" button, OR
- Close the Flow and send the order details as a chat message with action buttons.

The simpler approach (and better for seller efficiency) is the latter: the Flow shows the list, and the seller taps an order to close the Flow and receive an interactive message in chat with that specific order's details and action buttons.

---

### 4.7 Wallet Flow

When the seller taps "Wallet":

---

**FLOW: Wallet**

**Screen 1 — "Your Wallet"**

| Element | Type | Details |
|---|---|---|
| Balance | Large display | "GH₵ 1,245.00" (total earnings available for withdrawal) |
| Pending | Sub-display | "GH₵ 180.00 pending" (from orders not yet delivered) |
| Withdrawal Section | Form fields | Amount (number input), Withdrawal Method (dropdown: MTN MoMo, Vodafone Cash, Bank Transfer), Account Number (text input) |

At the bottom: **[Withdraw Funds 💰]**

When the seller taps "Withdraw," the Flow closes. The backend processes the withdrawal request and sends a confirmation:

> 💰 **Withdrawal Requested!**
>
> Amount: GH₵ 500.00
> Method: MTN Mobile Money
> Number: 024-XXX-XXXX
>
> Processing time: 1-24 hours. You'll be notified when it's complete.

---

### 4.8 Delivery Zones Flow

When the seller taps "Delivery Zones":

---

**FLOW: Delivery Zones**

**Screen 1 — "Your Delivery Zones"**

| Element | Type | Details |
|---|---|---|
| Active Zones | List with toggles | Each zone shows: Zone name (e.g. "SRC — University of Cape Coast"), Delivery fee (e.g. "GH₵ 12.00"), Active/Inactive toggle |
| Add Zone Button | Navigation button | **[+ Add New Zone]** → navigates to Screen 2 |

---

**Screen 2 — "Add Delivery Zone"**

| Field | Type | Details |
|---|---|---|
| Available Zones | Multi-select checkboxes | Shows all zones from the ALL_ZONES list that the seller hasn't already added: SRC, Superannuation, PSI, ATL, Casford, Valco, KNH, Oguaa, Adehyie. Green checkmarks on selected items. |
| Delivery Fee (GH₵) | Number input | Required. The fee to charge for delivery to the selected zone(s). |

At the bottom: **[Save Zones ✓]**

Flow closes. Backend updates the seller's delivery zones. Confirmation sent in chat.

---

### 4.9 Store Profile Flow

When the seller taps "Store Profile":

---

**FLOW: Store Profile**

**Screen 1 — "Edit Store Profile"**

| Field | Type | Details |
|---|---|---|
| Restaurant Name | Text input | Pre-filled. Editable. |
| Description | Text area | Pre-filled. Editable. |
| Opening Hours | Text input | Placeholder: "e.g. 7:00 AM - 9:00 PM" |
| Store Status | Toggle/Radio | Open for Orders / Closed |

At the bottom: **[Save Changes ✓]**

---

### 4.10 Seller Help Flow

Similar to Buyer Help — shows FAQs relevant to sellers (how to manage products, how payments work, how to handle orders, etc.) and contact support buttons.

---

## 5. CONVERSATION FLOW SUMMARY — VISUAL FLOWCHART (Descriptive)

Here is the complete flow described as a step-by-step decision tree:

```
USER SENDS FIRST MESSAGE TO ZAN CHOP WHATSAPP NUMBER
│
├── Is user registered?
│   │
│   ├── NO → Send Welcome Message
│   │         │
│   │         ├── User taps [Buy Food]
│   │         │   └── Launch BUYER REGISTRATION FLOW
│   │         │       ├── Screen 1: Name + Phone
│   │         │       └── Screen 2: Area + Address + Landmark
│   │         │           └── Submit → Create buyer record
│   │         │               └── Send Buyer Main Menu
│   │         │
│   │         └── User taps [Sell Food]
│   │             └── Launch SELLER REGISTRATION FLOW
│   │                 ├── Screen 1: Name + Phone + Restaurant Name
│   │                 └── Screen 2: Category + Location + Description
│   │                     └── Submit → Create seller record (pending)
│   │                         └── Send "Application Submitted" + Preview option
│   │
│   ├── YES, BUYER → Send Buyer Main Menu
│   │   │
│   │   ├── [Order Food]
│   │   │   └── Launch FOOD ORDERING FLOW
│   │   │       ├── Screen 1: Search / Browse Restaurants
│   │   │       ├── Screen 2: Restaurant Menu (select items)
│   │   │       ├── Screen 3: Customise Order (portion, spice, add-ons, qty, notes)
│   │   │       ├── Screen 4: Cart (review, adjust, delivery method, address)
│   │   │       └── Screen 5: Checkout (summary, payment method, PAY button)
│   │   │           └── Submit → Create order, process payment
│   │   │               ├── Send buyer: Order Confirmation
│   │   │               ├── Send seller: New Order Alert (with Accept/Reject buttons)
│   │   │               └── Start 30-second timeout timer
│   │   │
│   │   ├── [My Orders]
│   │   │   └── Launch ORDER TRACKING FLOW
│   │   │       ├── Screen 1: Order List (filterable by status)
│   │   │       └── Screen 2: Order Detail (with Cancel option if Pending)
│   │   │
│   │   └── [Help]
│   │       └── Launch BUYER HELP FLOW
│   │           └── Screen 1: FAQs + Contact Support
│   │
│   └── YES, SELLER → Send Seller Main Menu
│       │
│       ├── [My Products]
│       │   └── Launch PRODUCT MANAGEMENT FLOW
│       │       ├── Screen 1: Product List + Add New
│       │       └── Screen 2: Add/Edit Product Form
│       │
│       ├── [Orders]
│       │   └── Launch SELLER ORDERS FLOW
│       │       └── Screen 1: Order List (filterable)
│       │           └── Tap order → Details + Update Status
│       │
│       ├── [Wallet]
│       │   └── Launch WALLET FLOW
│       │       └── Screen 1: Balance + Withdraw Form
│       │
│       ├── [Delivery Zones]
│       │   └── Launch DELIVERY ZONES FLOW
│       │       ├── Screen 1: Active Zones (with toggles)
│       │       └── Screen 2: Add New Zone (multi-select + fee)
│       │
│       ├── [Store Profile]
│       │   └── Launch STORE PROFILE FLOW
│       │       └── Screen 1: Edit Name, Description, Hours, Status
│       │
│       └── [Help]
│           └── Launch SELLER HELP FLOW
│               └── Screen 1: Seller FAQs + Support Contact
│
│
═══════════════════════════════════════════════════════
ASYNCHRONOUS / PUSH NOTIFICATIONS (Backend → WhatsApp)
═══════════════════════════════════════════════════════
│
├── NEW ORDER → Seller receives alert with Accept/Reject buttons
│   ├── 30s timeout → Send timeout warning to seller
│   ├── Seller Accepts → Buyer notified "Preparing"
│   ├── Seller Rejects → Buyer notified "Cancelled" + Refund
│   └── Seller updates status → Buyer notified at each stage
│
├── STATUS CHANGES → Buyer receives notification
│   ├── Pending → Preparing: "Your order is being prepared! 👨‍🍳"
│   ├── Preparing → On the Way: "Your food is on its way! 🚗"
│   ├── On the Way → Delivered: "Delivered! Enjoy! ✅"
│   └── Any → Cancelled: "Order cancelled. Refund processing. ❌"
│
└── PAYMENT EVENTS → Buyer receives confirmation
    ├── Payment successful: "Payment of GH₵ XX received ✅"
    ├── Payment failed: "Payment failed. Please try again ❌"
    └── Refund processed: "Refund of GH₵ XX completed ✅"
```

---

## 6. WHY WHATSAPP FLOWS INSTEAD OF TRADITIONAL CHATBOT MESSAGES

The traditional chatbot approach would look like this for just ordering one item:

> **Bot:** What would you like to do? [Buy Food] [Sell Food]
> **User:** *taps Buy Food*
> **Bot:** Great! Please enter your name.
> **User:** Kwame Mensah
> **Bot:** Thanks Kwame! Now enter your phone number.
> **User:** 0241234567
> **Bot:** Select your delivery area: [SRC] [Superannuation] [PSI]...
> **User:** *taps SRC*
> **Bot:** Enter your address.
> **User:** Hostel B Room 204
> **Bot:** Any landmark?
> **User:** Near the blue gate
> **Bot:** Registration complete! Here are restaurants near you: [Aunty Ama's] [Chop Bar Plus]...
> **User:** *taps Aunty Ama's*
> **Bot:** Here's the menu: [Jollof Rice - GH₵25] [Fried Rice - GH₵30]...
> **User:** *taps Jollof Rice*
> **Bot:** Select portion: [Regular] [Large] [Extra Large]
> **User:** *taps Large*
> **Bot:** Select spice level: [Mild] [Medium] [Hot] [Extra Hot]
> **User:** *taps Hot*
> **Bot:** Any add-ons? [Extra Meat +GH₵8] [Egg +GH₵3] [Plantain +GH₵5] [None]
> **User:** *taps Extra Meat*
> **Bot:** How many? [1] [2] [3] [4] [5]
> **User:** *taps 1*
> **Bot:** Special instructions?
> **User:** No onions
> ...and so on through cart, delivery, payment...

That's **20+ messages** just to place one order. The conversation becomes impossibly long and cluttered. If the user wants to scroll back to check something, they're lost in a wall of messages.

**With WhatsApp Flows**, the same entire process happens in **one Flow with 5 screens**, producing only **3 messages in the chat**: the initial CTA button, the order confirmation, and status updates. The chat stays clean, professional, and easy to reference.

---

## 7. BACKEND WEBHOOK ARCHITECTURE

The backend needs to handle these webhook events from WhatsApp:

| Event Type | Description | Action |
|---|---|---|
| `messages.text` | User sends a text message | Parse intent (greet, menu, help) → send appropriate response |
| `messages.interactive.button_reply` | User taps a reply button | Route based on button ID (accept_order, reject_order, etc.) |
| `messages.interactive.nfm_reply` | User completes a Flow | Parse Flow response payload → extract screen data → process (register, create order, update product, etc.) |
| `message_status` | Delivery/read receipts | Track message delivery status |

The backend sends messages using:
| API Call | Purpose |
|---|---|
| `POST /messages` (text) | Simple text notifications |
| `POST /messages` (interactive - buttons) | Messages with reply buttons (Accept/Reject, Main Menu) |
| `POST /messages` (interactive - flow) | Messages with Flow CTA buttons that launch Flows |
| `POST /messages` (template) | Pre-approved notification templates for proactive messages (order updates, payment confirmations) |

---

## 8. DATA FLOW FOR A SINGLE ORDER — END TO END

Here is the complete data journey for one food order:

1. **Buyer taps [Order Food]** → Backend sends Flow CTA message → Buyer taps the button → Flow opens

2. **Buyer completes Flow screens 1-5** → Selects restaurant, items, customisations, delivery, payment → Taps "Pay" → Flow closes → WhatsApp sends `nfm_reply` webhook to backend with the full response payload JSON

3. **Backend receives webhook** → Parses payload → Extracts: restaurant_id, items array (each with name, portion, spice, addons, qty, price), delivery_method, delivery_address, payment_method, momo_number

4. **Backend creates order** → Generates order_id (#8472), sets status="pending", calculates totals, stores in database

5. **Backend initiates payment** → Calls MTN MoMo API / Vodafone Cash API / Card gateway → Sends payment prompt to buyer's phone

6. **Backend sends buyer confirmation** → WhatsApp message with order summary and [Track Order] button

7. **Backend sends seller notification** → WhatsApp interactive message with order details and [Accept] [Reject] buttons

8. **Backend starts 30s timer** → If no seller response in 30 seconds, sends timeout alert to seller

9. **Seller taps [Accept]** → Backend receives `button_reply` webhook → Updates order status to "preparing" → Sends buyer notification → Sends seller confirmation with [Update Status] button

10. **Seller taps [Update Status]** → Backend sends Flow CTA → Seller opens Status Update Flow → Selects "On the Way" → Flow closes → Backend updates status → Buyer notified

11. **Seller updates to "Delivered"** → Backend marks order complete → Buyer receives delivery notification with [Rate Order] option → Seller's wallet balance increased

---

## 9. FLOW ID REFERENCE TABLE

Each WhatsApp Flow needs to be created in the Meta Business Manager and has a unique Flow ID. Here's the mapping:

| Flow Name | Screens | Triggered By | Used By |
|---|---|---|---|
| `buyer_registration` | 2 screens | "Buy Food" button (new users) | Buyer |
| `food_ordering` | 5 screens | "Order Food" button | Buyer |
| `order_tracking_buyer` | 2 screens | "My Orders" button | Buyer |
| `buyer_help` | 1 screen | "Help" button | Buyer |
| `seller_registration` | 2 screens | "Sell Food" button (new users) | Seller |
| `product_management` | 2 screens | "My Products" button | Seller |
| `seller_orders` | 1-2 screens | "Orders" button | Seller |
| `status_update` | 1 screen | "Update Status" button | Seller |
| `wallet` | 1 screen | "Wallet" button | Seller |
| `delivery_zones` | 2 screens | "Delivery Zones" button | Seller |
| `store_profile` | 1 screen | "Store Profile" button | Seller |
| `seller_help` | 1 screen | "Help" button | Seller |

---

## 10. CURRENCY, REGION & PAYMENT SPECIFICS

- **All prices** are displayed in **Ghanaian Cedi (GH₵)**
- **Delivery fee** is a fixed **GH₵ 12.00** (configurable per zone in future)
- **Target region**: Cape Coast, Ghana — specifically UCC campus and surrounding areas
- **Delivery zones**: SRC, Superannuation, PSI, ATL, Casford, Valco, KNH, Oguaa, Adehyie
- **Payment methods**: MTN Mobile Money (primary), Vodafone Cash, Bank Card (Visa/Mastercard)
- **Payment flow**: For MoMo/Vodafone, the backend triggers a payment prompt to the buyer's phone. The buyer approves on their phone. The payment gateway sends a callback to the backend confirming success/failure. The backend then updates the order and notifies both parties.

---

This architecture keeps the WhatsApp conversation thread clean and minimal while delivering a rich, app-like food ordering experience entirely within WhatsApp, using Flows for structured input and interactive messages for quick actions and notifications.