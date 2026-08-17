# Test all functions and classes
_r = Stack()
_r.push(1)
_r.push(2)
_r.push(3)
print("actual: " + str(_r.pop()))
assert _r.pop() == 2
assert _r.peek() == 1
assert not _r.is_empty()

_r2 = Queue()
_r2.enqueue('a')
_r2.enqueue('b')
_r2.enqueue('c')
print("actual: " + str(_r2.dequeue()))
assert _r2.dequeue() == 'b'
assert _r2.front() == 'c'
assert not _r2.is_empty()

obj = Stack()
obj.push(1)
obj.push(2)
_r3 = obj.pop()
print("actual: " + str(_r3))
assert _r3 == 2

obj2 = Queue()
obj2.enqueue('a')
obj2.enqueue('b')
_r4 = obj2.dequeue()
print("actual: " + str(_r4))
assert _r4 == 'a'

print("TESTS PASSED")