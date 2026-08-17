def capitalize_words(s):
    """Capitalizes the first letter of each word in a string."""
    return ' '.join(word.capitalize() for word in s.split())