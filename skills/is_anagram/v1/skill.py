def is_anagram(str1, str2):
    """Check if two strings are anagrams of each other."""
    return sorted(str1) == sorted(str2)