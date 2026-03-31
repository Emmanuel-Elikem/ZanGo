import os

APP_PY = "/home/demigod/PROJECTS/ZanGo/app.py"

def refactor():
    with open(APP_PY, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Imports and DB Connection
    import_block = """import psycopg2
from psycopg2.extras import RealDictCursor"""
    content = content.replace("import sqlite3", import_block)
    
    content = content.replace("sqlite3.connect(DB_FILE)", "get_db_connection()")
    
    db_conn_def = """DB_FILE = os.path.join(BASE_DIR, "prim_store.db")

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")
    conn = psycopg2.connect(DATABASE_URL)
    return conn"""
    content = content.replace('DB_FILE = os.path.join(BASE_DIR, "prim_store.db")', db_conn_def)

    # 2. Schema conversions
    content = content.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    content = content.replace('c.execute(f"PRAGMA table_info({table_name})")', 'c.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table_name,))')
    content = content.replace('return {row[1] for row in c.fetchall()}', 'return {row[0] for row in c.fetchall()}')
    
    # INSERT OR REPLACE / IGNORE -> ON CONFLICT
    content = content.replace("INSERT OR REPLACE INTO seller_invites", "INSERT INTO seller_invites")
    content = content.replace(
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', NULL)",
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'active', NULL) ON CONFLICT (code) DO UPDATE SET seller_phone = excluded.seller_phone, seller_name = excluded.seller_name, shop_name = excluded.shop_name, shop_description = excluded.shop_description, shop_image_url = excluded.shop_image_url, zone = excluded.zone, landmark = excluded.landmark, status = 'active', claimed_at = NULL"
    )

    content = content.replace("INSERT OR IGNORE INTO users", "INSERT INTO users")
    content = content.replace(
        ") VALUES (?, ?, ?, ?, ?)",
        ") VALUES (%s, %s, %s, %s, %s) ON CONFLICT (phone) DO NOTHING"
    )

    # 3. Handle specific SQL updates with ?
    replacements = [
        ("WHERE seller_phone = ? AND stock > 0", "WHERE seller_phone = %s AND stock > 0"),
        ("WHERE phone = ?", "WHERE phone = %s"),
        ("WHERE payment_ref = ?", "WHERE payment_ref = %s"),
        ("WHERE code = ?", "WHERE code = %s"),
        ("UPPER(code) = UPPER(?)", "UPPER(code) = UPPER(%s)"),
        ("VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', NULL, NULL)", "VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', NULL, NULL)"),
        ("LIMIT ?", "LIMIT %s"),
        ("WHERE id = ?", "WHERE id = %s"),
        ("SET status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP", "SET status = %s, reviewed_by = %s, reviewed_at = CURRENT_TIMESTAMP"),
        ("WHERE id = ? AND seller_phone = ?", "WHERE id = %s AND seller_phone = %s"),
        ("updates.append(f\"{key} = ?\")", "updates.append(f\"{key} = %s\")"),
        ("WHERE seller_phone = ?", "WHERE seller_phone = %s"),
        ("phone = ? OR phone = ? OR phone = ?", "phone = %s OR phone = %s OR phone = %s"),
        ("COALESCE(?, name)", "COALESCE(%s, name)"),
        ("COALESCE(?, role)", "COALESCE(%s, role)"),
        ("COALESCE(?, zone)", "COALESCE(%s, zone)"),
        ("COALESCE(?, landmark)", "COALESCE(%s, landmark)"),
        ("SET name = ? WHERE phone = ?", "SET name = %s WHERE phone = %s"),
        ("SET role = ? WHERE phone = ?", "SET role = %s WHERE phone = %s"),
        ("SET zone = ? WHERE phone = ?", "SET zone = %s WHERE phone = %s"),
        ("SET landmark = ? WHERE phone = ?", "SET landmark = %s WHERE phone = %s"),
        ("WHERE p.id = ?", "WHERE p.id = %s"),
        ("LIKE ?", "LIKE %s"),
        ("WHERE o.buyer_phone = ?", "WHERE o.buyer_phone = %s"),
        ("WHERE o.id = ? AND o.buyer_phone = ?", "WHERE o.id = %s AND o.buyer_phone = %s"),
        ("WHERE oi.order_id = ?", "WHERE oi.order_id = %s"),
        ("[\"?\"] * len(insert_columns)", "[\"%s\"] * len(insert_columns)"),
        ('VALUES (?, ?, ?, ?)', 'VALUES (%s, %s, %s, %s)'),
        ('VALUES (?, ?, ?, ?, ?, ?)', 'VALUES (%s, %s, %s, %s, %s, %s)'), # potential other inserts
        ('shop_name = ?', 'shop_name = %s'),
        ('shop_description = ?', 'shop_description = %s'),
        ('shop_image_url = ?', 'shop_image_url = %s'),
        ('zone = ?', 'zone = %s'),
        ('landmark = ?', 'landmark = %s'),
    ]
    for old, new in replacements:
        content = content.replace(old, new)
        
    # sqlite3 exceptions
    content = content.replace("sqlite3.OperationalError", "psycopg2.OperationalError")
    content = content.replace("sqlite3.IntegrityError", "psycopg2.IntegrityError")

    # 4. Handle RETURNING id instead of lastrowid
    # order_id
    content = content.replace(') VALUES ({placeholders})",', ') VALUES ({placeholders}) RETURNING id",')
    content = content.replace('order_id = c.lastrowid', 'order_id = c.fetchone()[0]')

    # Also check if there's any other lastrowid missed:
    # seller_requests or products might have it
    content = content.replace('product_id = c.lastrowid', 'product_id = c.fetchone()[0]')
    content = content.replace(") VALUES (%s, %s, %s, %s, %s, %s)", ") VALUES (%s, %s, %s, %s, %s, %s) RETURNING id") 

    with open(APP_PY, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    refactor()
