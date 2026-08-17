def sum_even_numbers(numbers):
    """Sum all even numbers in a list of numbers."""
    return sum(num for num in numbers if num % 2 == 0)