def count_lines(text):
    """Count the number of lines in a string."""
    return text.count('\n') + 1 if '\n' in text else (0 if text == '' else 1)