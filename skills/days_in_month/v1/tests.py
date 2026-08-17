_r = days_in_month(2020, 2)
print("actual: " + str(_r))
assert _r == 29

_r = days_in_month(2021, 2)
print("actual: " + str(_r))
assert _r == 28

_r = days_in_month(2021, 4)
print("actual: " + str(_r))
assert _r == 30

_r = days_in_month(2021, 5)
print("actual: " + str(_r))
assert _r == 31

print("TESTS PASSED")