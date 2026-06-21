def format_currency(amount):
    """Formats amount as: PKR 120,000"""
    if amount is None:
        return "PKR 0"
    try:
        val = float(amount)
    except (ValueError, TypeError):
        return f"PKR {amount}"
    return f"PKR {val:,.0f}"
