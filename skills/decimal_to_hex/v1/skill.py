def decimal_to_hex(decimal):
    """Convert a decimal integer to a hexadecimal string."""
    if decimal == 0:
        return "0"
    hex_chars = "0123456789ABCDEF"
    hex_string = ""
    while decimal > 0:
        remainder = decimal % 16
        hex_string = hex_chars[remainder] + hex_string
        decimal //= 16
    return hex_string