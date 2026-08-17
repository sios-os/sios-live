import time

_r = time_ago(time.time() - 180)
print("actual: " + _r)
assert _r == "3 minutes ago"

_r = time_ago(time.time() - 7200)
print("actual: " + _r)
assert _r == "2 hours ago"

try:
    _r = time_ago(time.time() + 180)
except ValueError as e:
    print("actual: " + str(e))
    assert str(e) == "Future timestamp"

print("TESTS PASSED")