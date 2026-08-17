_r = roman_to_int("III")
print("actual: " + str(_r))
assert _r == 3

_r = roman_to_int("IV")
print("actual: " + str(_r))
assert _r == 4

_r = roman_to_int("IX")
print("actual: " + str(_r))
assert _r == 9

_r = roman_to_int("LVIII")
print("actual: " + str(_r))
assert _r == 58

_r = roman_to_int("MCMXCIV")
print("actual: " + str(_r))
assert _r == 1994

print("TESTS PASSED")