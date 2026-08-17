_r = snake_to_camel("hello_world")
print("actual: " + _r)
assert _r == "helloWorld"

_r = snake_to_camel("this_is_a_snake_case_string")
print("actual: " + _r)
assert _r == "thisIsASnakeCaseString"

_r = snake_to_camel("")
print("actual: " + _r)
assert _r == ""

print("TESTS PASSED")