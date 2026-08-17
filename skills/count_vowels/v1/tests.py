actual = count_vowels("Hello World")
print("actual: " + str(actual))
assert actual == 3
actual = count_vowels("")
print("actual: " + str(actual))
assert actual == 0
actual = count_vowels("aeiouAEIOU")
print("actual: " + str(actual))
assert actual == 10
print("TESTS PASSED")