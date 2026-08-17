_r = ordinal(1)
print("actual: " + _r)
assert _r == "1st"

_r = ordinal(2)
print("actual: " + _r)
assert _r == "2nd"

_r = ordinal(3)
print("actual: " + _r)
assert _r == "3rd"

_r = ordinal(4)
print("actual: " + _r)
assert _r == "4th"

_r = ordinal(11)
print("actual: " + _r)
assert _r == "11th"

_r = ordinal(21)
print("actual: " + _r)
assert _r == "21st"

_r = ordinal(0)
print("actual: " + _r)
assert _r == "0th"

_r = ordinal(101)
print("actual: " + _r)
assert _r == "101st"

_r = ordinal(102)
print("actual: " + _r)
assert _r == "102nd"

_r = ordinal(103)
print("actual: " + _r)
assert _r == "103rd"

_r = ordinal(104)
print("actual: " + _r)
assert _r == "104th"

_r = ordinal(111)
print("actual: " + _r)
assert _r == "111th"

_r = ordinal(112)
print("actual: " + _r)
assert _r == "112th"

print("TESTS PASSED")