_r = word_frequency("Hello, world! Hello.")
print("actual: " + str(_r))
assert _r == {'hello': 2, 'world': 1}, "Test case 1 failed"

_r = word_frequency("")
print("actual: " + str(_r))
assert _r == {}, "Test case 2 failed"

_r = word_frequency("One. Two, two! Three three three.")
print("actual: " + str(_r))
assert _r == {'one': 1, 'two': 2, 'three': 3}, "Test case 3 failed"

print("TESTS PASSED")