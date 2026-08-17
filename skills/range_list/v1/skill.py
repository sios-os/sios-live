def range_list(lst):
    """Returns the range (max - min) of a list of numbers."""
    if not lst:
        return None
    return max(lst) - min(lst)