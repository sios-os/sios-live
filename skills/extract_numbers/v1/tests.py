_r = extract_numbers("abc123def45.67ghi89")
print("actual: " + str(_r))
assert _r == [123, 45.67, 89], "Test failed"

_r = extract_numbers("no numbers here!")
print("actual: " + str(_r))
assert _r == [], "Test failed"

_r = extract_numbers("0.1 2.3 4")
print("actual: " + str(_r))
assert _r == [0.1, 2.3, 4], "Test failed"

print("TESTS PASSED")