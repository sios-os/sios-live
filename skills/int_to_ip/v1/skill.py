def int_to_ip(n):
    """Convert an integer to an IPv4 address string."""
    if not (0 <= n <= 4294967295):  # Check if the number is within the valid range for IPv4
        raise ValueError("Number out of range for IPv4")
    
    octets = []
    for _ in range(4):
        octet = n & 0xFF  # Extract the least significant byte
        octets.append(str(octet))
        n >>= 8  # Shift right by 8 bits to process the next octet
    
    return '.'.join(reversed(octets))