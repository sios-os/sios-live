def decimal_to_binary(decimal):
    """Convert a decimal integer to its binary string representation."""
    if decimal == 0:
        return "0"
    binary = ""
    while decimal > 0:
        binary = str(decimal % 2) + binary
        decimal //= 2
    return binary