_r = merge_dicts({'a': 1, 'b': 2}, {'b': 3, 'c': 4})
print("actual: " + str(_r))
assert _r == {'a': 1, 'b': 3, 'c': 4}

_r = merge_dicts({}, {'a': 1, 'b': 2})
print("actual: " + str(_r))
assert _r == {'a': 1, 'b': 2}

_r = merge_dicts({'a': 1, 'b': 2}, {})
print("actual: " + str(_r))
assert _r == {'a': 1, 'b': 2}

_r = merge_dicts({'a': 1, 'b': 2}, {'c': 3})
print("actual: " + str(_r))
assert _r == {'a': 1, 'b': 2, 'c': 3}

print("TESTS PASSED")