_r = is_leap_year(2000)
print("actual: " + str(_r))
assert _r == True, "2000 should be a leap year"

_r = is_leap_year(1900)
print("actual: " + str(_r))
assert _r == False, "1900 should not be a leap year"

_r = is_leap_year(2024)
print("actual: " + str(_r))
assert _r == True, "2024 should be a leap year"

_r = is_leap_year(2023)
print("actual: " + str(_r))
assert _r == False, "2023 should not be a leap year"

print("TESTS PASSED")