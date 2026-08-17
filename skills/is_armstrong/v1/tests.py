_r = is_armstrong(153)
print("actual: " + str(_r))
assert _r == True, "153 should be an Armstrong number"

_r = is_armstrong(370)
print("actual: " + str(_r))
assert _r == True, "370 should be an Armstrong number"

_r = is_armstrong(9474)
print("actual: " + str(_r))
assert _r == True, "9474 should be an Armstrong number"

_r = is_armstrong(123)
print("actual: " + str(_r))
assert _r == False, "123 should not be an Armstrong number"

_r = is_armstrong(0)
print("actual: " + str(_r))
assert _r == True, "0 should be considered an Armstrong number"

print("TESTS PASSED")