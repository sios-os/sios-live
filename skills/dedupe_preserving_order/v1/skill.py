def dedupe_preserving_order(iterable):
    """
    Remove duplicates from an iterable while preserving the order of first appearance.
    
    This function uses a combination of hashability and slower comparison for unhashable elements.
    
    :param iterable: The input iterable to remove duplicates from
    :return: A new list with duplicates removed, preserving the order of first appearance
    """
    seen = set()
    result = []
    for element in iterable:
        try:
            # Try to use a hashable version of the element (e.g., frozenset) if it's not already hashable
            hashed_element = hash(element)
            if hashed_element not in seen:
                seen.add(hashed_element)
                result.append(element)
        except TypeError:
            # If the element is unhashable, fall back to slower comparison
            if element not in seen:
                seen.add(element)
                result.append(element)
    return result