_r = count_words_in_string("Hello world")
print("actual: " + str(_r))
assert _r == 2

_r = count_words_in_string("")
print("actual: " + str(_r))
assert _r == 0

_r = count_words_in_string("One")
print("actual: " + str(_r))
assert _r == 1

print("TESTS PASSED")