_r = contains_substring("Hello World", "world")
print("actual: " + str(_r))
assert _r == True

_r = contains_substring("Python Programming", "java")
print("actual: " + str(_r))
assert _r == False

_r = contains_substring("Case INSENSITIVE", "insensitive")
print("actual: " + str(_r))
assert _r == True

print("TESTS PASSED")