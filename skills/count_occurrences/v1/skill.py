def count_occurrences(lst):
    """Counts occurrences of each element in a list and returns a dictionary."""
    result = {}
    for item in lst:
        if item in result:
            result[item] += 1
        else:
            result[item] = 1
    return result