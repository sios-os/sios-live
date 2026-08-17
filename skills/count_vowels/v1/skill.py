def count_vowels(s):
    """
    Count the number of vowels (a, e, i, o, u) in a string.
    
    Args:
        s (str): The input string to count vowels from.
    
    Returns:
        int: The total number of vowels found in the string.
    """
    # Convert the string to lower case for case insensitive comparison
    s = s.lower()
    
    # Initialize a counter variable to store the vowel count
    count = 0
    
    # Iterate over each character in the string
    for char in s:
        # Check if the character is a vowel (a, e, i, o, u)
        if char in 'aeiou':
            # If it's a vowel, increment the counter
            count += 1
    
    # Return the total vowel count
    return count