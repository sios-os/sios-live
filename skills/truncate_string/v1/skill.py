def truncate_string(s, max_length):
    """Truncates a string to a max length and appends an ellipsis if truncated."""
    if len(s) > max_length:
        return s[:max_length] + "..."
    return s