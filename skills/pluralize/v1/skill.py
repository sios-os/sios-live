def pluralize(word):
    """Return the plural of an English noun."""
    if word.endswith(('s', 'x', 'z', 'ch', 'sh')):
        return word + 'es'
    elif word.endswith('y') and not word.endswith(('ay', 'oy', 'ey', 'iy', 'uy')):
        return word[:-1] + 'ies'
    else:
        return word + 's'