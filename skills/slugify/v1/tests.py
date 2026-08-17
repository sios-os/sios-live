_r = slugify("Hello World")
print("actual: " + _r)
assert _r == "hello-world"

_r = slugify("Leading-and-trailing hyphens")
print("actual: " + _r)
assert _r == "leading-and-trailing-hyphens"

_r = slugify("")
print("actual: " + _r)
assert _r == ""

_r = slugify("123!@#")
print("actual: " + _r)
assert _r == "123"

_r = slugify("--Leading and Trailing--")
print("actual: " + _r)
assert _r == "leading-and-trailing"

print("TESTS PASSED")