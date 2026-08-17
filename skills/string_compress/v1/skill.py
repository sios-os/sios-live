def string_compress(s):
    """Compresses a string by replacing consecutive characters with the character followed by the count."""
    if not s:
        return ""
    
    compressed = []
    count = 1
    
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            count += 1
        else:
            compressed.append(f"{s[i-1]}{count}")
            count = 1
    
    compressed.append(f"{s[-1]}{count}")
    
    return ''.join(compressed)