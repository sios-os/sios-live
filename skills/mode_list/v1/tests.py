# Normal case: single mode
_r = mode_list([1, 2, 2, 3, 4])
print("actual:", _r)
assert _r == [2]

# Edge case: multiple modes
_r = mode_list([1, 1, 2, 2, 3])
print("actual:", _r)
assert _r == [1, 2]

# Error case: empty list
_r = mode_list([])
print("actual:", _r)
assert _r == []

# Edge case: all elements are the same
_r = mode_list([5, 5, 5, 5])
print("actual:", _r)
assert _r == [5]

# Edge case: two modes with different frequencies
_r = mode_list([1, 2, 2, 3, 3, 4])
print("actual:", _r)
assert _r == [2, 3]

print("TESTS PASSED")