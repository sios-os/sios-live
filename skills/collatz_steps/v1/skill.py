def collatz_steps(n):
    """Return the number of Collatz conjecture steps to reach 1."""
    if n <= 0:
        raise ValueError("Input must be a positive integer.")
    steps = 0
    while n != 1:
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        steps += 1
    return steps