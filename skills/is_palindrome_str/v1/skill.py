def is_palindrome_str(s):
    """Check if a string is a palindrome, ignoring spaces and case."""
    cleaned = s.replace(" ", "").lower()
    return cleaned == cleaned[::-1]