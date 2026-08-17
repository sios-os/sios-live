_r = validate_email("example@example.com")
print("actual: " + str(_r))
assert _r == True

_r = validate_email("user.name@domain.co.uk")
print("actual: " + str(_r))
assert _r == True

_r = validate_email("user@domain")
print("actual: " + str(_r))
assert _r == False

_r = validate_email("user@.com")
print("actual: " + str(_r))
assert _r == False

_r = validate_email("@example.com")
print("actual: " + str(_r))
assert _r == False

_r = validate_email("user name@example.com")
print("actual: " + str(_r))
assert _r == False

print("TESTS PASSED")