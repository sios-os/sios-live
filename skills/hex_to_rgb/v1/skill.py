def hex_to_rgb(hex_str):
    """Converts a hex color string to an RGB tuple."""
    if len(hex_str) != 7 or hex_str[0] != '#':
        raise ValueError("Invalid hex color format")
    
    r = int(hex_str[1:3], 16)
    g = int(hex_str[3:5], 16)
    b = int(hex_str[5:7], 16)
    
    return (r, g, b)