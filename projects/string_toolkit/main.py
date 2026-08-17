# Step 1: reverse (reused reverse_string)
def reverse_string(s):
    """Reverses a string."""
    if not isinstance(s, str):
        raise TypeError("Input must be a string")
    return s[::-1]


# Step 2: count_words (reused count_words)
def count_words(s):
    """Count the number of words in a string."""
    return len(s.split())


# Step 3: title_case (reused title_case)
def title_case(s):
    """Converts a string to title case."""
    return s.title()


# Step 4: slugify_text (reused slugify)
def slugify(s):
    """Convert a string to a URL-safe slug: lowercase, replace any run of non-alphanumeric characters with a single hyphen, strip leading and trailing hyphens."""
    import re
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = s.strip('-')
    return s