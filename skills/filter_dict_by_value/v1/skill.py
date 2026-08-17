def filter_dict_by_value(dct, predicate):
    """Filter a dictionary to only entries where the value satisfies a predicate."""
    return {k: v for k, v in dct.items() if predicate(v)}