_r = dict_to_sorted_list({'a': 1, 'b': 2})
print("actual: " + str(_r))
assert _r == [('a', 1), ('b', 2)]

_r = dict_to_sorted_list({})
print("actual: " + str(_r))
assert _r == []

_r = dict_to_sorted_list({'c': 3, 'a': 1, 'b': 2})
print("actual: " + str(_r))
assert _r == [('a', 1), ('b', 2), ('c', 3)]

_r = dict_to_sorted_list({'apple': 50, 'banana': 30, 'cherry': 20})
print("actual: " + str(_r))
assert _r == [('apple', 50), ('banana', 30), ('cherry', 20)]

print("TESTS PASSED")