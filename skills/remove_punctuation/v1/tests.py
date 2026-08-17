_r = remove_punctuation("Hello World")
print("actual: " + str(_r))
assert _r == "Hello World"

_r = remove_punctuation("No punctuation here")
print("actual: " + str(_r))
assert _r == "No punctuation here"

_r = remove_punctuation("Punctuation!")
print("actual: " + str(_r))
assert _r == "Punctuation"

print("TESTS PASSED")