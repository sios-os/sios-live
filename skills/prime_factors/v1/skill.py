def prime_factors(n):
    """Return the prime factors of a number as a list."""
    factors = []
    # Divide n by 2 to remove all even factors
    while n % 2 == 0:
        factors.append(2)
        n //= 2
    
    # Check for odd factors from 3 onwards
    factor = 3
    while factor * factor <= n:
        if n % factor == 0:
            factors.append(factor)
            n //= factor
        else:
            factor += 2
    
    # If n is a prime number greater than 2
    if n > 2:
        factors.append(n)
    
    return factors