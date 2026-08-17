# Test all functions and classes
_r = parse_csv_line('a,b,c')
print("actual: " + str(_r))
assert _r == ['a', 'b', 'c']

_r2 = parse_csv_line('"quoted",unquoted,"has,comma"')
print("actual: " + str(_r2))
assert _r2 == ['quoted', 'unquoted', 'has,comma']

print("TESTS PASSED")