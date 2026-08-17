def generate_password(length=8, use_special_chars=False):
    """Generate a random password of a given length with optional special characters."""
    import string
    import random

    if length <= 0:
        raise ValueError("Length must be greater than 0")

    characters = string.ascii_letters + string.digits
    if use_special_chars:
        characters += string.punctuation

    return ''.join(random.choice(characters) for _ in range(length))