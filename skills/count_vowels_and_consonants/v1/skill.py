def count_vowels_and_consonants(s):
    """Count vowels and consonants in a string, returning both counts."""
    s = s.lower()
    vowels = "aeiou"
    vowel_count = sum(1 for char in s if char in vowels)
    consonant_count = sum(1 for char in s if char.isalpha() and char not in vowels)
    return (vowel_count, consonant_count)