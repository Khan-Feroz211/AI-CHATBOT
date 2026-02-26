"""Output formatters for WhatsApp messages."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List


class WhatsAppFormatter:
    """Format data for WhatsApp messages."""

    # Common separators and symbols
    DIVIDER = "─" * 30
    BULLET = "✓"
    ARROW = "→"
    RUPEE = "Rs."

    @staticmethod
    def bold(text: str) -> str:
        """Format text as bold. WhatsApp uses *text*."""
        return f"*{text}*"

    @staticmethod
    def italic(text: str) -> str:
        """Format text as italic. WhatsApp uses _text_."""
        return f"_{text}_"

    @staticmethod
    def code(text: str) -> str:
        """Format text as code. WhatsApp uses ```text```."""
        return f"```{text}```"

    @staticmethod
    def format_currency(amount: float) -> str:
        """Format amount as currency.

        Args:
            amount: Amount in decimal

        Returns:
            Formatted currency string "Rs. 1,234.50"
        """
        if isinstance(amount, Decimal):
            amount = float(amount)
        return f"Rs. {amount:,.2f}"

    @staticmethod
    def format_quantity(qty: int, unit: str = "pcs") -> str:
        """Format quantity with unit.

        Args:
            qty: Quantity
            unit: Unit (pcs, kg, liters, etc.)

        Returns:
            Formatted string "100 pcs"
        """
        return f"{qty} {unit}"

    @staticmethod
    def format_phone(phone: str) -> str:
        """Format phone number for display.

        Args:
            phone: Phone number

        Returns:
            Formatted phone (last 4 digits)
        """
        if len(phone) >= 4:
            return f"****{phone[-4:]}"
        return "*" * (len(phone) - 1) + phone[-1]

    @staticmethod
    def format_date(date: datetime) -> str:
        """Format datetime for display.

        Args:
            date: Datetime object

        Returns:
            Formatted date string
        """
        if isinstance(date, str):
            return date
        return date.strftime("%d-%m-%Y")

    @staticmethod
    def format_time(date: datetime) -> str:
        """Format datetime for display with time.

        Args:
            date: Datetime object

        Returns:
            Formatted datetime string
        """
        if isinstance(date, str):
            return date
        return date.strftime("%d-%m-%Y %H:%M")

    @staticmethod
    def format_order_summary(order: Dict[str, Any]) -> str:
        """Format order details for display.

        Args:
            order: Order dict with keys: number, status, total, items_count

        Returns:
            Formatted order summary
        """
        lines = [
            WhatsAppFormatter.bold(f"Order #{order.get('number', 'N/A')}"),
            f"Status: {order.get('status', 'Unknown').upper()}",
            f"Items: {order.get('items_count', 0)}",
            f"Total: {WhatsAppFormatter.format_currency(order.get('total', 0))}",
        ]
        return "\n".join(lines)

    @staticmethod
    def format_product_list(products: List[Dict[str, Any]]) -> str:
        """Format list of products for display.

        Args:
            products: List of product dicts with keys: sku, name, price, quantity

        Returns:
            Formatted product list
        """
        if not products:
            return "No products found."

        lines = [WhatsAppFormatter.bold("Available Products:"), ""]

        for i, product in enumerate(products, 1):
            lines.append(
                f"{i}. {WhatsAppFormatter.bold(product.get('name', 'Unknown'))}"
            )
            lines.append(f"   SKU: {product.get('sku', 'N/A')}")
            lines.append(
                f"   Price: {WhatsAppFormatter.format_currency(product.get('price', 0))}"
            )
            lines.append(f"   Stock: {product.get('quantity', 0)} pcs")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def format_invoice(order: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
        """Format invoice for display.

        Args:
            order: Order dict with keys: number, date, client_name, total
            items: List of item dicts with keys: name, qty, price, subtotal

        Returns:
            Formatted invoice
        """
        lines = [
            WhatsAppFormatter.bold("INVOICE"),
            WhatsAppFormatter.DIVIDER,
            f"Order #: {order.get('number', 'N/A')}",
            f"Date: {WhatsAppFormatter.format_date(order.get('date', datetime.now()))}",
            f"Customer: {order.get('client_name', 'N/A')}",
            "",
            WhatsAppFormatter.bold("Items:"),
        ]

        subtotal = 0
        for item in items:
            lines.append(f"{item.get('name', 'Unknown')}")
            lines.append(
                f"  {item.get('qty', 0)} × {WhatsAppFormatter.format_currency(item.get('price', 0))} = {WhatsAppFormatter.format_currency(item.get('subtotal', 0))}"
            )
            subtotal += item.get("subtotal", 0)

        lines.extend(
            [
                "",
                WhatsAppFormatter.DIVIDER,
                f"Total: {WhatsAppFormatter.bold(WhatsAppFormatter.format_currency(order.get('total', subtotal)))}",
            ]
        )

        return "\n".join(lines)

    @staticmethod
    def format_menu(options: List[str], title: str = None) -> str:
        """Format menu options for display.

        Args:
            options: List of option strings
            title: Menu title (optional)

        Returns:
            Formatted menu
        """
        lines = []

        if title:
            lines.append(WhatsAppFormatter.bold(title))
            lines.append("")

        for i, option in enumerate(options, 1):
            lines.append(f"{i}. {option}")

        return "\n".join(lines)

    @staticmethod
    def format_status_message(title: str, details: Dict[str, Any]) -> str:
        """Format status message.

        Args:
            title: Status title
            details: Dict of key-value details

        Returns:
            Formatted status message
        """
        lines = [WhatsAppFormatter.bold(title)]

        for key, value in details.items():
            lines.append(f"{key}: {value}")

        return "\n".join(lines)

    @staticmethod
    def format_payment_summary(unpaid: float, paid: float, credit_limit: float) -> str:
        """Format payment status summary.

        Args:
            unpaid: Unpaid amount
            paid: Paid amount
            credit_limit: Credit limit

        Returns:
            Formatted payment summary
        """
        available_credit = credit_limit - paid

        lines = [
            WhatsAppFormatter.bold("Payment Summary"),
            f"Paid: {WhatsAppFormatter.format_currency(paid)}",
            f"Unpaid: {WhatsAppFormatter.format_currency(unpaid)}",
            f"Credit Limit: {WhatsAppFormatter.format_currency(credit_limit)}",
            f"Available: {WhatsAppFormatter.format_currency(max(0, available_credit))}",
        ]

        return "\n".join(lines)

    @staticmethod
    def format_error(error_title: str, error_message: str) -> str:
        """Format error message.

        Args:
            error_title: Error title
            error_message: Error message details

        Returns:
            Formatted error message
        """
        return f"{WhatsAppFormatter.bold('❌ ' + error_title)}\n\n{error_message}"

    @staticmethod
    def format_success(success_title: str, success_message: str = None) -> str:
        """Format success message.

        Args:
            success_title: Success title
            success_message: Success message details (optional)

        Returns:
            Formatted success message
        """
        lines = [WhatsAppFormatter.bold("✓ " + success_title)]

        if success_message:
            lines.append("")
            lines.append(success_message)

        return "\n".join(lines)

    @staticmethod
    def format_order_status_update(
        order_number: str, old_status: str, new_status: str
    ) -> str:
        """Format order status update notification.

        Args:
            order_number: Order number
            old_status: Previous status
            new_status: New status

        Returns:
            Formatted update message
        """
        return f"{WhatsAppFormatter.bold(f'Order #{order_number}')}\nStatus: {old_status.upper()} {WhatsAppFormatter.ARROW} {WhatsAppFormatter.bold(new_status.upper())}"

    @staticmethod
    def format_stock_alert(
        product_name: str, sku: str, current_qty: int, reorder_qty: int
    ) -> str:
        """Format low stock alert.

        Args:
            product_name: Product name
            sku: Product SKU
            current_qty: Current quantity
            reorder_qty: Reorder quantity

        Returns:
            Formatted alert
        """
        lines = [
            WhatsAppFormatter.bold("⚠️ Low Stock Alert"),
            f"Product: {product_name}",
            f"SKU: {sku}",
            f"Current: {current_qty} pcs",
            f"Reorder Level: {reorder_qty} pcs",
        ]
        return "\n".join(lines)
