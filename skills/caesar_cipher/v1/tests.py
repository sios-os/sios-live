_r = caesar_cipher("hello", 3)
print("actual: " + _r)
assert _r == "khoor"

_r = caesar_cipher("Hello, World!", 5)
print("actual: " + _r)
assert _r == "Mjqqt, Btwqi!"

_r = caesar_cipher("123", 7)
print("actual: " + _r)
assert _r == "123"

print("TESTS PASSED")