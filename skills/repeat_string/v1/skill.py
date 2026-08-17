def repeat_string(s, n, separator=""):
    """Repeats a string `n` times with a specified separator between each repetition."""
    if n <= 0:
        return ""
    return (separator.join([s] * n))