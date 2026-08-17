# Normal case: Repeat "hello" 3 times with ", " as the separator
_r = repeat_string("hello", 3, ", ")
print("actual: " + _r)
assert _r == "hello, hello, hello"

# Edge case: Repeat "world" 1 time with no separator
_r = repeat_string("world", 1, "")
print("actual: " + _r)
assert _r == "world"

# Error case: Repeat "test" 0 times
_r = repeat_string("test", 0, ";")
print("actual: " + _r)
assert _r == ""

print("TESTS PASSED")