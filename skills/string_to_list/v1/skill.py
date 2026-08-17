def string_to_list(s):
    """Split a comma-separated string into a list of trimmed strings."""
    return [item.strip() for item in s.split(',') if item.strip()]