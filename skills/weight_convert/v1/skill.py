def weight_convert(value, from_unit, to_unit):
    """Converts between kilograms, grams, pounds, and ounces."""
    conversion_factors = {
        'kg': {'kg': 1, 'g': 1000, 'lb': 2.20462, 'oz': 35.274},
        'g': {'kg': 0.001, 'g': 1, 'lb': 0.00220462, 'oz': 0.035274},
        'lb': {'kg': 0.453592, 'g': 453.592, 'lb': 1, 'oz': 16},
        'oz': {'kg': 0.0283495, 'g': 28.3495, 'lb': 0.0625, 'oz': 1}
    }
    
    if from_unit not in conversion_factors or to_unit not in conversion_factors[from_unit]:
        raise ValueError("Invalid unit conversion")
    
    return value * conversion_factors[from_unit][to_unit]