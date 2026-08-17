_r = generate_password(8, False)
print("actual: " + str(_r))
assert _r == _r  # Replace with actual value from stdout

_r = generate_password(12, True)
print("actual: " + str(_r))
assert _r == _r  # Replace with actual value from stdout

try:
    _r = generate_password(0, False)
except ValueError as e:
    print("actual: " + str(e))
    assert str(e) == "Length must be greater than 0"
else:
    assert False, "Expected ValueError"

print("TESTS PASSED")