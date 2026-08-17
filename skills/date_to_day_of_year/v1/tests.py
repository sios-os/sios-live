# Normal case: January 1st, non-leap year
_r = date_to_day_of_year(2023, 1, 1)
print("actual: " + str(_r))
assert _r == 1

# Edge case: December 31st, leap year
_r = date_to_day_of_year(2024, 12, 31)
print("actual: " + str(_r))
assert _r == 366

# Error case: Invalid date (February 30th)
try:
    _r = date_to_day_of_year(2023, 2, 30)
except ValueError as e:
    print("Caught expected ValueError")
else:
    assert False, "Expected ValueError for invalid date"

print("TESTS PASSED")