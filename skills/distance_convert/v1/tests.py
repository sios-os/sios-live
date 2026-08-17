# Normal case
_r = distance_convert(10, 'm', 'km')
print("actual: " + str(_r))
assert _r == 0.01

# Edge case (same unit)
_r = distance_convert(5, 'mi', 'mi')
print("actual: " + str(_r))
assert _r == 5

# Error case (invalid unit)
try:
    _r = distance_convert(100, 'm', 'yard')
except ValueError as e:
    print("caught expected error:", e)

print("TESTS PASSED")