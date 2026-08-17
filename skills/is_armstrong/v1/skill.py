def is_armstrong(number):
    """Check if a number is an Armstrong number."""
    digits = [int(d) for d in str(number)]
    num_digits = len(digits)
    armstrong_sum = sum(d ** num_digits for d in digits)
    return armstrong_sum == number