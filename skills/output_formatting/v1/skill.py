def output_formatting(word_frequencies, unique_words):
    """Format word frequencies and unique words as JSON."""
    result = {
        "word_frequencies": word_frequencies,
        "unique_words": unique_words
    }
    return json.dumps(result)