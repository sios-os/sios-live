_r = find_duplicates([1, 2, 3, 2, 4, 5, 5])
print("actual: " + str(_r))
assert _r == [2, 5], "Expected [2, 5] but got " + str(_r)

_r = find_duplicates(['a', 'b', 'c', 'd', 'a'])
print("actual: " + str(_r))
assert _r == ['a'], "Expected ['a'] but got " + str(_r)

_r = find_duplicates([1, 2, 3])
print("actual: " + str(_r))
assert _r == [], "Expected [] but got " + str(_r)

print("TESTS PASSED")