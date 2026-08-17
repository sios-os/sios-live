def day_of_year_to_date(day_of_year, year):
    """Converts a day of the year and a year to a date (year, month, day)."""
    def is_leap_year(year):
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    days_in_month = [31, 28 if not is_leap_year(year) else 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    if day_of_year < 1 or day_of_year > (365 + is_leap_year(year)):
        raise ValueError("Invalid day of the year")

    month = 1
    while day_of_year > days_in_month[month - 1]:
        day_of_year -= days_in_month[month - 1]
        month += 1

    return (year, month, day_of_year)