_r = string_compress("aabbbcccc")
print("actual: " + _r)
assert _r == "a2b3c4", f"Expected 'a2b3c4', but got {_r}"

_r = string_compress("")
print("actual: " + _r)
assert _r == "", f"Expected '', but got {_r}"

_r = string_compress("abc")
print("actual: " + _r)
assert _r == "a1b1c1", f"Expected 'a1b1c1', but got {_r}"

print("TESTS PASSED")