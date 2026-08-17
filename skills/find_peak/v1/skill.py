def find_peak(lst):
    """Find a peak element in a list (an element greater than its neighbors)."""
    if len(lst) == 1:
        return lst[0]
    for i in range(1, len(lst) - 1):
        if lst[i] > lst[i-1] and lst[i] > lst[i+1]:
            return lst[i]
    return max(lst[0], lst[-1])