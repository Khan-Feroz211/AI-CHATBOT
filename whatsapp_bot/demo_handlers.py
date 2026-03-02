"""
WhatsApp Demo Conversation Flow Handlers
Handles join, MFA, stock check, ordering, pricing, and transaction queries
"""

import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pyotp
from flask import request

# Import from the project
from src.auth.qr_generator import WhatsAppQRSender
from src.utils import format_pkr

logger = logging.getLogger("demo_handlers")


class DemoConversationHandler:
    """Handle all demo conversation flows."""
    
    def __init__(self, phone_id: str, access_token: str):
        """Initialize with WhatsApp API credentials."""
        self.phone_id = phone_id
        self.access_token = access_token
        self.qr_sender = WhatsAppQRSender(access_token, phone_id)
        
        # Demo data
        self.products = {
            "Product A": {"sku": "PROD-A", "price": 2500, "stock": 150},
            "Product B": {"sku": "PROD-B", "price": 1800, "stock": 89},
            "Product C": {"sku": "PROD-C", "price": 3200, "stock": 12},
            "Product D": {"sku": "PROD-D", "price": 950, "stock": 0},
            "Product E": {"sku": "PROD-E", "price": 4100, "stock": 200},
        }
        
        self.suppliers = {
            1: {"name": "Supplier A (Best)", "PROD-A": 2200, "PROD-B": 1600},
            2: {"name": "Supplier B", "PROD-A": 2400, "PROD-B": 1750},
            3: {"name": "Supplier C", "PROD-A": 2600, "PROD-B": 1900},
        }
        
        self.transactions = [
            {
                "id": "ORD-001",
                "product": "Product A",
                "qty": 50,
                "amount": 110000,
                "status": "✅ Paid",
            },
            {
                "id": "ORD-002",
                "product": "Product B",
                "qty": 30,
                "amount": 54000,
                "status": "⏳ Pending",
            },
            {
                "id": "ORD-003",
                "product": "Product C",
                "qty": 10,
                "amount": 32000,
                "status": "✅ Paid",
            },
        ]
    
    def _send_message(self, to_phone: str, message: str) -> bool:
        """Send a WhatsApp message."""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": to_phone,
                "type": "text",
                "text": {"body": message},
            }
            
            import httpx
            client = httpx.Client()
            response = client.post(
                f"https://graph.instagram.com/v18.0/{self.phone_id}/messages",
                headers=headers,
                json=payload,
                timeout=15,
            )
            
            if response.status_code >= 300:
                logger.error(f"Failed to send message: {response.text}")
                return False
            
            logger.info(f"Message sent to {to_phone}")
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def handle_join_request(self, phone: str, join_code: str) -> None:
        """Handle 'join <code>' request - Step 1."""
        try:
            # Verify join code (in demo, any code works)
            logger.info(f"User {phone} joining with code: {join_code}")
            
            # Send welcome message
            welcome = (
                "*🤖 Welcome to AI Business Bot!*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Setting up your secure account...\n\n"
                "🔐 Please scan the QR code with Microsoft or Oracle Authenticator"
            )
            self._send_message(phone, welcome)
            
            # Generate and send QR code for MFA setup
            import hashlib
            secret = hashlib.sha256(
                f"{phone}-{datetime.now().isoformat()}".encode()
            ).hexdigest()[:32]
            
            totp = pyotp.TOTP(secret)
            issuer = os.getenv("MFA_ISSUER_NAME", "AI Business Bot")
            provisioning_uri = totp.provisioning_uri(
                name=phone,
                issuer_name=issuer,
            )
            
            # Send QR code image
            qr_message = "🔐 *Scan this QR code:*"
            self._send_message(phone, qr_message)
            
            logger.info(f"QR code generated for {phone}")
            
            # Send instruction
            instruction = (
                "After scanning, you'll see a 6-digit code changing every 30 seconds.\n"
                "Send that code to continue! ⏱️"
            )
            self._send_message(phone, instruction)
            
        except Exception as e:
            logger.error(f"Error in join request: {e}")
            error_msg = "❌ Setup failed. Type *help* for support."
            self._send_message(phone, error_msg)
    
    def handle_mfa_code(self, phone: str, code: str) -> None:
        """Handle MFA code submission - Step 2."""
        try:
            # In demo, validate 6-digit format
            if not re.match(r"^\d{6}$", code):
                error = "❌ Invalid code format. Please send a 6-digit number."
                self._send_message(phone, error)
                return
            
            # In production, verify against TOTP secret
            # For demo, accept any valid 6-digit code
            
            success = (
                "*✅ Authenticated!*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Welcome aboard! 🎉\n\n"
                "Here's your main menu 👇"
            )
            self._send_message(phone, success)
            
            # Send main menu
            self.send_main_menu(phone)
            
            logger.info(f"User {phone} successfully authenticated")
            
        except Exception as e:
            logger.error(f"Error in MFA code handling: {e}")
            error_msg = "❌ Authentication failed. Type *help* for support."
            self._send_message(phone, error_msg)
    
    def send_main_menu(self, phone: str) -> None:
        """Send main menu - Step 3."""
        menu = (
            "*🤖 AI Business Bot*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Hello! How can I help you today?\n\n"
            "1️⃣ Check Stock\n"
            "2️⃣ Place Order\n"
            "3️⃣ Find Best Price\n"
            "4️⃣ View Transactions\n"
            "5️⃣ My Account\n"
            "6️⃣ Help\n\n"
            "Just reply with a number or type your question!"
        )
        self._send_message(phone, menu)
    
    def handle_stock_check(self, phone: str) -> None:
        """Handle stock check request - Step 4."""
        try:
            stock_msg = (
                "*📦 Current Stock Status*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "✅ Product A — 150 units\n"
                "✅ Product B — 89 units\n"
                "⚠️  Product C — 12 units (LOW)\n"
                "❌ Product D — 0 units (OUT OF STOCK)\n"
                "✅ Product E — 200 units\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Reply *reorder <product>* to restock"
            )
            self._send_message(phone, stock_msg)
            logger.info(f"Stock status sent to {phone}")
        except Exception as e:
            logger.error(f"Error in stock check: {e}")
            self._send_message(phone, "❌ Error retrieving stock. Try again later.")
    
    def handle_place_order(self, phone: str, order_text: str = None) -> None:
        """Handle order placement - Step 5."""
        try:
            if order_text and order_text.lower().startswith("order"):
                # Parse order: "order Product A 50"
                parts = order_text.split()
                if len(parts) >= 3:
                    product_name = " ".join(parts[1:-1])
                    try:
                        quantity = int(parts[-1])
                        self._confirm_order(phone, product_name, quantity)
                        return
                    except (ValueError, IndexError):
                        pass
            
            # Ask what to order
            ask_msg = (
                "*🛒 Place an Order*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Available products:\n"
                "• Product A ₨2,500/unit\n"
                "• Product B ₨1,800/unit\n"
                "• Product C ₨3,200/unit\n"
                "• Product E ₨4,100/unit\n\n"
                "Send: *order <product> <quantity>*\n"
                "Example: *order Product A 50*"
            )
            self._send_message(phone, ask_msg)
            logger.info(f"Order prompt sent to {phone}")
        except Exception as e:
            logger.error(f"Error in order placement: {e}")
            self._send_message(phone, "❌ Error processing order. Try again.")
    
    def _confirm_order(self, phone: str, product: str, qty: int) -> None:
        """Confirm an order."""
        if product not in self.products:
            self._send_message(phone, f"❌ Product '{product}' not found.")
            return
        
        product_data = self.products[product]
        price = product_data["price"]
        total = price * qty
        order_id = f"ORD-{datetime.now().strftime('%H%M%S')}"
        
        confirm = (
            f"*✅ Order Confirmed!*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 Order #{order_id}\n"
            f"📦 {product} × {qty} units\n"
            f"💰 Total: {format_pkr(total)}\n"
            f"📅 Date: {datetime.now().strftime('%d-%m-%Y %H:%M')}\n"
            f"🚚 Status: Processing\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"You'll receive updates on this order!"
        )
        self._send_message(phone, confirm)
        logger.info(f"Order {order_id} placed for {phone}")
    
    def handle_price_finder(self, phone: str, product: str = None) -> None:
        """Handle price finder request - Step 6."""
        try:
            if not product:
                # Ask which product
                ask_msg = (
                    "*💰 Best Price Finder*\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "Which product do you need the best price for?\n\n"
                    "• Product A\n"
                    "• Product B\n\n"
                    "Send the product name!"
                )
                self._send_message(phone, ask_msg)
                return
            
            # Show prices for the product
            if product == "Product A":
                prices_msg = (
                    "*💰 Best Prices for Product A*\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "1. Supplier A — ₨2,200/unit ⭐ BEST\n"
                    "2. Supplier B — ₨2,400/unit\n"
                    "3. Supplier C — ₨2,600/unit\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "Reply *buy from supplier 1* to order!"
                )
            elif product == "Product B":
                prices_msg = (
                    "*💰 Best Prices for Product B*\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "1. Supplier A — ₨1,600/unit ⭐ BEST\n"
                    "2. Supplier B — ₨1,750/unit\n"
                    "3. Supplier C — ₨1,900/unit\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "Reply *buy from supplier 1* to order!"
                )
            else:
                self._send_message(phone, f"❌ Product '{product}' not available in price comparison.")
                return
            
            self._send_message(phone, prices_msg)
            logger.info(f"Price finder results sent for {product}")
        except Exception as e:
            logger.error(f"Error in price finder: {e}")
            self._send_message(phone, "❌ Error finding prices. Try again.")
    
    def handle_transactions(self, phone: str) -> None:
        """Handle transaction history request - Step 7."""
        try:
            trans_msg = (
                "*💳 Recent Transactions*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            )
            
            for i, txn in enumerate(self.transactions, 1):
                trans_msg += (
                    f"{i}. {txn['id']} | {txn['product']}×{txn['qty']} | "
                    f"{format_pkr(txn['amount'])} | {txn['status']}\n"
                )
            
            trans_msg += (
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 Total Spent: {format_pkr(196000)}\n"
                "Reply *receipt <order>* for details!"
            )
            
            self._send_message(phone, trans_msg)
            logger.info(f"Transaction history sent to {phone}")
        except Exception as e:
            logger.error(f"Error in transactions: {e}")
            self._send_message(phone, "❌ Error retrieving transactions.")
    
    def handle_unknown_command(self, phone: str) -> None:
        """Handle unknown commands with graceful fallback."""
        try:
            unknown_msg = (
                "*ℹ️ I didn't understand that.*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Here's what I can do:\n\n"
            )
            unknown_msg += (
                "1️⃣ *Check Stock* — See product availability\n"
                "2️⃣ *Place Order* — Order products now\n"
                "3️⃣ *Find Best Price* — Compare supplier prices\n"
                "4️⃣ *View Transactions* — See your order history\n"
                "5️⃣ *My Account* — Account settings\n"
                "6️⃣ *Help* — Get support\n\n"
                "Just send a number! 👇"
            )
            self._send_message(phone, unknown_msg)
        except Exception as e:
            logger.error(f"Error in unknown command: {e}")
            fallback = "❌ Something went wrong. Type *menu* to continue."
            self._send_message(phone, fallback)
    
    def process_message(self, phone: str, message_text: str) -> None:
        """Main message processor - routes to appropriate handler."""
        try:
            msg_lower = message_text.lower().strip()
            
            # Route based on message content
            if msg_lower.startswith("join"):
                # Extract join code
                parts = msg_lower.split()
                code = parts[1] if len(parts) > 1 else "demo"
                self.handle_join_request(phone, code)
            
            elif re.match(r"^\d{6}$", msg_lower):
                # MFA code
                self.handle_mfa_code(phone, msg_lower)
            
            elif msg_lower in ["1", "stock", "check stock"]:
                self.handle_stock_check(phone)
            
            elif msg_lower.startswith(("2", "order", "place order")):
                if msg_lower.startswith("order"):
                    self.handle_place_order(phone, message_text)
                else:
                    self.handle_place_order(phone)
            
            elif msg_lower in ["3", "price", "find best price"]:
                # Check if product name follows
                if msg_lower.startswith("3"):
                    self.handle_price_finder(phone)
                else:
                    parts = message_text.split()
                    product = " ".join(parts[1:]) if len(parts) > 1 else None
                    self.handle_price_finder(phone, product)
            
            elif msg_lower in ["4", "transactions", "history"]:
                self.handle_transactions(phone)
            
            elif msg_lower in ["5", "account", "my account"]:
                account_msg = (
                    "*👤 Your Account*\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "Phone: +9203375651717\n"
                    "Status: ✅ Active\n"
                    "MFA: ✅ Enabled\n"
                    "Role: Admin\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "Contact support for changes."
                )
                self._send_message(phone, account_msg)
            
            elif msg_lower in ["6", "help"]:
                help_msg = (
                    "*🆘 Help*\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "Commands:\n"
                    "• *1* or *stock* — Check inventory\n"
                    "• *2* or *order <name> <qty>* — Place order\n"
                    "• *3* or *price* — Find best prices\n"
                    "• *4* or *transactions* — View history\n"
                    "• *menu* — Show main menu\n\n"
                    "Issues? Reply *support*"
                )
                self._send_message(phone, help_msg)
            
            elif msg_lower == "menu":
                self.send_main_menu(phone)
            
            else:
                # Unknown command
                self.handle_unknown_command(phone)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_msg = "❌ Technical error. Type *menu* to try again."
            self._send_message(phone, error_msg)
