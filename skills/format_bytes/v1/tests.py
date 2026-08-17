_r = format_bytes(512)
print("actual: " + _r)
assert _r == "512 B"

_r = format_bytes(1536)
print("actual: " + _r)
assert _r == "1.5 KB"

_r = format_bytes(4096)
print("actual: " + _r)
assert _r == "4.0 KB"

_r = format_bytes(2**20)
print("actual: " + _r)
assert _r == "1.0 MB"

_r = format_bytes(2**30)
print("actual: " + _r)
assert _r == "1.0 GB"

_r = format_bytes(2**40)
print("actual: " + _r)
assert _r == "1.0 TB"

print("TESTS PASSED")