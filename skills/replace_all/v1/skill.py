def replace_all(s, old, new):
    """Replace all occurrences of a substring with another in a string."""
    if not isinstance(s, str) or not isinstance(old, str) or not isinstance(new, str):
        raise ValueError("All arguments must be strings")
    return s.replace(old, new)