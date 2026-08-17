def average_list(lst):
    """Calculate and return the average of a list of numbers."""
    if not lst:
        return 0
    return sum(lst) / len(lst)