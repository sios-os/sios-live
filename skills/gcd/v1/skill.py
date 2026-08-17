def gcd(a, b):
    """Compute the greatest common divisor of two numbers."""
    while b:
        a, b = b, a % b
    return a