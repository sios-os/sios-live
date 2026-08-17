_r = tab_to_spaces("a\tb", 4)
print("actual: " + repr(_r))
assert _r == "a   b"

_r = tab_to_spaces("\t", 2)
print("actual: " + repr(_r))
assert _r == "  "

_r = tab_to_spaces("a\tb\nc", 3)
print("actual: " + repr(_r))
assert _r == "a  b\nc"

print("TESTS PASSED")