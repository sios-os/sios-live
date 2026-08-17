_r = checks_if_a("racecar")
print("actual: " + str(_r))
assert _r == True

_r = checks_if_a("hello")
print("actual: " + str(_r))
assert _r == False

_r = checks_if_a("")
print("actual: " + str(_r))
assert _r == True

print("TESTS PASSED")