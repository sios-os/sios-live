actual = dedupe_preserving_order([1, 2, 3, 4, 5])
print("actual: " + str(actual))
assert actual == [1, 2, 3, 4, 5]
actual = dedupe_preserving_order(['a', 'b', 'c', 'd'])
print("actual: " + str(actual))
assert actual == ['a', 'b', 'c', 'd']
actual = dedupe_preserving_order([1, 2, 3, 4, 5, 1])
print("actual: " + str(actual))
assert actual == [1, 2, 3, 4, 5]
actual = dedupe_preserving_order(['a', 'b', 'c', 'd', 'a'])
print("actual: " + str(actual))
assert actual == ['a', 'b', 'c', 'd']
print("TESTS PASSED")