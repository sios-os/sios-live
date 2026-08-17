def deep_flatten(lst):
    """Flattens a nested list of any depth."""
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(deep_flatten(item))
        else:
            result.append(item)
    return result