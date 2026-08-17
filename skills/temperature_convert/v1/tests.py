_r = temperature_convert(0, 'C', 'F')
print("actual: " + str(_r))
assert _r == 32.0

_r = temperature_convert(100, 'C', 'K')
print("actual: " + str(_r))
assert _r == 373.15

_r = temperature_convert(-40, 'F', 'C')
print("actual: " + str(_r))
assert _r == -40.0

print("TESTS PASSED")