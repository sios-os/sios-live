def is_perfect_number(num):
    """Check if a number is a perfect number."""
    if num < 2:
        return False
    divisors_sum = sum(i for i in range(1, num) if num % i == 0)
    return divisors_sum == num