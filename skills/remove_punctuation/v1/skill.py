def remove_punctuation(text):
    """Remove all punctuation from a string."""
    import string
    return ''.join(char for char in text if char not in string.punctuation)