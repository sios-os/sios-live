_r = count_vowels_and_consonants("Hello World")
print("actual: " + str(_r))
assert _r == (3, 7), f"Expected (3, 7) but got {_r}"

_r = count_vowels_and_consonants("")
print("actual: " + str(_r))
assert _r == (0, 0), f"Expected (0, 0) but got {_r}"

_r = count_vowels_and_consonants("bcdfghjklmnpqrstvwxyz")
print("actual: " + str(_r))
assert _r == (0, 21), f"Expected (0, 21) but got {_r}"

print("TESTS PASSED")