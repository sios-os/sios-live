def parse_bytes(byte_str):
    """Parse a human-readable byte string like '1.5KB' or '2.3 MB' into a byte count integer."""
    units = {
        "B": 1,
        "KB": 1024,
        "MB": 1024 * 1024,
        "GB": 1024 * 1024 * 1024,
        "TB": 1024 * 1024 * 1024 * 1024
    }
    
    byte_str = byte_str.strip()
    if not byte_str or not any(c.isalpha() for c in byte_str):
        raise ValueError("Invalid byte string format")
    
    # Find the position where the number ends and the unit starts
    for i, char in enumerate(byte_str):
        if char.isalpha():
            break
    
    value = float(byte_str[:i].strip())
    unit = byte_str[i:].strip().upper()
    
    if unit not in units:
        raise ValueError(f"Unknown unit: {unit}")
    
    return int(value * units[unit])