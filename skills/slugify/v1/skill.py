def slugify(s):
    """Convert a string to a URL-safe slug: lowercase, replace any run of non-alphanumeric characters with a single hyphen, strip leading and trailing hyphens."""
    import re
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = s.strip('-')
    return s