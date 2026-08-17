_r = title_case("hello world")
print("actual: " + str(_r))
assert _r == "Hello World"

_r = title_case("this is a test")
print("actual: " + str(_r))
assert _r == "This Is A Test"

_r = title_case("")
print("actual: " + str(_r))
assert _r == ""

print("TESTS PASSED")