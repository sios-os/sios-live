_r = count_substring("hello world", "o")
print("actual: " + str(_r))
assert _r == 2

_r = count_substring("hello world", "world")
print("actual: " + str(_r))
assert _r == 1

_r = count_substring("", "a")
print("actual: " + str(_r))
assert _r == 0

print("TESTS PASSED")