_r = rot13("Hello, World!")
print("actual: " + _r)
assert _r == "Uryyb, Jbeyq!"

_r = rot13("abc")
print("actual: " + _r)
assert _r == "nop"

_r = rot13("XYZ")
print("actual: " + _r)
assert _r == "KLM"

_r = rot13("")
print("actual: " + _r)
assert _r == ""

_r = rot13("123")
print("actual: " + _r)
assert _r == "123"

print("TESTS PASSED")