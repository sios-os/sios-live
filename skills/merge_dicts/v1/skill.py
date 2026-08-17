def merge_dicts(dict1, dict2):
    """Merge two dictionaries, with the second taking priority on conflicts."""
    merged_dict = dict1.copy()
    for key, value in dict2.items():
        merged_dict[key] = value
    return merged_dict