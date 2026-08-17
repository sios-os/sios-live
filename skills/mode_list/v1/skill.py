def mode_list(lst):
    """Returns the most common value(s) in a list of numbers. If there are ties, returns all modes."""
    from collections import Counter
    
    if not lst:
        return []
    
    count = Counter(lst)
    max_freq = max(count.values())
    modes = [num for num, freq in count.items() if freq == max_freq]
    
    return modes