def sum_of_digits(number):
    """Sum the digits of an integer."""
    return sum(int(digit) for digit in str(abs(number)))