# Stack and Queue data structure module

class Stack:
    """Stack implementation using a list."""
    
    def __init__(self):
        self.items = []
    
    def push(self, item):
        """Add an item to the top of the stack."""
        self.items.append(item)
    
    def pop(self):
        """Remove the item from the top of the stack and return it."""
        if not self.is_empty():
            return self.items.pop()
        raise IndexError("pop from empty stack")
    
    def peek(self):
        """Return the item at the top of the stack without removing it."""
        if not self.is_empty():
            return self.items[-1]
        raise IndexError("peek from empty stack")
    
    def is_empty(self):
        """Check if the stack is empty."""
        return len(self.items) == 0

class Queue:
    """Queue implementation using a list."""
    
    def __init__(self):
        self.items = []
    
    def enqueue(self, item):
        """Add an item to the end of the queue."""
        self.items.append(item)
    
    def dequeue(self):
        """Remove the item from the front of the queue and return it."""
        if not self.is_empty():
            return self.items.pop(0)
        raise IndexError("dequeue from empty queue")
    
    def front(self):
        """Return the item at the front of the queue without removing it."""
        if not self.is_empty():
            return self.items[0]
        raise IndexError("front from empty queue")
    
    def is_empty(self):
        """Check if the queue is empty."""
        return len(self.items) == 0

def stack_queue():
    """One-line docstring."""
    pass