# Your module with multiple functions/classes
def parse_csv_line(line, delimiter=','):
    """Parse a CSV line handling quoted fields containing delimiters."""
    result = []
    field = ''
    quote_mode = False

    for char in line:
        if char == '"':
            quote_mode = not quote_mode
        elif char == delimiter and not quote_mode:
            result.append(strip_quotes(field))
            field = ''
        else:
            field += char

    result.append(strip_quotes(field))
    return result

def strip_quotes(field):
    """Remove surrounding quotes from a field."""
    if len(field) >= 2 and field[0] == '"' and field[-1] == '"':
        return field[1:-1]
    return field