from auth.mfa_whatsapp import is_user_authenticated, handle_mfa_flow
from whatsapp.menu import get_main_menu
from whatsapp.handlers import (
    handle_stock, handle_order_start, handle_order_create,
    handle_price_start, handle_price_lookup, handle_transactions, 
    handle_account, handle_help, handle_reorder, handle_receipt,
    handle_supplier_buy, handle_unknown
)

def process_message(from_number, message):
    """Route incoming messages to appropriate handlers."""
    try:
        message = message.strip().lower()
        
        # MFA DISABLED FOR DEMO - Uncomment below to enable
        # if not is_user_authenticated(from_number):
        #     return handle_mfa_flow(from_number, message)
        
        # Menu triggers
        if message in ["hi", "hello", "start", "menu", "help me", ""]:
            return get_main_menu()
        
        # Stock
        elif message in ["1", "stock", "check stock", "inventory"]:
            return handle_stock(from_number)
        
        # Order start
        elif message in ["2", "order", "place order", "new order"]:
            return handle_order_start(from_number)
        
        # Order create
        elif message.startswith("order "):
            return handle_order_create(from_number, message)
        
        # Price finder
        elif message in ["3", "price", "find price", "best price"]:
            return handle_price_start(from_number)
        
        # Price lookup
        elif any(p in message for p in ["product a", "product b", "product c", "product d", "product e"]):
            return handle_price_lookup(from_number, message)
        
        # Transactions
        elif message in ["4", "transactions", "history", "my orders"]:
            return handle_transactions(from_number)
        
        # Account
        elif message in ["5", "account", "my account", "profile"]:
            return handle_account(from_number)
        
        # Help
        elif message in ["6", "help", "?"]:
            return handle_help()
        
        # Reorder
        elif message.startswith("reorder "):
            return handle_reorder(from_number, message)
        
        # Receipt
        elif message.startswith("receipt "):
            return handle_receipt(from_number, message)
        
        # Buy from supplier
        elif message.startswith("buy from supplier"):
            return handle_supplier_buy(from_number, message)
        
        # Unknown
        else:
            return handle_unknown(message)
    
    except Exception as e:
        print(f"❌ Router error: {e}")
        import traceback
        traceback.print_exc()
        return "Sorry, something went wrong. Type *menu* to continue."
