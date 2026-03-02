#!/usr/bin/env python3
"""
Demo Data Setup Script
Initializes demo products, suppliers, and transactions in PKR for Monday client demo
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DemoDataSetup:
    """Setup demo data for WhatsApp bot."""
    
    def __init__(self):
        """Initialize database connection."""
        self.db_path = Path("chatbot_data/chatbot.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = None
        self.cursor = None
        
    def connect(self) -> bool:
        """Connect to database."""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.cursor = self.connection.cursor()
            print(f"✅ Connected to database: {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.commit()
            self.connection.close()
            print("✅ Database connection closed")
    
    def setup_demo_products(self) -> None:
        """Setup demo products in PKR."""
        print("\n📦 Setting up demo products...")
        
        products = [
            {
                "sku": "PROD-A",
                "name": "Product A",
                "price": 2500.00,
                "stock": 150,
                "description": "Premium quality Product A"
            },
            {
                "sku": "PROD-B",
                "name": "Product B",
                "price": 1800.00,
                "stock": 89,
                "description": "Standard Product B"
            },
            {
                "sku": "PROD-C",
                "name": "Product C",
                "price": 3200.00,
                "stock": 12,
                "description": "Limited stock Product C (LOW)"
            },
            {
                "sku": "PROD-D",
                "name": "Product D",
                "price": 950.00,
                "stock": 0,
                "description": "Product D - OUT OF STOCK"
            },
            {
                "sku": "PROD-E",
                "name": "Product E",
                "price": 4100.00,
                "stock": 200,
                "description": "High volume Product E"
            },
        ]
        
        try:
            # Create table if not exists
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    price FLOAT NOT NULL,
                    stock INTEGER NOT NULL DEFAULT 0,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert or update products
            for product in products:
                self.cursor.execute("""
                    INSERT OR REPLACE INTO products (sku, name, price, stock, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (product["sku"], product["name"], product["price"], 
                      product["stock"], product["description"]))
                print(f"  ✓ {product['name']} — ₨{product['price']:,.0f} | Stock: {product['stock']}")
            
            self.connection.commit()
            print("✅ Demo products created successfully")
        except Exception as e:
            print(f"❌ Failed to setup products: {e}")
    
    def setup_demo_suppliers(self) -> None:
        """Setup demo suppliers with pricing."""
        print("\n🤝 Setting up demo suppliers...")
        
        suppliers = [
            {
                "name": "Supplier A (Best)",
                "contact": "+923001234567",
                "pricing": [
                    ("PROD-A", 2200.00),
                    ("PROD-B", 1600.00),
                ]
            },
            {
                "name": "Supplier B",
                "contact": "+923001234568",
                "pricing": [
                    ("PROD-A", 2400.00),
                    ("PROD-B", 1750.00),
                ]
            },
            {
                "name": "Supplier C",
                "contact": "+923001234569",
                "pricing": [
                    ("PROD-A", 2600.00),
                    ("PROD-B", 1900.00),
                ]
            },
        ]
        
        try:
            # Create supplier table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    contact TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create supplier pricing table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS supplier_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER NOT NULL,
                    sku TEXT NOT NULL,
                    price FLOAT NOT NULL,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                    UNIQUE(supplier_id, sku)
                )
            """)
            
            # Insert suppliers
            for supplier in suppliers:
                self.cursor.execute("""
                    INSERT OR REPLACE INTO suppliers (name, contact)
                    VALUES (?, ?)
                """, (supplier["name"], supplier["contact"]))
                
                # Get supplier ID
                supplier_id = self.cursor.lastrowid
                
                # Insert pricing
                for sku, price in supplier["pricing"]:
                    self.cursor.execute("""
                        INSERT OR REPLACE INTO supplier_prices (supplier_id, sku, price)
                        VALUES (?, ?, ?)
                    """, (supplier_id, sku, price))
                
                print(f"  ✓ {supplier['name']}")
                for sku, price in supplier["pricing"]:
                    print(f"    - {sku}: ₨{price:,.0f}/unit")
            
            self.connection.commit()
            print("✅ Demo suppliers created successfully")
        except Exception as e:
            print(f"❌ Failed to setup suppliers: {e}")
    
    def setup_demo_transactions(self) -> None:
        """Setup demo transactions."""
        print("\n💳 Setting up demo transactions...")
        
        transactions = [
            {
                "order_id": "ORD-001",
                "sku": "PROD-A",
                "quantity": 50,
                "amount": 110000.00,
                "status": "paid",
                "days_ago": 5
            },
            {
                "order_id": "ORD-002",
                "sku": "PROD-B",
                "quantity": 30,
                "amount": 54000.00,
                "status": "pending",
                "days_ago": 2
            },
            {
                "order_id": "ORD-003",
                "sku": "PROD-C",
                "quantity": 10,
                "amount": 32000.00,
                "status": "paid",
                "days_ago": 1
            },
        ]
        
        try:
            # Create transactions table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE NOT NULL,
                    phone TEXT NOT NULL DEFAULT '+9203375651717',
                    sku TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    amount FLOAT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert transactions
            for txn in transactions:
                created_at = datetime.now() - timedelta(days=txn["days_ago"])
                self.cursor.execute("""
                    INSERT OR REPLACE INTO transactions 
                    (order_id, phone, sku, quantity, amount, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (txn["order_id"], "+9203375651717", txn["sku"], 
                      txn["quantity"], txn["amount"], txn["status"], 
                      created_at.isoformat()))
                
                status_emoji = "✅" if txn["status"] == "paid" else "⏳"
                print(f"  {status_emoji} {txn['order_id']} | {txn['sku']}×{txn['quantity']} | ₨{txn['amount']:,.0f}")
            
            self.connection.commit()
            print(f"✅ Demo transactions created (Total: ₨1,96,000)")
        except Exception as e:
            print(f"❌ Failed to setup transactions: {e}")
    
    def setup_demo_admin_account(self) -> None:
        """Setup demo admin account."""
        print("\n👤 Setting up demo admin account...")
        
        try:
            # Create clients table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone TEXT UNIQUE NOT NULL,
                    name TEXT,
                    role TEXT DEFAULT 'user',
                    is_verified BOOLEAN DEFAULT FALSE,
                    mfa_enabled BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert demo admin
            admin_phone = "+9203375651717"
            self.cursor.execute("""
                INSERT OR REPLACE INTO clients (phone, name, role, is_verified, mfa_enabled)
                VALUES (?, ?, ?, ?, ?)
            """, (admin_phone, "Demo Admin", "admin", True, True))
            
            self.connection.commit()
            print(f"  ✓ Admin account linked to {admin_phone}")
            print(f"  ✓ MFA enabled")
            print("✅ Demo admin account created")
        except Exception as e:
            print(f"❌ Failed to setup admin account: {e}")
    
    def run(self) -> None:
        """Run all setup steps."""
        print("\n" + "="*60)
        print("  AI Business Bot - Demo Data Setup")
        print("="*60)
        
        if not self.connect():
            sys.exit(1)
        
        try:
            self.setup_demo_products()
            self.setup_demo_suppliers()
            self.setup_demo_transactions()
            self.setup_demo_admin_account()
            
            print("\n" + "="*60)
            print("✅ DEMO DATA SETUP COMPLETE!")
            print("="*60)
            print("\n📌 Next steps:")
            print("1. python start_demo.py")
            print("2. Copy the webhook URL from the console")
            print("3. Paste in Twilio Console → Messaging → Webhook URL")
            print("4. Tell client: Send 'join demo' to +1 415 523 8886")
            print("\n")
            
        finally:
            self.close()


if __name__ == "__main__":
    setup = DemoDataSetup()
    setup.run()
