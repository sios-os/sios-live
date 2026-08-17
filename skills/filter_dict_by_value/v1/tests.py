_r = filter_dict_by_value({'a': 1, 'b': 2, 'c': 3}, lambda x: x > 1)
print("actual: " + str(_r))
assert _r == {'b': 2, 'c': 3}

_r = filter_dict_by_value({'x': 5, 'y': 10, 'z': 15}, lambda x: x % 2 == 0)
print("actual: " + str(_r))
assert _r == {'y': 10}

_r = filter_dict_by_value({'p': 'apple', 'q': 'banana', 'r': 'cherry'}, lambda x: len(x) > 5)
print("actual: " + str(_r))
assert _r == {'q': 'banana', 'r': 'cherry'}

print("TESTS PASSED")