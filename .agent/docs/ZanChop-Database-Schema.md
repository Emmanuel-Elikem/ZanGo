# ZanChop — Database Schema

> **Read this before any data model, query, or migration work.**

---

## Current State vs Target

| Aspect         | Current (SQLite)                    | Target (PostgreSQL)                         |
| -------------- | ----------------------------------- | ------------------------------------------- |
| Connection     | `sqlite3.connect("prim_store.db")`  | `psycopg2` via `DATABASE_URL` env var       |
| Auto-increment | `INTEGER PRIMARY KEY AUTOINCREMENT` | `SERIAL PRIMARY KEY` or `BIGSERIAL`         |
| Schema inspect | `PRAGMA table_info(table_name)`     | `information_schema.columns`                |
| Booleans       | `INTEGER (0/1)`                     | `BOOLEAN`                                   |
| Timestamps     | `TEXT` (ISO string)                 | `TIMESTAMP WITH TIME ZONE`                  |
| Concurrent     | NOT safe                            | Safe (connection pooling required)           |

---

## Schema Tables

### `users`
Stores all users — buyers and sellers share this table.

| Column         | Type          | Notes                                          |
| -------------- | ------------- | ---------------------------------------------- |
| `id`           | SERIAL PK     |                                                |
| `phone`        | TEXT UNIQUE   | Normalized (no `+`). Index this.               |
| `name`         | TEXT          | Full name as entered                           |
| `role`         | TEXT          | `buyer`, `seller`, `admin`                     |
| `created_at`   | TIMESTAMP     | Default: NOW()                                 |
| `is_active`    | BOOLEAN       | Default: TRUE                                  |

---

### `buyers`
Extended profile for users with role=`buyer`.

| Column           | Type      | Notes                                     |
| ---------------- | --------- | ----------------------------------------- |
| `id`             | SERIAL PK |                                           |
| `user_id`        | INT FK    | → `users.id`                              |
| `delivery_zone`  | TEXT      | One of the 7 zone names                   |
| `address`        | TEXT      | Street / hostel / room                    |
| `landmark`       | TEXT      | Optional. Nearby reference point          |
| `updated_at`     | TIMESTAMP |                                           |

---

### `sellers`
Extended profile for users with role=`seller`.

| Column           | Type      | Notes                                      |
| ---------------- | --------- | ------------------------------------------ |
| `id`             | SERIAL PK |                                            |
| `user_id`        | INT FK    | → `users.id`                               |
| `shop_name`      | TEXT      | Restaurant/vendor name                     |
| `description`    | TEXT      | Short description                          |
| `food_category`  | TEXT      | e.g. "Local Dishes", "Grills & BBQ"        |
| `location`       | TEXT      | Physical location text                     |
| `logo_url`       | TEXT      | URL to shop logo/image                     |
| `status`         | TEXT      | `pending_approval`, `active`, `suspended`  |
| `is_open`        | BOOLEAN   | Seller-controlled open/closed toggle       |
| `wallet_balance` | DECIMAL   | GHS. Default: 0.00. Escrow release target. |
| `created_at`     | TIMESTAMP |                                            |
| `approved_at`    | TIMESTAMP | Set when admin approves                    |

---

### `products`
Food items listed by sellers.

| Column         | Type       | Notes                                     |
| -------------- | ---------- | ----------------------------------------- |
| `id`           | SERIAL PK  |                                           |
| `seller_id`    | INT FK     | → `sellers.id`                            |
| `name`         | TEXT       | e.g. "Jollof Rice Special"               |
| `description`  | TEXT       | Short dish description                    |
| `price`        | DECIMAL    | GHS                                       |
| `category`     | TEXT       | e.g. "Rice Dishes", "Soups", "Grills"    |
| `image_url`    | TEXT       | URL to product image                      |
| `addons`       | TEXT       | Comma-separated add-on strings            |
| `is_available` | BOOLEAN    | Default: TRUE. Seller can toggle off.     |
| `created_at`   | TIMESTAMP  |                                           |

---

### `delivery_zones` (seller-product mapping)
Which zones a seller delivers to and their fee per zone.

| Column        | Type       | Notes                                     |
| ------------- | ---------- | ----------------------------------------- |
| `id`          | SERIAL PK  |                                           |
| `seller_id`   | INT FK     | → `sellers.id`                            |
| `zone_name`   | TEXT       | One of the 7 predefined zone names        |
| `delivery_fee`| DECIMAL    | GHS. Default: 0.00 at MVP.               |
| `is_active`   | BOOLEAN    | Default: TRUE                             |

---

### `orders`
Core order records.

