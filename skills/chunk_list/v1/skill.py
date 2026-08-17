def chunk_list(lst, size):
    """Split a list into chunks of a given size. Return a list of lists. The last chunk may be smaller than size. If size <= 0, raise ValueError. Empty input list returns empty list."""
    if size <= 0:
        raise ValueError("Size must be greater than 0")
    return [lst[i:i + size] for i in range(0, len(lst), size)]