def snake_to_kebab(snake_str):
    """Converts a snake_case string to kebab-case."""
    return '-'.join(word for word in snake_str.split('_'))