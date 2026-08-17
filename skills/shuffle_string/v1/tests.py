import random

_r = shuffle_string("abc")
print("actual: " + _r)
assert len(_r) == 3, "Length should be the same"

_r = shuffle_string("")
print("actual: " + _r)
assert _r == "", "Empty string should remain empty"

_r = shuffle_string("a")
print("actual: " + _r)
assert _r == "a", "Single character should remain unchanged"

_r = shuffle_string("hello")
print("actual: " + _r)
assert len(_r) == 5, "Length should be the same"

_r = shuffle_string("12345")
print("actual: " + _r)
assert len(_r) == 5, "Length should be the same"

print("TESTS PASSED")