def date_to_day_of_year(year, month, day):
    """Converts a date (year, month, day) to the day of the year (1-366)."""
    # Check for leap year
    is_leap_year = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    
    # Days in each month for non-leap year
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    # Adjust February for leap year
    if is_leap_year:
        days_in_month[1] = 29
    
    # Validate month and day
    if month < 1 or month > 12 or day < 1 or day > days_in_month[month - 1]:
        raise ValueError("Invalid date")
    
    # Calculate the day of the year
    day_of_year = sum(days_in_month[:month - 1]) + day
    return day_of_year