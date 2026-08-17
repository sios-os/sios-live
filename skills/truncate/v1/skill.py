def truncate(text, max_length):
    """Truncate text to a max length, adding an ellipsis if cut."""
    if len(text) <= max_length:
        return text
    else:
        return text[:max_length] + "..."