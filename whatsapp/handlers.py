from datetime import datetime
from whatsapp.menu import get_main_menu

def handle_stock(from_number):
    return (
        "📦 *Current Stock Status*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✅ Product A — 150 units — ₨2,500/unit\n"
        "✅ Product B — 89 units — ₨1,800/unit\n"
        "⚠️ Product C — 12 units (LOW) — ₨3,200/unit\n"
        "❌ Product D — 0 units (OUT OF STOCK)\n"
        "✅ Product E — 200 units — ₨2,200/unit\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Reply *reorder <product>* to restock"
    )

def handle_order_start(from_number):
    return (
        "🛍️ *Place an Order*\n"
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
            
            # Price mapping
            prices = {
                "product a": 2500,
                "product b": 1800,
                "product c": 3200,
                "product e": 2200
            }
            unit_price = prices.get(product.lower(), 2500)
            total = quantity * unit_price
            
            return (
                f"✅ *Order Confirmed!*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📋 Order #ORD-{str(abs(hash(from_number)))[-4:]}\n"
                f"📦 {product.title()} × {quantity} units\n"
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
        "Available:\n"
        "• Product A\n"
        "• Product B\n"
        "• Product C\n"
        "• Product E\n\n"
        "Just type the product name!"
    )

def handle_price_lookup(from_number, message):
    """Find best supplier prices for a product."""
    product_map = {
        "product a": (
            "💰 *Best Prices for Product A*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🥇 Supplier 1: ₨2,300/unit (Best!)\n"
            "🥈 Supplier 2: ₨2,450/unit\n"
            "🥉 Supplier 3: ₨2,600/unit\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Reply *buy from supplier 1 Product A 100* to order"
        ),
        "product b": (
            "💰 *Best Prices for Product B*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🥇 Supplier 2: ₨1,700/unit (Best!)\n"
            "🥈 Supplier 1: ₨1,850/unit\n"
            "🥉 Supplier 3: ₨1,900/unit\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Reply *buy from supplier 2 Product B 50* to order"
        ),
        "product c": (
            "💰 *Best Prices for Product C*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🥇 Supplier 3: ₨3,100/unit (Best!)\n"
            "🥈 Supplier 1: ₨3,250/unit\n"
            "🥉 Supplier 2: ₨3,400/unit\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Reply *buy from supplier 3 Product C 20* to order"
        ),
    }
    
    for product, response in product_map.items():
        if product in message:
            return response
    
    return handle_price_start(from_number)

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
        "✅ Status: Active\n"
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
        "• Send *5* or *account* → My account\n"
        "• Send *menu* → Back to main menu\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Need more help? Contact admin."
    )

def handle_reorder(from_number, message):
    """Handle reorder requests."""
    parts = message.split()
    if len(parts) >= 2:
        product = " ".join(parts[1:])
        return (
            f"✅ *Reorder Request Submitted*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📦 Product: {product.title()}\n"
            f"🔄 Reorder quantity: 100 units\n"
            f"📅 Expected: 3-5 business days\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            "We'll notify you when stock arrives!"
        )
    return "Please use format: *reorder <product>*"

def handle_receipt(from_number, message):
    """Generate detailed receipt."""
    parts = message.split()
    if len(parts) >= 2:
        order_id = parts[1].upper()
        return (
            f"🧾 *Receipt for {order_id}*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📋 Order: {order_id}\n"
            f"📅 Date: {datetime.now().strftime('%d/%m/%Y')}\n"
            f"📦 Items: Product A × 50\n"
            f"💵 Subtotal: ₨1,10,000\n"
            f"🚢 Shipping: ₨2,000\n"
            f"💰 Total: ₨1,12,000\n"
            f"✅ Status: Paid\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            "Thank you for your business!"
        )
    return "Please use format: *receipt <order-id>*"

def handle_supplier_buy(from_number, message):
    """Handle supplier purchase."""
    # Parse: buy from supplier 1 Product A 100
    parts = message.split()
    if len(parts) >= 6:
        try:
            supplier_num = parts[3]
            product = " ".join(parts[4:-1])
            quantity = int(parts[-1])
            
            return (
                f"✅ *Supplier Order Confirmed!*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🏭 Supplier: #{supplier_num}\n"
                f"📦 Product: {product.title()}\n"
                f"📊 Quantity: {quantity} units\n"
                f"💰 Estimated: ₨{quantity * 2300:,}\n"
                f"📅 Delivery: 5-7 days\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                "Order placed with supplier!"
            )
        except (ValueError, IndexError):
            pass
    return "Please use format: *buy from supplier <num> <product> <quantity>*"

def handle_unknown(message):
    return (
        "🤔 I didn't understand that.\n"
        "━━━━━━━━━━━━━━━━━━\n"
        + get_main_menu()
    )
