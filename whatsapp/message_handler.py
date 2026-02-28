from auth.mfa_whatsapp import is_user_authenticated, handle_mfa_flow
from whatsapp.menu import get_main_menu
from whatsapp.handlers import (
    handle_stock, handle_order_start, handle_order_create,
    handle_price_start, handle_transactions, handle_account,
    handle_help, handle_unknown
)

def process_message(from_number, message):
    try:
        if not is_user_authenticated(from_number):
            return handle_mfa_flow(from_number, message)

        if message in ["hi", "hello", "start", "menu", ""]:
            return get_main_menu()
        elif message in ["1", "stock", "check stock"]:
            return handle_stock(from_number)
        elif message in ["2", "order", "place order"]:
            return handle_order_start(from_number)
        elif message.startswith("order "):
            return handle_order_create(from_number, message)
        elif message in ["3", "price", "find price"]:
            return handle_price_start(from_number)
        elif message in ["4", "transactions"]:
            return handle_transactions(from_number)
        elif message in ["5", "account", "my account"]:
            return handle_account(from_number)
        elif message in ["6", "help"]:
            return handle_help()
        else:
            return handle_unknown(message)
    except Exception as e:
        print(f"❌ Process message error: {e}")
        return "Sorry, something went wrong. Type *menu* to continue."
