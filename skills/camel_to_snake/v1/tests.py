_r = camel_to_snake("camelCaseString")
print("actual: " + _r)
assert _r == "camel_case_string"

_r = camel_to_snake("thisIsATestString")
print("actual: " + _r)
assert _r == "this_is_a_test_string"

_r = camel_to_snake("singleWord")
print("actual: " + _r)
assert _r == "single_word"

_r = camel_to_snake("")
print("actual: " + _r)
assert _r == ""

print("TESTS PASSED")