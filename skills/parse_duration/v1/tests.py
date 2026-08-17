actual = parse_duration("2h30m")
print("actual: " + str(actual))
assert actual == 9000

actual = parse_duration("45s")
print("actual: " + str(actual))
assert actual == 45

actual = parse_duration("1h")
print("actual: " + str(actual))
assert actual == 3600

try:
    actual = parse_duration("abc")
    print("actual: " + str(actual))
except ValueError as e:
    assert str(e) == "Invalid duration string"
    
print("TESTS PASSED")