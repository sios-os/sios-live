def variance(lst):
    """Calculate the variance of a list of numbers."""
    if not lst:
        return None
    mean = sum(lst) / len(lst)
    return sum((x - mean) ** 2 for x in lst) / len(lst)