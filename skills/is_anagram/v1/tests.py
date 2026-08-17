_r = is_anagram("listen", "silent")
print("actual: " + str(_r))
assert _r == True

_r = is_anagram("hello", "world")
print("actual: " + str(_r))
assert _r == False

_r = is_anagram("", "")
print("actual: " + str(_r))
assert _r == True

print("TESTS PASSED")