def chunk_list_size(lst, size):
    """Split a list into chunks of a given size, returning a list of lists."""
    if size <= 0:
        raise ValueError("Size must be greater than 0")
    return [lst[i:i + size] for i in range(0, len(lst), size)]