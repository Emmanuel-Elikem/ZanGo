import os
import re

APP_PY = "/home/demigod/PROJECTS/ZanGo/app.py"

def refactor_flow():
    with open(APP_PY, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update handle_* signatures
    content = content.replace(
        "def handle_admin_flow(phone, text, session):", 
        "def handle_admin_flow(phone, text, session, is_interactive=False, metadata=None):"
    )
    content = content.replace(
        "def handle_onboarding(phone, text, session):", 
        "def handle_onboarding(phone, text, session, is_interactive=False, metadata=None):"
    )
    content = content.replace(
        "def handle_seller_flow(phone, text, session, user):", 
        "def handle_seller_flow(phone, text, session, user, is_interactive=False, metadata=None):"
    )
    content = content.replace(
        "def handle_buyer_flow(phone, text, session, user):", 
        "def handle_buyer_flow(phone, text, session, user, is_interactive=False, metadata=None):"
    )

    # 2. Update process_message entry routing
    old_routing = """        # Admin always uses the admin flow first
        if is_admin:
            handle_admin_flow(from_phone, msg_body, session)
        # New user OR in onboarding flow
        elif not user or session["state"].startswith("onboarding_"):
            handle_onboarding(from_phone, msg_body, session)
        # Existing user - route based on role
        elif user[USER_ROLE] == 'seller':
            handle_seller_flow(from_phone, msg_body, session, user)
        elif user[USER_ROLE] == 'buyer':
            handle_buyer_flow(from_phone, msg_body, session, user)
        else:
            send_text(from_phone, "Welcome! Type 'menu' to see your options.")"""

    new_routing = """        # Admin always uses the admin flow first
        if is_admin:
            handle_admin_flow(from_phone, msg_body, session, is_interactive, metadata)
        # New user OR in onboarding flow
        elif not user or session["state"] in ("new_user", "start") or session["state"].startswith("buyer_onboarding_") or session["state"].startswith("seller_onboarding_") or session["state"].startswith("onboarding_"):
            handle_onboarding(from_phone, msg_body, session, is_interactive, metadata)
        # Existing user - route based on role
        elif user[USER_ROLE] == 'seller':
            handle_seller_flow(from_phone, msg_body, session, user, is_interactive, metadata)
        elif user[USER_ROLE] == 'buyer':
            handle_buyer_flow(from_phone, msg_body, session, user, is_interactive, metadata)
        else:
            from whatsapp_cloud_helper import get_whatsapp_cloud
            get_whatsapp_cloud().send_whatsapp_message(from_phone, "Welcome! Type 'menu' to see your options.")"""
            
    content = content.replace(old_routing, new_routing)

    # 3. Completely rewrite handle_onboarding logic
    # Find the block of handle_onboarding to replace it
    pattern = re.compile(r"def handle_onboarding\(phone, text, session, is_interactive=False, metadata=None\):.*?(?=\ndef handle_seller_flow|\ndef \w)", re.DOTALL)
    
    new_handle_onboarding = """def handle_onboarding(phone, text, session, is_interactive=False, metadata=None):
    from whatsapp_cloud_helper import get_whatsapp_cloud
    cloud = get_whatsapp_cloud()
    
    state = session.get("state", "new_user")
    text = (text or "").strip()
    
    # Get interactive ID if available
    interactive_id = metadata.get("id") if is_interactive and metadata else None

    # Normalisation from legacy start -> new_user
    if state == "start":
        state = "new_user"

    if state == "new_user":
        msg = (
            "🍽️ *Welcome to Zan Chop!*\n"
            "Your favourite food, delivered fast across Cape Coast. UCC campus and beyond.\n"
            "What would you like to do?"
        )
        buttons = [
            {"id": "btn_buy_food", "title": "🛒 Buy Food"},
            {"id": "btn_sell_food", "title": "🏪 Sell Food"}
        ]
        cloud.send_interactive_buttons(phone, msg, buttons)
        session["state"] = "onboarding_role_selection"

    elif state == "onboarding_role_selection":
        if is_interactive and interactive_id == "btn_buy_food":
            cloud.send_whatsapp_message(phone, "Let's get your profile ready. What's your *full name*?")
            session["state"] = "buyer_onboarding_name"
        elif is_interactive and interactive_id == "btn_sell_food":
            cloud.send_whatsapp_message(phone, "Let's build your shop profile for admin approval.\\n\\nWhat is your *full name*?")
            session["state"] = "seller_onboarding_name"
        else:
            cloud.send_whatsapp_message(phone, "Please tap one of the buttons above to continue.")

    # ----------- BUYER ONBOARDING -----------
    elif state == "buyer_onboarding_name":
        session["data"]["buyer_name"] = text
        
        zones = []
        for i, zone in enumerate(UCC_ZONES.keys(), 1):
            preview = ", ".join(DELIVERY_ZONES.get(zone, {}).get("landmarks", [])[:2]) or "Popular campus area"
            zones.append({"id": f"zone_{i}", "title": zone, "description": truncate_text(preview, 72)})
        
        sections = [{"title": "Select Your Zone", "rows": zones}]
        cloud.send_interactive_list(
            phone, 
            f"✅ Great, {text}!\\n\\n📍 Which campus zone are you in?", 
            "Select Zone", 
            sections
        )
        session["state"] = "buyer_onboarding_zone"
        
    elif state == "buyer_onboarding_zone":
        if is_interactive and interactive_id and interactive_id.startswith("zone_"):
            # Extract zone index
            try:
                idx = int(interactive_id.split("_")[1]) - 1
                zone_name = list(UCC_ZONES.keys())[idx]
            except:
                zone_name = None
        else:
            zone_name = resolve_zone_choice(text)
            
        if zone_name:
            session["data"]["buyer_zone"] = zone_name
            cloud.send_whatsapp_message(phone, f"📍 *Zone: {zone_name}*\\n\\nAlmost done! Please enter your specific *address or landmark*:")
            session["state"] = "buyer_onboarding_address"
        else:
            cloud.send_whatsapp_message(phone, "Please select a valid zone from the list.")
            
    elif state == "buyer_onboarding_address":
        landmark = text
        buyer_name = session["data"].get("buyer_name")
        zone_name = session["data"].get("buyer_zone")
        
        # Create Buyer User
        update_user(phone, name=buyer_name, role="buyer", zone=zone_name, landmark=landmark)
        
        # Clear data and send to menu
        session["data"] = {}
        session["state"] = "buyer_menu"
        
        # Transition immediately to showing the buyer menu
        handle_buyer_flow(phone, "menu", session, get_user(normalize_phone(phone)))

    # ----------- SELLER ONBOARDING -----------
    elif state == "seller_onboarding_name":
        session["data"]["seller_name"] = text
        cloud.send_whatsapp_message(phone, "Great! What is your *restaurant/shop name*?")
        session["state"] = "seller_onboarding_shopname"
        
    elif state == "seller_onboarding_shopname":
        session["data"]["shop_name"] = text
        cloud.send_whatsapp_message(phone, "Can you provide a short *description* of what you sell? (e.g., 'Best waakye and jollof on campus!')")
        session["state"] = "seller_onboarding_details"
        
    elif state == "seller_onboarding_details":
        session["data"]["shop_description"] = text
        
        # We need a zone for the seller too
        zones = []
        for i, zone in enumerate(UCC_ZONES.keys(), 1):
            preview = ", ".join(DELIVERY_ZONES.get(zone, {}).get("landmarks", [])[:2]) or "Popular campus area"
            zones.append({"id": f"zone_{i}", "title": zone, "description": truncate_text(preview, 72)})
        
        sections = [{"title": "Select Shop Zone", "rows": zones}]
        cloud.send_interactive_list(
            phone, 
            "📍 Which campus zone is your shop located in?", 
            "Select Zone", 
            sections
        )
        session["state"] = "seller_onboarding_zone"

    elif state == "seller_onboarding_zone":
        if is_interactive and interactive_id and interactive_id.startswith("zone_"):
            try:
                idx = int(interactive_id.split("_")[1]) - 1
                zone_name = list(UCC_ZONES.keys())[idx]
            except:
                zone_name = None
        else:
            zone_name = resolve_zone_choice(text)
            
        if zone_name:
            session["data"]["shop_zone"] = zone_name
            cloud.send_whatsapp_message(phone, f"📍 *Zone: {zone_name}*\\n\\nPlease provide a specific *landmark or address* for your shop:")
            session["state"] = "seller_onboarding_landmark"
        else:
            cloud.send_whatsapp_message(phone, "Please select a valid zone from the list.")

    elif state == "seller_onboarding_landmark":
        session["data"]["shop_landmark"] = text
        
        # Save request and show pending
        data = session["data"]
        submit_seller_request_direct(
            phone=phone,
            seller_name=data.get("seller_name"),
            shop_name=data.get("shop_name"),
            shop_description=data.get("shop_description"),
            zone=data.get("shop_zone"),
            landmark=data.get("shop_landmark")
        )
        
        cloud.send_whatsapp_message(phone, "✅ Your application has been submitted successfully! Check back soon. The admin will review your profile.")
        session["state"] = "seller_pending"

"""

    # We need to replace the old handle_onboarding with the new one.
    # We will use Regex to find everything from def handle_onboarding... to the next def.
    # Because handle_onboarding can be quite long.
    import re
    # To be safe, let's find the exact string boundaries.
    start_idx = content.find("def handle_onboarding(phone, text, session, is_interactive=False, metadata=None):")
    if start_idx != -1:
        end_idx = content.find("def submit_seller_request_direct", start_idx)
        if end_idx == -1:
            end_idx = content.find("def handle_admin", start_idx)
        if end_idx == -1:
            end_idx = content.find("def handle_seller_flow", start_idx)

        if end_idx != -1:
            # We want to keep everything from end_idx onwards
            content = content[:start_idx] + new_handle_onboarding + "\n\n" + content[end_idx:]

    # Since submit_seller_request_direct might not exist, we'll create it.
    if "def submit_seller_request_direct" not in content:
        create_req_func = """def submit_seller_request_direct(phone, seller_name, shop_name, shop_description, zone, landmark):
    normalized_phone = normalize_phone(phone)
    import string
    import random
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(\"\"\"
        INSERT INTO seller_requests 
        (seller_phone, seller_name, shop_name, shop_description, zone, landmark, code, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
    \"\"\", (normalized_phone, seller_name, shop_name, shop_description, zone, landmark, code))
    conn.commit()
    conn.close()
"""
        # Insert before handle_seller_flow
        idx = content.find("def handle_seller_flow")
        content = content[:idx] + create_req_func + "\n" + content[idx:]

    with open(APP_PY, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    refactor_flow()
