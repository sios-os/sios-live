_r = hex_to_rgb("#FFFFFF")
print("actual: " + str(_r))
assert _r == (255, 255, 255), "Expected (255, 255, 255)"

_r = hex_to_rgb("#000000")
print("actual: " + str(_r))
assert _r == (0, 0, 0), "Expected (0, 0, 0)"

_r = hex_to_rgb("#FFAABB")
print("actual: " + str(_r))
assert _r == (255, 170, 187), "Expected (255, 170, 187)"

try:
    _r = hex_to_rgb("FFFFFF")
except ValueError as e:
    print("actual: " + str(e))
    assert str(e) == "Invalid hex color format", "Expected 'Invalid hex color format'"

print("TESTS PASSED")