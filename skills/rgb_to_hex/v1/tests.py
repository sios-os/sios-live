_r = rgb_to_hex(255, 0, 0)
print("actual: " + str(_r))
assert _r == "#ff0000", "Test failed for RGB (255, 0, 0)"

_r = rgb_to_hex(0, 128, 0)
print("actual: " + str(_r))
assert _r == "#008000", "Test failed for RGB (0, 128, 0)"

_r = rgb_to_hex(0, 0, 255)
print("actual: " + str(_r))
assert _r == "#0000ff", "Test failed for RGB (0, 0, 255)"

_r = rgb_to_hex(128, 128, 128)
print("actual: " + str(_r))
assert _r == "#808080", "Test failed for RGB (128, 128, 128)"

_r = rgb_to_hex(0, 0, 0)
print("actual: " + str(_r))
assert _r == "#000000", "Test failed for RGB (0, 0, 0)"

_r = rgb_to_hex(255, 255, 255)
print("actual: " + str(_r))
assert _r == "#ffffff", "Test failed for RGB (255, 255, 255)"

print("TESTS PASSED")