_r = kebab_to_snake("hello-world")
print("actual: " + str(_r))
assert _r == "hello_world"

_r = kebab_to_snake("one-two-three")
print("actual: " + str(_r))
assert _r == "one_two_three"

_r = kebab_to_snake("")
print("actual: " + str(_r))
assert _r == ""

print("TESTS PASSED")