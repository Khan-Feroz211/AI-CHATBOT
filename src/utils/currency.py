"""Pakistani Rupee (PKR) currency formatting utilities."""

from typing import Union


def format_pkr(amount: Union[int, float]) -> str:
    """Format amount in Pakistani Rupee format with ₨ symbol.
    
    Args:
        amount: Amount in PKR (numeric value)
        
    Returns:
        Formatted string like "₨1,500.00" or "₨2,500"
        
    Examples:
        >>> format_pkr(1500)
        '₨1,500.00'
        >>> format_pkr(2500.50)
        '₨2,500.50'
        >>> format_pkr(100)
        '₨100.00'
    """
    try:
        amount_float = float(amount)
        if amount_float == int(amount_float):
            return f"₨{int(amount_float):,}"
        return f"₨{amount_float:,.2f}"
    except (ValueError, TypeError):
        return f"₨0.00"


def calculate_total(price_per_unit: Union[int, float], quantity: int) -> str:
    """Calculate total in PKR.
    
    Args:
        price_per_unit: Price per unit/item
        quantity: Number of units/items
        
    Returns:
        Formatted total in PKR format
        
    Examples:
        >>> calculate_total(500, 10)
        '₨5,000.00'
        >>> calculate_total(2500, 2)
        '₨5,000'
    """
    total = float(price_per_unit) * int(quantity)
    return format_pkr(total)


def parse_pkr(amount_str: str) -> float:
    """Parse a PKR formatted string back to float.
    
    Args:
        amount_str: String like "₨1,500.00" or "₨2,500"
        
    Returns:
        Float value of the amount
        
    Examples:
        >>> parse_pkr("₨1,500.00")
        1500.0
        >>> parse_pkr("₨2,500")
        2500.0
    """
    # Remove ₨ symbol and commas
    cleaned = amount_str.replace("₨", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def get_currency_symbol() -> str:
    """Get the Pakistani Rupee currency symbol."""
    return "₨"
