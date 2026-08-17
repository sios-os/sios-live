_r = truncate_string("Hello, World!", 5)
print("actual: " + str(_r))
assert _r == "Hello..."

_r = truncate_string("Python", 10)
print("actual: " + str(_r))
assert _r == "Python"

_r = truncate_string("Short", 3)
print("actual: " + str(_r))
assert _r == "Sho..."

print("TESTS PASSED")