def matrix_transpose(matrix):
    """Transposes a 2D matrix."""
    return [list(row) for row in zip(*matrix)]