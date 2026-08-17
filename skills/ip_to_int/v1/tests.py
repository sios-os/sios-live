_r = ip_to_int("192.168.1.1")
print("actual: " + str(_r))
assert _r == 3232235777, f"Expected 3232235777 but got {_r}"

_r = ip_to_int("0.0.0.0")
print("actual: " + str(_r))
assert _r == 0, f"Expected 0 but got {_r}"

try:
    _r = ip_to_int("256.256.256.256")
except ValueError as e:
    print("actual: " + str(e))
    assert str(e) == "Invalid IPv4 address", f"Expected 'Invalid IPv4 address' but got {e}"

try:
    _r = ip_to_int("192.168.1")
except ValueError as e:
    print("actual: " + str(e))
    assert str(e) == "Invalid IPv4 address", f"Expected 'Invalid IPv4 address' but got {e}"

print("TESTS PASSED")