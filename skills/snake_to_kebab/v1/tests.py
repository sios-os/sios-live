_r = snake_to_kebab("hello_world")
print("actual: " + _r)
assert _r == "hello-world"

_r = snake_to_kebab("this_is_a_test_string")
print("actual: " + _r)
assert _r == "this-is-a-test-string"

_r = snake_to_kebab("")
print("actual: " + _r)
assert _r == ""

print("TESTS PASSED")