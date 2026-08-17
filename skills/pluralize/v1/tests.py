_r = pluralize("cat")
print("actual: " + _r)
assert _r == "cats"

_r = pluralize("box")
print("actual: " + _r)
assert _r == "boxes"

_r = pluralize("church")
print("actual: " + _r)
assert _r == "churches"

_r = pluralize("sky")
print("actual: " + _r)
assert _r == "skies"

_r = pluralize("ses")
print("actual: " + _r)
assert _r == "seses"

print("TESTS PASSED")