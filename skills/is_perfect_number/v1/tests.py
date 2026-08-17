_r = is_perfect_number(6)
print("actual: " + str(_r))
assert _r == True

_r = is_perfect_number(28)
print("actual: " + str(_r))
assert _r == True

_r = is_perfect_number(496)
print("actual: " + str(_r))
assert _r == True

_r = is_perfect_number(12)
print("actual: " + str(_r))
assert _r == False

_r = is_perfect_number(1)
print("actual: " + str(_r))
assert _r == False

_r = is_perfect_number(-6)
print("actual: " + str(_r))
assert _r == False

print("TESTS PASSED")