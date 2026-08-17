_r = count_lines("")
print("actual: " + str(_r))
assert _r == 0

_r = count_lines("Hello World")
print("actual: " + str(_r))
assert _r == 1

_r = count_lines("Line1\nLine2\nLine3")
print("actual: " + str(_r))
assert _r == 3

print("TESTS PASSED")