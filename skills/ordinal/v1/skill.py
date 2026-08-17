def ordinal(n):
    """Converts a number to its ordinal string."""
    if n < 0:
        raise ValueError("Negative numbers are not supported")
    
    last_digit = abs(n) % 10
    last_two_digits = abs(n) % 100
    
    if last_two_digits in (11, 12, 13):
        return f"{n}th"
    
    if last_digit == 1:
        return f"{n}st"
    elif last_digit == 2:
        return f"{n}nd"
    elif last_digit == 3:
        return f"{n}rd"
    else:
        return f"{n}th"