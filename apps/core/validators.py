import re
from django.core.exceptions import ValidationError

def format_cnic(value):
    """Normalize and format CNIC/B-Form to XXXXX-XXXXXXX-X format.
    Accepts raw 13 digits or already formatted 15-char CNIC with dashes.
    """
    if not value:
        return value

    # Strip spaces and normalize dashes
    val = str(value).strip().replace(" ", "").replace("-", "")

    if len(val) == 13 and val.isdigit():
        return f"{val[:5]}-{val[5:12]}-{val[12]}"

    return value

def validate_cnic(value):
    """Validate that the given value is a correctly formatted CNIC/B-Form."""
    if not value:
        return

    # We first clean it to verify if clean output matches regex
    cleaned_value = format_cnic(value)

    # Ensure regex matches XXXXX-XXXXXXX-X exactly
    if not re.match(r'^\d{5}-\d{7}-\d{1}$', cleaned_value):
        raise ValidationError("CNIC must follow the Pakistani format: XXXXX-XXXXXXX-X (13 digits).")
