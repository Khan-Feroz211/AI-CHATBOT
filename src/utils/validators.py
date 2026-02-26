"""Input validation utilities."""

import re
from typing import Tuple


def validate_phone_number(phone: str) -> Tuple[bool, str]:
    """Validate phone number format.

    Supports formats:
    - Pakistan: +923001234567, 923001234567, 3001234567
    - International: +1234567890

    Args:
        phone: Phone number to validate

    Returns:
        Tuple of (is_valid, normalized_number)
    """
    if not phone or not isinstance(phone, str):
        return False, ""

    # Remove spaces and dashes
    phone = phone.strip().replace(" ", "").replace("-", "")

    # Check if all characters are digits or + at start
    if not re.match(r"^\+?\d+$", phone):
        return False, ""

    # Must be at least 10 digits
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 10:
        return False, ""

    # Normalize to international format
    if not phone.startswith("+"):
        if phone.startswith("92"):  # Pakistan code
            phone = "+" + phone
        elif phone.startswith("03"):  # Pakistan local
            phone = "+92" + phone[1:]
        elif phone.startswith("3"):  # Pakistan local without 0
            phone = "+923" + phone[1:]
        else:
            phone = "+" + phone

    return True, phone


def validate_otp(otp: str) -> bool:
    """Validate OTP format (6 digits).

    Args:
        otp: OTP code

    Returns:
        True if valid format
    """
    if not otp or not isinstance(otp, str):
        return False
    return bool(re.match(r"^\d{6}$", otp.strip()))


def validate_sku(sku: str) -> bool:
    """Validate product SKU format.

    Args:
        sku: Stock keeping unit

    Returns:
        True if valid format
    """
    if not sku or not isinstance(sku, str):
        return False
    # SKU: alphanumeric, 3-20 characters, may contain dashes
    return bool(re.match(r"^[A-Z0-9\-]{3,20}$", sku.upper().strip()))


def validate_quantity(qty: any) -> Tuple[bool, int]:
    """Validate quantity is positive integer.

    Args:
        qty: Quantity value

    Returns:
        Tuple of (is_valid, quantity)
    """
    try:
        qty_int = int(qty)
        return qty_int > 0, qty_int if qty_int > 0 else 0
    except (TypeError, ValueError):
        return False, 0


def validate_price(price: any) -> Tuple[bool, float]:
    """Validate price is positive number.

    Args:
        price: Price value

    Returns:
        Tuple of (is_valid, price)
    """
    try:
        price_float = float(price)
        return price_float > 0, round(price_float, 2) if price_float > 0 else 0.0
    except (TypeError, ValueError):
        return False, 0.0


def validate_email(email: str) -> bool:
    """Validate email format.

    Args:
        email: Email address

    Returns:
        True if valid format
    """
    if not email or not isinstance(email, str):
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def validate_order_number(order_num: str) -> bool:
    """Validate order number format.

    Args:
        order_num: Order number

    Returns:
        True if valid format
    """
    if not order_num or not isinstance(order_num, str):
        return False
    # Order format: ORD-YYYYMMDD-XXXXX or similar
    return len(order_num.strip()) >= 5


def validate_text_input(
    text: str, min_len: int = 1, max_len: int = 1000
) -> Tuple[bool, str]:
    """Validate text input length.

    Args:
        text: Text to validate
        min_len: Minimum length
        max_len: Maximum length

    Returns:
        Tuple of (is_valid, cleaned_text)
    """
    if not isinstance(text, str):
        return False, ""

    cleaned = text.strip()
    is_valid = min_len <= len(cleaned) <= max_len
    return is_valid, cleaned if is_valid else ""


def validate_selection(choice: str, valid_options: list) -> Tuple[bool, str]:
    """Validate selection is in valid options.

    Args:
        choice: Selected option
        valid_options: List of valid options

    Returns:
        Tuple of (is_valid, choice)
    """
    if not choice or not isinstance(choice, str):
        return False, ""

    choice = choice.strip().lower()
    valid_lower = [option.lower() for option in valid_options]

    if choice in valid_lower:
        # Return original case from valid_options
        idx = valid_lower.index(choice)
        return True, valid_options[idx]

    return False, ""


def validate_order_status(status: str) -> Tuple[bool, str]:
    """Validate order status.

    Args:
        status: Order status

    Returns:
        Tuple of (is_valid, status)
    """
    valid_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
    return validate_selection(status, valid_statuses)


def validate_payment_status(status: str) -> Tuple[bool, str]:
    """Validate payment status.

    Args:
        status: Payment status

    Returns:
        Tuple of (is_valid, status)
    """
    valid_statuses = ["unpaid", "paid", "partial", "refunded"]
    return validate_selection(status, valid_statuses)


def validate_role(role: str) -> Tuple[bool, str]:
    """Validate user role.

    Args:
        role: User role

    Returns:
        Tuple of (is_valid, role)
    """
    valid_roles = ["client", "admin", "manager"]
    return validate_selection(role, valid_roles)
