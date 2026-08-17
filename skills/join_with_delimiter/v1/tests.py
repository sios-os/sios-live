_r = join_with_delimiter(["Hello", "World"], " ")
print("actual: " + str(_r))
assert _r == "Hello World"

_r = join_with_delimiter(["apple", "banana", "cherry"], ",")
print("actual: " + str(_r))
assert _r == "apple,banana,cherry"

_r = join_with_delimiter([], ";")
print("actual: " + str(_r))
assert _r == ""

print("TESTS PASSED")