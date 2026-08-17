_r = is_palindrome_str("A man a plan a canal Panama")
print("actual: " + str(_r))
assert _r == True

_r = is_palindrome_str("racecar")
print("actual: " + str(_r))
assert _r == True

_r = is_palindrome_str("hello world")
print("actual: " + str(_r))
assert _r == False

print("TESTS PASSED")