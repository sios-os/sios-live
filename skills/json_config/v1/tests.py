_r1 = load_config('{"a": 1, "b": {"c": 2}}')
print("actual: " + str(_r1))
assert _r1 == {'a': 1, 'b': {'c': 2}}

_r2 = get_value({'a': 1, 'b': {'c': 2}}, 'a')
print("actual: " + str(_r2))
assert _r2 == 1

_r3 = get_value({'a': 1, 'b': {'c': 2}}, 'b.c')
print("actual: " + str(_r3))
assert _r3 == 2

_r4 = get_value({'a': 1, 'b': {'c': 2}}, 'b.d', default=0)
print("actual: " + str(_r4))
assert _r4 == 0

_r5 = merge_configs({'a': 1, 'b': {'c': 2}}, {'b': {'d': 3}, 'e': 4})
print("actual: " + str(_r5))
assert _r5 == {'a': 1, 'b': {'c': 2, 'd': 3}, 'e': 4}

_r6 = merge_configs({'a': [1, 2]}, {'a': [3, 4]})
print("actual: " + str(_r6))
assert _r6 == {'a': [3, 4]}

print("TESTS PASSED")