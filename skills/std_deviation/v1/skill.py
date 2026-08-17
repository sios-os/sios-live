def std_deviation(lst):
    """Calculate the standard deviation of a list of numbers."""
    if len(lst) == 0:
        return 0.0
    
    mean = sum(lst) / len(lst)
    variance = sum((x - mean) ** 2 for x in lst) / len(lst)
    return variance ** 0.5