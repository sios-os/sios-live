# Normal case
_r = split_by_delimiter("apple,banana,cherry", ",")
print("actual: " + str(_r))
assert _r == ["apple", "banana", "cherry"]

# Edge case with empty string
_r = split_by_delimiter("", ",")
print("actual: " + str(_r))
assert _r == [""], "Expected an empty list when splitting an empty string"

# Error case with no delimiter found
_r = split_by_delimiter("apple banana cherry", ",")
print("actual: " + str(_r))
assert _r == ["apple banana cherry"], "Expected the original string in a single-element list if delimiter is not found"

print("TESTS PASSED")