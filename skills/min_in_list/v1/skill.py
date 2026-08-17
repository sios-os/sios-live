def min_in_list(lst):
    """Return the minimum value in a list of numbers."""
    if not lst:
        return None
    min_val = lst[0]
    for num in lst:
        if num < min_val:
            min_val = num
    return min_val