| Column              | Type       | Notes                                                  |
| ------------------- | ---------- | ------------------------------------------------------ |
| `id`                | SERIAL PK  |                                                        |
| `order_ref`         | TEXT UNIQUE| Human-readable e.g. "#8472". Generated on create.     |
| `buyer_id`          | INT FK     | → `buyers.id`                                          |
| `seller_id`         | INT FK     | → `sellers.id`                                         |
| `status`            | TEXT       | See order lifecycle states below                       |
| `delivery_method`   | TEXT       | `delivery` or `pickup`                                 |
| `delivery_zone`     | TEXT       | Buyer's delivery zone name                             |
| `delivery_address`  | TEXT       | Buyer's address string                                 |
| `delivery_landmark` | TEXT       | Optional landmark                                      |
| `delivery_fee`      | DECIMAL    | GHS. 0.00 at MVP.                                     |
| `subtotal`          | DECIMAL    | GHS. Sum of line items.                               |
| `total`             | DECIMAL    | GHS. subtotal + delivery_fee                          |
| `payment_method`    | TEXT       | `mtn_momo`, `vodafone_cash`, `card`                   |
| `payment_ref`       | TEXT       | Paystack payment reference                             |
| `payment_status`    | TEXT       | `pending`, `paid`, `refunded`, `failed`               |
| `confirmation_code` | TEXT       | OTP for delivery confirmation (4–6 digits)            |
| `special_note`      | TEXT       | Buyer's free-text instructions                         |
| `created_at`        | TIMESTAMP  |                                                        |
| `accepted_at`       | TIMESTAMP  |                                                        |
| `delivered_at`      | TIMESTAMP  |                                                        |

**Order status values:** `awaiting_payment`, `paid`, `accepted`, `preparing`, `on_the_way`, `delivered`, `cancelled`

---

### `order_items`
Line items for each order.

| Column          | Type      | Notes                                         |
| --------------- | --------- | --------------------------------------------- |
| `id`            | SERIAL PK |                                               |
| `order_id`      | INT FK    | → `orders.id`                                 |
| `product_id`    | INT FK    | → `products.id`                               |
| `product_name`  | TEXT      | Snapshot of name at order time                |
| `unit_price`    | DECIMAL   | Snapshot of price at order time               |
| `quantity`      | INT       | Default: 1                                    |
| `portion_size`  | TEXT      | `regular`, `large`, `extra_large`             |
| `spice_level`   | TEXT      | `mild`, `medium`, `hot`, `extra_hot`          |
| `addons`        | TEXT      | Comma-separated selected add-ons              |
| `addons_price`  | DECIMAL   | Extra charge for selected add-ons             |
| `line_total`    | DECIMAL   | (unit_price + addons_price) × quantity        |

---

### `sessions`
Replaces `sessions.json`. One row per active user conversation.

| Column       | Type      | Notes                                           |
| ------------ | --------- | ----------------------------------------------- |
| `id`         | SERIAL PK |                                                 |
| `phone`      | TEXT UK   | Normalized phone number. One row per user.      |
| `state`      | TEXT      | Current conversation state                      |
| `data`       | JSONB     | Scratchpad for in-progress flows (cart, etc.)   |
| `cart`       | JSONB     | Active cart items array                         |
| `updated_at` | TIMESTAMP | Used for session expiry logic                   |

> **Why JSONB for `data` and `cart`?**
> The scratchpad data is highly variable (depends on state). JSONB allows flexible storage without adding columns for every possible state's data. It's indexed and queryable in PostgreSQL.

---

## Key Indexes (Must Create)

```sql
CREATE UNIQUE INDEX idx_users_phone ON users(phone);
CREATE UNIQUE INDEX idx_sessions_phone ON sessions(phone);
CREATE INDEX idx_orders_buyer_id ON orders(buyer_id);
CREATE INDEX idx_orders_seller_id ON orders(seller_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_products_seller_id ON products(seller_id);
```

---

## Migration Checklist (SQLite → PostgreSQL)

- [ ] Add `psycopg2-binary` to `requirements.txt`
- [ ] Create a `get_db_connection()` helper that uses `DATABASE_URL` env var
- [ ] Replace all `sqlite3.connect(DB_FILE)` calls with the helper
- [ ] Replace `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY`
- [ ] Replace `PRAGMA table_info(...)` → `information_schema.columns`
- [ ] Replace `?` placeholders → `%s` (psycopg2 uses %s)
- [ ] Replace `0/1` integers for booleans → `TRUE/FALSE`
- [ ] Create `sessions` table to replace `sessions.json`
- [ ] Run `init_db()` against PostgreSQL to create schema
- [ ] Verify all queries handle `None` vs `NULL` correctly
- [ ] Set `DATABASE_URL` in Railway Variables
