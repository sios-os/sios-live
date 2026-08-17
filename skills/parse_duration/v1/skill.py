def parse_duration(s):
    """
    Parse a duration string like '2h30m', '45s', or '1h' into an integer number of seconds.
    
    Args:
        s (str): A duration string with h, m, and/or s units in any combination.
        
    Returns:
        int: The number of seconds represented by the input string.
        
    Raises:
        ValueError: If the input string is invalid.
    """
    import re
    # Regular expression pattern to match one or more digits optionally followed by a unit (h/m/s)
    pattern = r"(\d+)([hms])"
    
    # Find all matches of the pattern in the input string
    matches = re.findall(pattern, s)
    
    # Initialize total seconds to 0
    total_seconds = 0
    
    # Iterate over each match and calculate its contribution to total seconds
    for value, unit in matches:
        if unit == 'h':
            total_seconds += int(value) * 3600
        elif unit == 'm':
            total_seconds += int(value) * 60
        elif unit == 's':
            total_seconds += int(value)
    
    return total_seconds