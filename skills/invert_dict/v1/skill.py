def invert_dict(d):
    """Invert a dictionary (keys become values and vice versa)."""
    return {v: k for k, v in d.items()}