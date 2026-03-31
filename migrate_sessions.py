import os
import re

APP_PY = "/home/demigod/PROJECTS/ZanGo/app.py"

def refactor_sessions():
    with open(APP_PY, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add json import if not there
    if "import json" not in content:
        content = content.replace("import os", "import os\nimport json")

    # 2. Add sessions table to init_db()
    sessions_table_sql = '''        c.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                phone VARCHAR(20) PRIMARY KEY,
                state VARCHAR(50) NOT NULL,
                data JSONB DEFAULT '{}'::jsonb,
                cart JSONB DEFAULT '[]'::jsonb,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)'''
    if "CREATE TABLE IF NOT EXISTS sessions" not in content:
        content = content.replace("        conn.commit()", sessions_table_sql + "\n        conn.commit()", 1)

    # 3. Add get_session and save_session functions
    get_save_session_code = """
def get_session(phone):
    normalized = normalize_phone(phone)
    conn = get_db_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT * FROM sessions WHERE phone = %s", (normalized,))
    row = c.fetchone()
    conn.close()
    if row:
        session = {"state": row["state"], "cart": row["cart"] or []}
        session.update(row["data"] or {})
        return session
    return {"state": "new_user", "data": {}, "cart": []}

def save_session(phone, session):
    normalized = normalize_phone(phone)
    state = session.get("state", "new_user")
    cart = session.get("cart", [])
    
    # Extract data (everything except state and cart)
    session_data = {k: v for k, v in session.items() if k not in ("state", "cart")}
    
    data_json = json.dumps(session_data)
    cart_json = json.dumps(cart)
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(\"\"\"
        INSERT INTO sessions (phone, state, data, cart, updated_at)
        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (phone) DO UPDATE 
        SET state = EXCLUDED.state,
            data = EXCLUDED.data,
            cart = EXCLUDED.cart,
            updated_at = EXCLUDED.updated_at
    \"\"\", (normalized, state, data_json, cart_json))
    conn.commit()
    conn.close()

def reset_user_session(phone, state="idle", data=None, keep_cart=False):
    normalized_phone = normalize_phone(phone)
    if data is None:
        data = {}
    
    session_data = get_session(normalized_phone) if keep_cart else {"cart": []}
    new_session = {
        "state": state,
        "data": data,
        "cart": session_data.get("cart", [])
    }
    save_session(normalized_phone, new_session)
"""
    # Replace the old reset_user_session and add get_session / save_session
    old_reset = """def reset_user_session(phone, state="idle", data=None, keep_cart=False):
    normalized_phone = normalize_phone(phone)
    sessions = load_json(SESSIONS_FILE, {})
    session_record = {"state": state, "data": data or {}}
    if keep_cart and normalized_phone in sessions and isinstance(sessions[normalized_phone].get("cart"), list):
        session_record["cart"] = sessions[normalized_phone]["cart"]
    sessions[normalized_phone] = session_record
    save_json(SESSIONS_FILE, sessions)"""
    
    if old_reset in content:
        content = content.replace(old_reset, get_save_session_code)
        
    # In process_message:
    old_process_sess = """    sessions = load_json(SESSIONS_FILE, {})
    session_key = normalized_phone
    if session_key not in sessions:
        sessions[session_key] = {"state": "start", "data": {}}
    session = sessions[session_key]"""
    content = content.replace(old_process_sess, "    session = get_session(from_phone)")
    
    # In handle_incoming_media (wait, grep showed normalized_phone is used in handle_incoming_media logic)
    # The variable is phone or normalized_phone?
    # Actually, in generic usage, I'll just use save_session(from_phone if 'from_phone' in locals() else normalized_phone if 'normalized_phone' in locals() else phone, session)
    # Let's cleanly replace the specific blocks:
    old_media_sess = """        sessions = load_json(SESSIONS_FILE, {})
        if normalized_phone in sessions:
            sessions[normalized_phone]["pending_image"] = media_url
            save_json(SESSIONS_FILE, sessions)"""
    new_media_sess = """        session = get_session(normalized_phone)
        session["pending_image"] = media_url
        save_session(normalized_phone, session)"""
    if old_media_sess in content:
        content = content.replace(old_media_sess, new_media_sess)
    
    # In process_image_message
    old_img_sess = """            sessions = load_json(SESSIONS_FILE, {})
            if normalized_phone not in sessions:
                sessions[normalized_phone] = {"state": "start", "data": {}}
            session = sessions[normalized_phone]"""
    if old_img_sess in content:
        content = content.replace(old_img_sess, "            session = get_session(normalized_phone)")

    # Replace save_json(SESSIONS_FILE, sessions) EVERYWHERE else by checking the context
    # Usually it's in process_message at the end
    content = content.replace("save_json(SESSIONS_FILE, sessions)", "save_session(from_phone, session)")
    
    with open(APP_PY, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    refactor_sessions()
