_r = is_prime(2)
print("actual: " + str(_r))
assert _r == True, "Test failed for input 2"

_r = is_prime(17)
print("actual: " + str(_r))
assert _r == True, "Test failed for input 17"

_r = is_prime(4)
print("actual: " + str(_r))
assert _r == False, "Test failed for input 4"

_r = is_prime(1)
print("actual: " + str(_r))
assert _r == False, "Test failed for input 1"

_r = is_prime(0)
print("actual: " + str(_r))
assert _r == False, "Test failed for input 0"

_r = is_prime(-5)
print("actual: " + str(_r))
assert _r == False, "Test failed for input -5"

print("TESTS PASSED")