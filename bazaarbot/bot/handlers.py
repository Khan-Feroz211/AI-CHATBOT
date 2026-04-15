"""Business logic handlers — Pakistani market focused."""
from datetime import datetime, date, timedelta
from bazaarbot import database as db
from bazaarbot.bot.menu import get_main_menu, get_payment_menu


# ── Stock ────────────────────────────────────────────────────────────────

def handle_stock(tenant_slug: str, phone: str) -> str:
    items = db.get_inventory(tenant_slug)
    if not items:
        return (
            "📦 *Aapka Stock*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Abhi koi product nahi hai.\n\n"
            "Product add karne ke liye likhein:\n"
            "*add product [naam] [qty] [unit] [price]*\n"
            "Misaal: add product Atta 100 kg 65"
        )
    lines = ["📦 *Aapka Stock*", "━━━━━━━━━━━━━━━━━━"]
    for item in items[:15]:
        qty = item["quantity"]
        if qty == 0:
            icon, status = "❌", "(khatam)"
        elif qty <= item["reorder_level"]:
            icon, status = "⚠️", "(kam — reorder karein)"
        else:
            icon, status = "✅", ""
        lines.append(
            f"{icon} {item['product_name']} — {qty} {item['unit']} "
            f"@ ₨{item['sell_price']:,.0f} {status}"
        )
    low = db.get_low_stock(tenant_slug)
    if low:
        lines.append(f"\n⚠️ {len(low)} item(s) ka stock kam hai!")
    lines += ["━━━━━━━━━━━━━━━━━━", "Stock update: *update [product] [qty]*"]
    return "\n".join(lines)


def handle_add_stock_prompt(tenant_slug: str, phone: str) -> str:
    db.set_session(tenant_slug, phone, "adding_stock")
    return (
        "➕ *Naya Product / Stock Add*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Niche format mein likhein:\n\n"
        "*add product [naam] [qty] [unit] [sell price]*\n\n"
        "Misaalein:\n"
        "• add product Atta 200 kg 70\n"
        "• add product Coca Cola 48 bottle 85\n"
        "• add product Surf Excel 100 box 380\n\n"
        "Waapis jaane ke liye *menu* likhein."
    )


def handle_add_stock(tenant_slug: str, phone: str, message: str) -> str:
    """Parse: add product <name> <qty> <unit> <sell_price>"""
    parts = message.strip().split()
    start = 2 if (
        len(parts) >= 2
        and parts[0].lower() == "add"
        and parts[1].lower() == "product"
    ) else 1
    remaining = parts[start:]
    if len(remaining) < 3:
        return (
            "Format: *add product [naam] [qty] [unit] [price]*\n"
            "Misaal: add product Atta 100 kg 65"
        )
    try:
        sell_price = float(remaining[-1].replace(",", ""))
        unit = remaining[-2]
        qty = int(remaining[-3].replace(",", ""))
        name = " ".join(remaining[:-3]).title()
        if not name:
            return "Product ka naam zaroor likhein."
        db.upsert_product(
            tenant_slug, name,
            quantity=qty, unit=unit,
            sell_price=sell_price,
            buy_price=round(sell_price * 0.8, 2),
        )
        db.clear_session(tenant_slug, phone)
        return (
            f"✅ *Stock Add Ho Gaya!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📦 Product: {name}\n"
            f"📊 Qty: {qty} {unit}\n"
            f"💰 Price: ₨{sell_price:,.0f}/{unit}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            "Stock check ke liye *1* ya *stock* likhein."
        )
    except (ValueError, IndexError):
        return "Format sahi nahi. Misaal: add product Atta 100 kg 65"


def handle_update_stock(tenant_slug: str, phone: str, message: str) -> str:
    """Parse: update <product> <qty>"""
    parts = message.strip().split()
    if len(parts) < 3:
        return (
            "Format: *update [product naam] [qty]*\n"
            "Misaal: update Atta 200"
        )
    try:
        qty = int(parts[-1])
        name = " ".join(parts[1:-1])
        existing = db.get_product(tenant_slug, name)
        if not existing:
            return (
                f"'{name}' inventory mein nahi mili.\n"
                "*stock* likhein sab products dekhne ke liye."
            )
        db.upsert_product(
            tenant_slug, existing["product_name"],
            category=existing["category"],
            quantity=qty,
            unit=existing["unit"],
            buy_price=existing["buy_price"],
            sell_price=existing["sell_price"],
            reorder_level=existing["reorder_level"],
            supplier=existing["supplier"],
        )
        return (
            f"✅ Stock update ho gaya!\n"
            f"{existing['product_name']}: {qty} {existing['unit']}"
        )
    except ValueError:
        return "Qty ek number hona chahiye. Misaal: update Atta 200"


