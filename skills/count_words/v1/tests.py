_r = count_words("Hello World")
print("actual: " + str(_r))
assert _r == 2

_r = count_words("")
print("actual: " + str(_r))
assert _r == 0

_r = count_words("one two three four five")
print("actual: " + str(_r))
assert _r == 5

print("TESTS PASSED")