_r = zip_dicts(['a', 'b', 'c'], [1, 2, 3])
print("actual: " + str(_r))
assert _r == {'a': 1, 'b': 2, 'c': 3}

_r = zip_dicts([], [])
print("actual: " + str(_r))
assert _r == {}

_r = zip_dicts(['x'], [42])
print("actual: " + str(_r))
assert _r == {'x': 42}

try:
    _r = zip_dicts([1, 2], [3])
except ValueError as e:
    print("actual: " + str(e))
    assert str(e) == "Values list is shorter than keys list"

print("TESTS PASSED")