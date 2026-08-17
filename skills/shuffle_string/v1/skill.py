def shuffle_string(s):
    """Shuffles the characters of a string randomly."""
    import random
    s_list = list(s)
    random.shuffle(s_list)
    return ''.join(s_list)