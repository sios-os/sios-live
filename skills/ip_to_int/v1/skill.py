def ip_to_int(ip):
    """Convert an IPv4 address string to an integer."""
    parts = ip.split('.')
    if len(parts) != 4:
        raise ValueError("Invalid IPv4 address")
    
    result = 0
    for part in parts:
        if not part.isdigit() or int(part) < 0 or int(part) > 255:
            raise ValueError("Invalid IPv4 address")
        
        result = (result << 8) + int(part)
    
    return result