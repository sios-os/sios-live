_r = capitalize_words("hello world")
print("actual: " + _r)
assert _r == "Hello World"

_r = capitalize_words("this is a test")
print("actual: " + _r)
assert _r == "This Is A Test"

_r = capitalize_words("")
print("actual: " + _r)
assert _r == ""

print("TESTS PASSED")