def handle_sell(tenant_slug: str, phone: str, message: str) -> str:
    """Parse: sell <product> <qty>"""
    parts = message.strip().split()
    if len(parts) < 3:
        return (
            "Format: *sell [product naam] [qty]*\n"
            "Misaal: sell Atta 5\n"
            "Yeh stock se automatically minus ho jata hai."
        )
    try:
        qty = int(parts[-1])
        name = " ".join(parts[1:-1])
        item = db.get_product(tenant_slug, name)
        if not item:
            return (
                f"'{name}' inventory mein nahi mili.\n"
                "*stock* likhein list dekhne ke liye."
            )
        if item["quantity"] < qty:
            return (
                f"⚠️ Itna stock nahi!\n"
                f"{item['product_name']}: Sirf {item['quantity']} "
                f"{item['unit']} available hain.\n"
                f"Aap {qty} bech nahi sakte."
            )
        ref, total = db.create_order(
            tenant_slug, phone, item["product_name"],
            qty, item["sell_price"]
        )
        return (
            f"✅ *Sale Record Ho Gayi!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📋 Ref: {ref}\n"
            f"📦 {item['product_name']} × {qty} {item['unit']}\n"
            f"💰 Amount: ₨{total:,.0f}\n"
            f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Baki stock: {item['quantity'] - qty} {item['unit']}"
        )
    except ValueError:
        return "Qty ek number hona chahiye. Misaal: sell Atta 5"


# ── Orders ───────────────────────────────────────────────────────────────

def handle_order_start(tenant_slug: str, phone: str) -> str:
    db.set_session(tenant_slug, phone, "placing_order")
    items = [i for i in db.get_inventory(tenant_slug) if i["quantity"] > 0][:8]
    lines = [
        "🛍️ *Order Place Karein*",
        "━━━━━━━━━━━━━━━━━━",
        "Format: *order [product] [qty]*",
        "",
        "Available products:",
    ]
    for it in items:
        lines.append(
            f"• {it['product_name']} — {it['quantity']} {it['unit']} "
            f"@ ₨{it['sell_price']:,.0f}"
        )
    lines.append("\nMisaal: order Atta 5")
    return "\n".join(lines)


def handle_order_create(tenant_slug: str, phone: str, message: str) -> str:
    """Parse: order <product> <qty>"""
    parts = message.strip().split()
    if len(parts) < 3:
        return "Format: *order [product] [qty]*\nMisaal: order Atta 5"
    try:
        qty = int(parts[-1])
        name = " ".join(parts[1:-1])
        item = db.get_product(tenant_slug, name)
        if not item:
            return (
                f"'{name}' available nahi.\n"
                "*stock* likhein list dekhne ke liye."
            )
        if item["quantity"] < qty:
            return (
                f"⚠️ Sirf {item['quantity']} {item['unit']} available hain.\n"
                f"Choti quantity dein ya *stock* check karein."
            )
        ref, total = db.create_order(
            tenant_slug, phone, item["product_name"],
            qty, item["sell_price"]
        )
        db.clear_session(tenant_slug, phone)
        tenant = db.get_tenant(tenant_slug)
        ep = (tenant or {}).get("easypaisa_number", "")
        jc = (tenant or {}).get("jazzcash_number", "")
        pay_line = ""
        if ep:
            pay_line = f"\n💳 EasyPaisa: {ep}"
        elif jc:
            pay_line = f"\n💳 JazzCash: {jc}"
        return (
            f"✅ *Order Confirm!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📋 Order: {ref}\n"
            f"📦 {item['product_name']} × {qty} {item['unit']}\n"
            f"💰 Total: ₨{total:,.0f}{pay_line}\n"
            f"📅 {datetime.now().strftime('%d/%m/%Y')}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            "*payment* likhein payment details ke liye."
        )
    except ValueError:
        return "Qty ek number hona chahiye. Misaal: order Atta 5"


# ── Market Finder ────────────────────────────────────────────────────────

