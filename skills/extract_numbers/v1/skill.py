def extract_numbers(text):
    """Extracts all numbers from a string and returns them as a list of floats."""
    import re
    matches = re.findall(r'\d+\.\d+|\d+', text)
    return [float(match) for match in matches]