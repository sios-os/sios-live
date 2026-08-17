_r = replace_all("hello world", "world", "universe")
print("actual: " + _r)
assert _r == "hello universe"

_r = replace_all("hello world", "world", "")
print("actual: " + _r)
assert _r == "hello "

try:
    _r = replace_all(123, "world", "universe")
except ValueError as e:
    print("Caught expected ValueError")

try:
    _r = replace_all("hello world", 123, "universe")
except ValueError as e:
    print("Caught expected ValueError")

try:
    _r = replace_all("hello world", "world", 123)
except ValueError as e:
    print("Caught expected ValueError")

print("TESTS PASSED")