def handle_market_finder(tenant_slug: str, phone: str,
                         message: str = "") -> str:
    lower = message.lower()
    if "karachi" in lower or "khi" in lower:
        return _market_city("Karachi", [
            ("Jodia Bazaar", "Food, spices, grains, dry fruits — M.A. Jinnah Rd"),
            ("Saddar Bazaar", "Electronics, mobile phones, household items"),
            ("Empress Market", "Vegetables, meat, spices, daily items"),
            ("Bolton Market", "Wholesale cloth, garments"),
            ("Shershah", "Used electronics, spare parts"),
            ("New Sabzi Mandi", "Fresh fruit/vegetables — Superhighway"),
        ])
    if "lahore" in lower or "lhr" in lower:
        return _market_city("Lahore", [
            ("Anarkali Bazaar", "Clothes, fabric, accessories"),
            ("Azam Cloth Market", "Pakistan ka sabse bara cloth wholesale market"),
            ("Hall Road", "Electronics, computers, mobile phones"),
            ("Icchra Bazaar", "Women's fabric, stitching material"),
            ("Badami Bagh Mandi", "Fruit / vegetable wholesale"),
        ])
    if any(x in lower for x in ("islamabad", "isbad", "rawalpindi", "pindi")):
        return _market_city("Islamabad / Rawalpindi", [
            ("Melody Market", "General goods, electronics — Islamabad"),
            ("Raja Bazaar", "Wholesale spices, general goods — Rawalpindi"),
            ("I-8 Markaz", "Electronics, hardware"),
            ("Bara Kahu", "Vegetables, meat"),
        ])
    if "faisalabad" in lower or "lyallpur" in lower:
        return _market_city("Faisalabad", [
            ("Katchery Bazaar", "Cloth, fabric, yarn — Pakistan's textile hub"),
            ("Clock Tower Bazaar", "General wholesale goods"),
        ])
    return (
        "🏪 *Market Finder — Pakistan*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Apna sheher likhein:\n\n"
        "• *market karachi*\n"
        "• *market lahore*\n"
        "• *market islamabad*\n"
        "• *market faisalabad*\n\n"
        "🌐 Online: daraz.pk | olx.com.pk | tradekey.com"
    )


def _market_city(city: str, markets: list) -> str:
    lines = [f"🏪 *{city} ke Markets*", "━━━━━━━━━━━━━━━━━━"]
    for name, desc in markets:
        lines.append(f"📍 *{name}*\n   {desc}")
    lines += [
        "━━━━━━━━━━━━━━━━━━",
        "💡 Tip: Wholesale ke liye subah 7-10 AM best time hai.",
        "Doosre sheher: *market lahore* / *market karachi*",
    ]
    return "\n".join(lines)


# ── Payment ──────────────────────────────────────────────────────────────

def handle_payment(tenant_slug: str, phone: str) -> str:
    tenant = db.get_tenant(tenant_slug)
    return get_payment_menu(tenant)


# ── Appointments ─────────────────────────────────────────────────────────

def handle_appointment_start(tenant_slug: str, phone: str) -> str:
    db.set_session(tenant_slug, phone, "booking_appointment")
    today = date.today()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)
    return (
        "📅 *Appointment Book Karein*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Format mein likhein:\n"
        "*appoint [YYYY-MM-DD] [HH:MM] [purpose]*\n\n"
        "Misaalein:\n"
        f"• appoint {tomorrow.isoformat()} 10:00 Delivery\n"
        f"• appoint {day_after.isoformat()} 14:30 Meeting\n\n"
        f"Aaj ki date: {today.isoformat()}\n"
        "Waapis jaane ke liye *menu* likhein."
    )


