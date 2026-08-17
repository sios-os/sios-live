import json

_r = output_formatting({"hello": 2, "world": 1}, ["hello", "world"])
print("actual: " + str(_r))
assert _r == '{"word_frequencies": {"hello": 2, "world": 1}, "unique_words": ["hello", "world"]}'

_r = output_formatting({"a": 3}, ["a"])
print("actual: " + str(_r))
assert _r == '{"word_frequencies": {"a": 3}, "unique_words": ["a"]}'

_r = output_formatting({}, [])
print("actual: " + str(_r))
assert _r == '{"word_frequencies": {}, "unique_words": []}'

print("TESTS PASSED")