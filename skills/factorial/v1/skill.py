def factorial(n):
    """Compute the factorial of a non-negative integer."""
    if n < 0:
        raise ValueError("Input must be a non-negative integer")
    elif n == 0 or n == 1:
        return 1
    else:
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result