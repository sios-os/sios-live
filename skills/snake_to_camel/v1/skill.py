def snake_to_camel(snake_str):
    """Converts a snake_case string to camelCase."""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])