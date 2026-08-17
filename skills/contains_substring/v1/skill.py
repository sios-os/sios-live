def contains_substring(main_str, sub_str):
    """Check if main_str contains sub_str case-insensitively."""
    return sub_str.lower() in main_str.lower()