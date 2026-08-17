_r = count_occurrences(["apple", "banana", "apple"])
print("actual: " + str(_r))
assert _r == {"apple": 2, "banana": 1}, "Test case 1 failed"

_r = count_occurrences([])
print("actual: " + str(_r))
assert _r == {}, "Test case 2 failed"

_r = count_occurrences(["a", "b", "c", "a", "b", "a"])
print("actual: " + str(_r))
assert _r == {"a": 3, "b": 2, "c": 1}, "Test case 3 failed"

print("TESTS PASSED")