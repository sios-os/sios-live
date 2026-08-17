actual = reverse_string("")
print("actual: " + str(actual))
assert actual == ""
actual = reverse_string("a")
print("actual: " + str(actual))
assert actual == "a"
actual = reverse_string("\u0041\u0020\u0068\u0020\u006C\u006C\u0065\u006F")
print("actual: " + str(actual))
assert actual == "oell h A"
print("TESTS PASSED")