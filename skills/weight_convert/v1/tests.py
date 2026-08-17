# Normal case
_r = weight_convert(1, 'kg', 'g')
print("actual: " + str(_r))
assert _r == 1000

# Edge case (same unit)
_r = weight_convert(5, 'lb', 'lb')
print("actual: " + str(_r))
assert _r == 5

# Error case (invalid unit)
try:
    _r = weight_convert(1, 'kg', 'm')
except ValueError as e:
    print("caught expected ValueError:", e)

print("TESTS PASSED")