_r = string_to_list("a,b,c")
print("actual: " + str(_r))
assert _r == ['a', 'b', 'c']

_r = string_to_list('  a, b , c  ')
print("actual: " + str(_r))
assert _r == ['a', 'b', 'c']

_r = string_to_list('')
print("actual: " + str(_r))
assert _r == []

print("TESTS PASSED")