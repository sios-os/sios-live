_r = truncate("Hello World", 5)
print("actual: " + str(_r))
assert _r == "Hello..."

_r = truncate("Short", 10)
print("actual: " + str(_r))
assert _r == "Short"

_r = truncate("", 3)
print("actual: " + str(_r))
assert _r == ""

print("TESTS PASSED")