_r = is_palindrome("racecar")
print("actual: " + str(_r))
assert _r == True

_r = is_palindrome("hello")
print("actual: " + str(_r))
assert _r == False

_r = is_palindrome("")
print("actual: " + str(_r))
assert _r == True

print("TESTS PASSED")