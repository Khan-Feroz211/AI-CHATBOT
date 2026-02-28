from datetime import datetime
from whatsapp.menu import get_main_menu

def handle_stock(from_number):
    return (
        "📦 *Current Stock Status*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✅ Product A — 150 units\n"
        "✅ Product B — 89 units\n"
        "⚠️ Product C — 12 units (LOW)\n"
        "❌ Product D — 0 units (OUT OF STOCK)\n"
        "✅ Product E — 200 units\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Reply *reorder <product>* to restock"
    )

def handle_order_start(from_number):
    return (
        "🛒 *Place an Order*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Send your order in this format:\n"
        "*order <product> <quantity>*\n\n"
        "Example: order Product A 50"
    )

def handle_order_create(from_number, message):
    parts = message.split()
    if len(parts) >= 3:
        try:
            product = " ".join(parts[1:-1])
            quantity = int(parts[-1])
            total = quantity * 2500
            return (
                f"✅ *Order Confirmed!*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📋 Order #ORD-{str(abs(hash(from_number)))[-4:]}\n"
                f"📦 {product} × {quantity} units\n"
                f"💰 Total: ₨{total:,}\n"
                f"📅 Date: {datetime.now().strftime('%d/%m/%Y')}\n"
                f"🚚 Status: Processing\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"You'll receive updates on this order!"
            )
        except ValueError:
            pass
    return "Please use format: *order <product> <quantity>*"

def handle_price_start(from_number):
    return (
        "💰 *Price Finder*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Which product do you want to find the best price for?\n\n"
        "Available: Product A, Product B, Product C"
    )

def handle_transactions(from_number):
    return (
        "💳 *Recent Transactions*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "1. ORD-001 | Product A×50 | ₨1,10,000 | ✅ Paid\n"
        "2. ORD-002 | Product B×30 | ₨54,000 | ⏳ Pending\n"
        "3. ORD-003 | Product C×10 | ₨32,000 | ✅ Paid\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💰 Total Spent: ₨1,96,000\n"
        "Reply *receipt <order>* for detailed receipt"
    )

def handle_account(from_number):
    return (
        "👤 *My Account*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📱 Number: {from_number}\n"
        "🏢 Company: Demo Business\n"
        "📊 Plan: Standard\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Type *menu* to go back."
    )

def handle_help():
    return (
        "❓ *Help & Commands*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "• Send *1* or *stock* → Check inventory\n"
        "• Send *2* or *order* → Place an order\n"
        "• Send *3* or *price* → Find best price\n"
        "• Send *4* or *transactions* → View history\n"
        "• Send *menu* → Back to main menu\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Need more help? Contact admin."
    )

def handle_unknown(message):
    return (
        "🤔 I didn't understand that.\n"
        "━━━━━━━━━━━━━━━━━━\n"
        + get_main_menu()
    )
