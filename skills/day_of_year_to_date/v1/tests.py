# Normal case: January 1st
_r = day_of_year_to_date(1, 2023)
print("actual:", _r)
assert _r == (2023, 1, 1)

# Edge case: December 31st of a non-leap year
_r = day_of_year_to_date(365, 2021)
print("actual:", _r)
assert _r == (2021, 12, 31)

# Edge case: December 31st of a leap year
_r = day_of_year_to_date(366, 2020)
print("actual:", _r)
assert _r == (2020, 12, 31)

# Error case: Invalid day of the year for a non-leap year
try:
    _r = day_of_year_to_date(366, 2021)
except ValueError as e:
    print("actual:", str(e))
    assert str(e) == "Invalid day of the year"

print("TESTS PASSED")