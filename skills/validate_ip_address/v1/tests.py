_r = validate_ip_address("192.168.1.1")
print("actual: " + str(_r))
assert _r == True, "Test case 1 failed"

_r = validate_ip_address("256.0.0.0")
print("actual: " + str(_r))
assert _r == False, "Test case 2 failed"

_r = validate_ip_address("192.168.1")
print("actual: " + str(_r))
assert _r == False, "Test case 3 failed"

_r = validate_ip_address("0.0.0.0")
print("actual: " + str(_r))
assert _r == True, "Test case 4 failed"

_r = validate_ip_address("192.168.1.256")
print("actual: " + str(_r))
assert _r == False, "Test case 5 failed"

_r = validate_ip_address("192.168.1.a")
print("actual: " + str(_r))
assert _r == False, "Test case 6 failed"

print("TESTS PASSED")