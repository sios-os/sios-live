def format_bytes(byte_count):
    """Converts a byte count to a human-readable string."""
    if byte_count < 1024:
        return f"{byte_count} B"
    elif byte_count < 1024**2:
        return f"{byte_count / 1024:.1f} KB"
    elif byte_count < 1024**3:
        return f"{byte_count / (1024**2):.1f} MB"
    elif byte_count < 1024**4:
        return f"{byte_count / (1024**3):.1f} GB"
    else:
        return f"{byte_count / (1024**4):.1f} TB"