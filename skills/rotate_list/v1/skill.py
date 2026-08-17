def rotate_list(lst, n):
    """Rotates a list by n positions (positive = right, negative = left)."""
    if not lst:
        return []
    n = n % len(lst)
    return lst[-n:] + lst[:-n]