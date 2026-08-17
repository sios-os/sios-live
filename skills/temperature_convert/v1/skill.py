def temperature_convert(value, from_unit, to_unit):
    """Converts between Celsius, Fahrenheit, and Kelvin given a value, from_unit, and to_unit."""
    if from_unit == 'C':
        if to_unit == 'F':
            return (value * 9/5) + 32
        elif to_unit == 'K':
            return value + 273.15
        else:
            raise ValueError("Invalid conversion")
    elif from_unit == 'F':
        if to_unit == 'C':
            return (value - 32) * 5/9
        elif to_unit == 'K':
            return (value - 32) * 5/9 + 273.15
        else:
            raise ValueError("Invalid conversion")
    elif from_unit == 'K':
        if to_unit == 'C':
            return value - 273.15
        elif to_unit == 'F':
            return (value - 273.15) * 9/5 + 32
        else:
            raise ValueError("Invalid conversion")
    else:
        raise ValueError("Invalid unit")