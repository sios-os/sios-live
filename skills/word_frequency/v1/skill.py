def word_frequency(text):
    """Count the frequency of each lowercase word in a string, ignoring punctuation."""
    import re
    from collections import Counter

    # Remove punctuation and convert to lowercase
    cleaned_text = re.sub(r'[^\w\s]', '', text).lower()
    
    # Split the text into words
    words = cleaned_text.split()
    
    # Count the frequency of each word
    freq_dict = dict(Counter(words))
    
    return freq_dict