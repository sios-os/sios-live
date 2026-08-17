def distance_convert(value, from_unit, to_unit):
    """Converts a distance value between meters, kilometers, miles, and feet."""
    conversion_factors = {
        'm': {'m': 1, 'km': 0.001, 'mi': 0.000621371, 'ft': 3.28084},
        'km': {'m': 1000, 'km': 1, 'mi': 0.621371, 'ft': 3280.84},
        'mi': {'m': 1609.34, 'km': 1.60934, 'mi': 1, 'ft': 5280},
        'ft': {'m': 0.3048, 'km': 0.0003048, 'mi': 0.000189394, 'ft': 1}
    }
    
    if from_unit not in conversion_factors or to_unit not in conversion_factors[from_unit]:
        raise ValueError("Invalid unit conversion")
    
    return value * conversion_factors[from_unit][to_unit]