def handle_appointment_create(tenant_slug: str, phone: str,
                               message: str) -> str:
    """Parse: appoint YYYY-MM-DD HH:MM [purpose]"""
    parts = message.strip().split()
    if len(parts) < 3:
        return (
            "Format: *appoint [date] [time] [purpose]*\n"
            "Misaal: appoint 2026-04-20 10:00 Delivery"
        )
    try:
        apt_date = parts[1]
        apt_time = parts[2]
        purpose = " ".join(parts[3:]) if len(parts) > 3 else "Business visit"
        datetime.strptime(apt_date, "%Y-%m-%d")
        datetime.strptime(apt_time, "%H:%M")
        apt_id = db.book_appointment(
            tenant_slug, phone, None, apt_date, apt_time, purpose
        )
        db.clear_session(tenant_slug, phone)
        return (
            f"✅ *Appointment Confirm!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🆔 ID: #{apt_id}\n"
            f"📅 Date: {apt_date}\n"
            f"🕐 Time: {apt_time}\n"
            f"📝 Purpose: {purpose}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            "Appointments dekhne ke liye *appointments* likhein.\n"
            "Cancel ke liye *cancel appoint [ID]* likhein."
        )
    except ValueError:
        return (
            "Date format: YYYY-MM-DD, Time format: HH:MM\n"
            "Misaal: appoint 2026-04-20 10:00 Delivery"
        )


def handle_view_appointments(tenant_slug: str, phone: str) -> str:
    apts = db.get_appointments(tenant_slug, upcoming_only=True, limit=10)
    if not apts:
        return (
            "📅 *Upcoming Appointments*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Abhi koi appointment nahi.\n"
            "Book karne ke liye *5* ya *appointment* likhein."
        )
    lines = ["📅 *Upcoming Appointments*", "━━━━━━━━━━━━━━━━━━"]
    for a in apts:
        icon = "✅" if a["status"] == "booked" else "❌"
        lines.append(
            f"{icon} #{a['id']} | {a['appointment_date']} "
            f"{a['appointment_time']} | {a['purpose'] or 'Visit'}"
        )
    lines += ["━━━━━━━━━━━━━━━━━━", "Cancel: *cancel appoint [ID]*"]
    return "\n".join(lines)


def handle_cancel_appointment(tenant_slug: str, phone: str,
                               message: str) -> str:
    parts = message.strip().split()
    apt_id = None
    for p in reversed(parts):
        if p.isdigit():
            apt_id = int(p)
            break
    if not apt_id:
        return "Format: *cancel appoint [ID]*\nMisaal: cancel appoint 3"
    db.cancel_appointment(apt_id, tenant_slug)
    return f"✅ Appointment #{apt_id} cancel ho gayi."


# ── Transactions ─────────────────────────────────────────────────────────

def handle_transactions(tenant_slug: str, phone: str) -> str:
    orders = db.get_orders(tenant_slug, phone=phone, limit=8)
    if not orders:
        return (
            "💳 *Meri History*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Abhi koi orders nahi.\n"
            "Order karne ke liye *2* ya *order* likhein."
        )
    lines = ["💳 *Recent Orders*", "━━━━━━━━━━━━━━━━━━"]
    total = 0.0
    for o in orders:
        icon = "✅" if o["status"] == "paid" else "⏳"
        lines.append(
            f"{icon} {o['order_ref']} | "
            f"{o['product_name']}×{o['quantity']} | "
            f"₨{o['total']:,.0f}"
        )
        total += o["total"]
    lines += ["━━━━━━━━━━━━━━━━━━", f"💰 Total: ₨{total:,.0f}"]
    return "\n".join(lines)


# ── Help ─────────────────────────────────────────────────────────────────

def handle_help() -> str:
    return (
        "❓ *BazaarBot Madad*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📦 *1* ya *stock* → Inventory dekhein\n"
        "➕ *add product [naam] [qty] [unit] [price]* → Naya product\n"
        "📉 *sell [naam] [qty]* → Sale record karein\n"
        "🔄 *update [naam] [qty]* → Stock update\n"
        "🛍️ *2* ya *order* → Order lein\n"
        "🏪 *3* ya *market [city]* → Market/supplier finder\n"
        "💰 *4* ya *payment* → Payment info\n"
        "📅 *5* ya *appointment* → Appointment book\n"
        "💳 *6* ya *history* → Orders history\n"
        "🔙 *menu* → Main menu wapas\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📧 Support: support@bazaarbot.pk"
    )


# ── Fallback ─────────────────────────────────────────────────────────────

def handle_unknown(tenant_slug: str, phone: str,
                   rag_snippet: str = "") -> str:
    if rag_snippet:
        return rag_snippet
    tenant = db.get_tenant(tenant_slug)
    bname = (tenant or {}).get("name", "BazaarBot")
    return (
        "🤔 Samajh nahi aaya.\n"
        "━━━━━━━━━━━━━━━━━━\n"
        + get_main_menu(bname)
    )
