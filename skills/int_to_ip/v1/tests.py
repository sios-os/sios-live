_r = int_to_ip(167772161)
print("actual: " + str(_r))
assert _r == '10.0.0.1'

_r = int_to_ip(0)
print("actual: " + str(_r))
assert _r == '0.0.0.0'

_r = int_to_ip(4294967295)
print("actual: " + str(_r))
assert _r == '255.255.255.255'

_r = int_to_ip(1)
print("actual: " + str(_r))
assert _r == '0.0.0.1'

_r = int_to_ip(256)
print("actual: " + str(_r))
assert _r == '0.0.1.0'

_r = int_to_ip(4294967294)
print("actual: " + str(_r))
assert _r == '255.255.255.254'

print("TESTS PASSED")