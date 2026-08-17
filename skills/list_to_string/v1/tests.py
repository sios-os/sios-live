_r = list_to_string(['apple', 'banana', 'cherry'])
print("actual: " + str(_r))
assert _r == "apple,banana,cherry"

_r = list_to_string([1, 2, 3, 4])
print("actual: " + str(_r))
assert _r == "1,2,3,4"

_r = list_to_string([])
print("actual: " + str(_r))
assert _r == ""

print("TESTS PASSED")