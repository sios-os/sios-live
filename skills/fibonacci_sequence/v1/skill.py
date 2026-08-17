def fibonacci_sequence(n):
    """Return the first n Fibonacci numbers as a list."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    fibs = [0, 1]
    for i in range(2, n):
        fibs.append(fibs[-1] + fibs[-2])
    return fibs