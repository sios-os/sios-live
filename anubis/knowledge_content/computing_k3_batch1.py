"""K3 advanced content for Computing specialties.

Each specialty gets multiple in-depth documents covering:
- Standards and specifications
- Patterns and best practices
- Code examples
- Common pitfalls and failure modes
- Reference material

K3 = Advanced: specialist literature, standards, datasets
"""

# Batch 1: Core programming and software engineering
COMPUTING_K3_BATCH1: dict[str, list[dict]] = {
    "computing_computer_science": [
        {
            "title": "Algorithm Complexity - Big-O Reference",
            "content": """# Algorithm Complexity Reference

## Big-O Hierarchy (best to worst)
O(1) < O(log n) < O(n) < O(n log n) < O(n^2) < O(n^3) < O(2^n) < O(n!)

## Common Algorithm Complexities

### Sorting
| Algorithm | Best | Average | Worst | Space | Stable |
|-----------|------|---------|-------|-------|--------|
| Quicksort | O(n log n) | O(n log n) | O(n^2) | O(log n) | No |
| Mergesort | O(n log n) | O(n log n) | O(n log n) | O(n) | Yes |
| Heapsort | O(n log n) | O(n log n) | O(n log n) | O(1) | No |
| Timsort | O(n) | O(n log n) | O(n log n) | O(n) | Yes |
| Insertion | O(n) | O(n^2) | O(n^2) | O(1) | Yes |
| Bubble | O(n) | O(n^2) | O(n^2) | O(1) | Yes |

### Data Structure Operations
| Structure | Access | Search | Insert | Delete |
|-----------|--------|--------|--------|--------|
| Array | O(1) | O(n) | O(n) | O(n) |
| Sorted array | O(1) | O(log n) | O(n) | O(n) |
| Linked list | O(n) | O(n) | O(1) | O(1) |
| Hash table | - | O(1) avg | O(1) avg | O(1) avg |
| BST (balanced) | O(log n) | O(log n) | O(log n) | O(log n) |
| Heap | - | O(n) | O(log n) | O(log n) |

### Graph Algorithms
- BFS: O(V + E)
- DFS: O(V + E)
- Dijkstra: O((V + E) log V) with binary heap
- Bellman-Ford: O(V * E)
- Floyd-Warshall: O(V^3)
- A*: O(E) best case, O(b^d) worst case

## NP-Complete Problems
- Traveling Salesman (decision)
- Knapsack (0/1)
- Graph coloring
- SAT (Boolean satisfiability)
- Hamiltonian path/cycle
- Subset sum

## When to Use Which
- n < 50: any algorithm works
- n < 1000: O(n^2) is fine
- n < 100000: O(n log n) needed
- n > 1000000: O(n) or O(log n) required
- n > 10^9: O(1) or approximation needed

## Pitfalls
- Hidden constants: O(n) with huge constant can be slower than O(n log n) for small n
- Amortized vs worst-case: hash table insert is O(1) amortized but O(n) worst case
- Cache effects: linear scan of array can beat binary search for small n due to cache locality
- Recursive depth: O(n) recursion can stack overflow at n ~ 1000 in Python
""",
            "tags": ["algorithms", "complexity", "big-O", "sorting", "reference"],
        },
        {
            "title": "Data Structures - Implementation Reference",
            "content": """# Data Structure Implementation Reference

## Arrays
Dynamic array (Python list, C++ vector):
- Amortized O(1) append by doubling capacity
- Random access O(1)
- Insert/delete in middle is O(n)

```python
# Dynamic array pattern
class DynamicArray:
    def __init__(self):
        self._data = [None] * 4
        self._size = 0
        self._capacity = 4

    def append(self, item):
        if self._size == self._capacity:
            self._resize(self._capacity * 2)
        self._data[self._size] = item
        self._size += 1

    def _resize(self, new_cap):
        old = self._data
        self._data = [None] * new_cap
        for i in range(self._size):
            self._data[i] = old[i]
        self._capacity = new_cap
```

## Hash Tables
- Open addressing (linear probing, quadratic probing, double hashing)
- Separate chaining (linked lists or dynamic arrays per bucket)
- Load factor: n/buckets; resize when > 0.7
- Hash function: must be deterministic, uniform, fast

```python
# Separate chaining hash table
class HashTable:
    def __init__(self, capacity=16):
        self._buckets = [[] for _ in range(capacity)]
        self._size = 0

    def _hash(self, key):
        return hash(key) % len(self._buckets)

    def put(self, key, value):
        idx = self._hash(key)
        for pair in self._buckets[idx]:
            if pair[0] == key:
                pair[1] = value
                return
        self._buckets[idx].append([key, value])
        self._size += 1
        if self._size > len(self._buckets) * 0.7:
            self._resize()

    def get(self, key):
        idx = self._hash(key)
        for k, v in self._buckets[idx]:
            if k == key:
                return v
        raise KeyError(key)

    def _resize(self):
        old = self._buckets
        self._buckets = [[] for _ in range(len(old) * 2)]
        self._size = 0
        for bucket in old:
            for k, v in bucket:
                self.put(k, v)
```

## Trees
### Binary Search Tree
- Left < root < right
- In-order traversal gives sorted order
- Balanced: AVL (height diff <= 1), Red-Black (properties)

### Trie (prefix tree)
- O(m) search/insert where m = key length
- Used for autocomplete, IP routing, dictionaries

```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True

    def search(self, word):
        node = self.root
        for ch in word:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return node.is_end

    def starts_with(self, prefix):
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return True
```

## Graphs
### Representations
- Adjacency matrix: O(V^2) space, O(1) edge lookup
- Adjacency list: O(V + E) space, O(degree) edge lookup
- Edge list: O(E) space, O(E) edge lookup

### When to use which
- Dense graph (E ~ V^2): adjacency matrix
- Sparse graph (E << V^2): adjacency list
- Need edge iteration: edge list

## Heaps
- Binary heap: complete binary tree, heap property
- Min-heap: parent <= children
- Operations: insert O(log n), extract-min O(log n), peek O(1)
- Build-heap: O(n) from unsorted array
- Python: heapq module
- Use case: priority queues, Dijkstra, A*

## Pitfalls
- Mutable default arguments in Python: `def f(x=[])` shares state
- Shallow vs deep copy: nested structures need deepcopy
- Hash table ordering: dict preserves insertion order (Python 3.7+) but not sorted
- Integer overflow: Python ints are arbitrary precision, but C/C++ need care
""",
            "tags": ["data structures", "arrays", "hash tables", "trees", "graphs", "reference"],
        },
        {
            "title": "Recursion and Dynamic Programming Patterns",
            "content": """# Recursion and Dynamic Programming Patterns

## Recursion Patterns

### Linear Recursion
```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
```

### Tail Recursion (not optimized in Python)
```python
def factorial_tail(n, acc=1):
    if n <= 1:
        return acc
    return factorial_tail(n - 1, n * acc)
```

### Divide and Conquer
```python
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
```

### Backtracking
```python
def solve_n_queens(n):
    results = []
    def backtrack(row, cols, diag1, diag2, placement):
        if row == n:
            results.append(placement[:])
            return
        for col in range(n):
            if col in cols or (row - col) in diag1 or (row + col) in diag2:
                continue
            cols.add(col); diag1.add(row - col); diag2.add(row + col)
            placement.append(col)
            backtrack(row + 1, cols, diag1, diag2, placement)
            placement.pop()
            cols.discard(col); diag1.discard(row - col); diag2.discard(row + col)
    backtrack(0, set(), set(), set(), [])
    return results
```

## Dynamic Programming Patterns

### 1. Top-Down (Memoization)
```python
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
```

### 2. Bottom-Up (Tabulation)
```python
def fib(n):
    if n < 2:
        return n
    dp = [0] * (n + 1)
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    return dp[n]
```

### 3. Space-Optimized
```python
def fib(n):
    if n < 2:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
```

## DP Problem Categories

### 1D DP
- Fibonacci, climbing stairs, house robber
- Longest increasing subsequence: O(n^2) or O(n log n) with binary search
- Coin change: O(n * amount)

### 2D DP
- Edit distance: O(m * n)
- Longest common subsequence: O(m * n)
- Matrix path (min/max sum): O(m * n)
- Knapsack 0/1: O(n * capacity)

### Interval DP
- Matrix chain multiplication
- Burst balloons
- Stone game

### Tree DP
- House robber III (tree)
- Binary tree max path sum
- Tree diameter

### State Compression DP
- Traveling salesman: O(2^n * n^2)
- Assignment problems with bitmask

## Pattern Recognition
1. Can the problem be divided into subproblems? -> DP
2. Are subproblems overlapping? -> Memoization needed
3. Optimal substructure? -> Optimization DP
4. Count subproblems? -> Counting DP
5. Boolean subproblems? -> Feasibility DP

## Pitfalls
- Stack overflow with deep recursion (Python default ~1000)
- Forgetting base case
- Off-by-one in DP table indexing
- Not considering all transitions
- Integer overflow in languages without big integers
- Memoization cache growing too large (use bounded cache)
""",
            "tags": ["recursion", "dynamic programming", "memoization", "backtracking", "patterns"],
        },
    ],
    "computing_software_engineering": [
        {
            "title": "SOLID Principles - Detailed Reference",
            "content": """# SOLID Principles

## S - Single Responsibility Principle
A class should have one reason to change.

### Violation
```python
# Bad: handles data AND persistence AND email
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def save_to_db(self):
        # database code

    def send_welcome_email(self):
        # email code

    def to_json(self):
        # serialization code
```

### Fixed
```python
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email

class UserRepository:
    def save(self, user):
        # database code

class WelcomeEmailService:
    def send(self, user):
        # email code

class UserSerializer:
    def to_json(self, user):
        # serialization code
```

## O - Open/Closed Principle
Open for extension, closed for modification.

### Violation
```python
# Bad: must modify this function to add new shapes
def area(shape):
    if shape.type == "circle":
        return 3.14 * shape.radius ** 2
    elif shape.type == "square":
        return shape.side ** 2
    # must edit here for every new shape
```

### Fixed
```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        pass

class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius
    def area(self):
        return 3.14159 * self.radius ** 2

class Square(Shape):
    def __init__(self, side):
        self.side = side
    def area(self):
        return self.side ** 2

# Adding Triangle requires no change to existing code
class Triangle(Shape):
    def __init__(self, base, height):
        self.base = base
        self.height = height
    def area(self):
        return 0.5 * self.base * self.height
```

## L - Liskov Substitution Principle
Subtypes must be substitutable for their base types.

### Violation
```python
class Bird:
    def fly(self):
        pass

class Penguin(Bird):
    def fly(self):
        raise NotImplementedError("Penguins can't fly")

# LSP violation: code expecting Bird.fly() breaks with Penguin
```

### Fixed
```python
class Bird:
    pass

class FlyingBird(Bird):
    def fly(self):
        pass

class Penguin(Bird):
    def swim(self):
        pass

# Code using FlyingBird can safely call fly()
```

## I - Interface Segregation Principle
No client should depend on methods it does not use.

### Violation
```python
class Machine:
    def print(self): pass
    def scan(self): pass
    def fax(self): pass

class SimplePrinter(Machine):
    def scan(self): raise NotImplementedError
    def fax(self): raise NotImplementedError
```

### Fixed
```python
from abc import ABC, abstractmethod

class Printer(ABC):
    @abstractmethod
    def print(self): pass

class Scanner(ABC):
    @abstractmethod
    def scan(self): pass

class Fax(ABC):
    @abstractmethod
    def fax(self): pass

class SimplePrinter(Printer):
    def print(self):
        # implementation
        pass

class MultiFunction(Printer, Scanner, Fax):
    def print(self): pass
    def scan(self): pass
    def fax(self): pass
```

## D - Dependency Inversion Principle
Depend on abstractions, not concretions.

### Violation
```python
class MySQLDatabase:
    def save(self, data): pass

class UserService:
    def __init__(self):
        self.db = MySQLDatabase()  # tight coupling

    def register(self, user):
        self.db.save(user)
```

### Fixed
```python
from abc import ABC, abstractmethod

class Database(ABC):
    @abstractmethod
    def save(self, data): pass

class MySQLDatabase(Database):
    def save(self, data): pass

class PostgreSQLDatabase(Database):
    def save(self, data): pass

class UserService:
    def __init__(self, db: Database):
        self.db = db  # depends on abstraction

    def register(self, user):
        self.db.save(user)

# Usage
service = UserService(MySQLDatabase())
service = UserService(PostgreSQLDatabase())  # easy to swap
```

## When SOLID Helps
- Large codebases with multiple developers
- Long-lived code that changes over time
- Code that needs to be tested in isolation
- Code that will be extended with new features

## When SOLID Is Overkill
- Small scripts and prototypes
- Single-use code
- Performance-critical inner loops (abstraction overhead)
- When YAGNI applies (you ain't gonna need it)
""",
            "tags": ["SOLID", "design principles", "SRP", "OCP", "LSP", "ISP", "DIP", "patterns"],
        },
        {
            "title": "Testing Strategies and Patterns",
            "content": """# Testing Strategies and Patterns

## Test Pyramid
```
        /\\
       /E2E\\      few, slow, brittle
      /------\\
     /Integr.\\    medium, moderate speed
    /----------\\
   /   Unit    \\  many, fast, isolated
  /--------------\\
```

## Unit Testing

### AAA Pattern (Arrange, Act, Assert)
```python
def test_addition():
    # Arrange
    a, b = 2, 3
    # Act
    result = add(a, b)
    # Assert
    assert result == 5
```

### Given-When-Then (BDD style)
```python
def test_user_registration():
    # Given a new user
    user = User(name="Alice", email="alice@example.com")
    # When they register
    result = register(user)
    # Then they should be saved and welcomed
    assert result.success
    assert user_exists("alice@example.com")
```

### Parametrized Tests
```python
import pytest

@pytest.mark.parametrize("input,expected", [
    ("", 0),
    ("hello", 5),
    ("hello world", 11),
    ("a b c d e", 9),
])
def test_string_length(input, expected):
    assert len(input) == expected
```

### Fixtures
```python
@pytest.fixture
def sample_db():
    db = Database(":memory:")
    db.init()
    yield db  # test runs here
    db.close()  # cleanup

def test_user_save(sample_db):
    sample_db.save(User("Alice"))
    assert sample_db.count() == 1
```

### Mocking
```python
from unittest.mock import Mock, patch, MagicMock

def test_email_sent():
    email_service = Mock()
    notifier = Notifier(email_service)
    notifier.notify("user@example.com", "Hello")
    email_service.send.assert_called_once_with(
        "user@example.com", "Hello"
    )

# Patch external calls
@patch("requests.get")
def test_api_call(mock_get):
    mock_get.return_value.json.return_value = {"status": "ok"}
    result = fetch_status()
    assert result == "ok"
```

## Integration Testing
```python
import pytest
from myapp import create_app
from myapp.db import db

@pytest.fixture
def app():
    app = create_app(testing=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_create_and_fetch_user(client):
    # Create
    resp = client.post("/users", json={"name": "Alice"})
    assert resp.status_code == 201
    user_id = resp.get_json()["id"]
    # Fetch
    resp = client.get(f"/users/{user_id}")
    assert resp.get_json()["name"] == "Alice"
```

## Property-Based Testing
```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_idempotent(lst):
    sorted_once = sorted(lst)
    sorted_twice = sorted(sorted_once)
    assert sorted_once == sorted_twice

@given(st.lists(st.integers(), min_size=1))
def test_min_le_max(lst):
    assert min(lst) <= max(lst)

@given(st.lists(st.integers()))
def test_reverse_twice_is_identity(lst):
    assert lst[::-1][::-1] == lst
```

## Test Doubbles
- **Dummy**: passed but never used
- **Stub**: returns canned answers
- **Spy**: records calls for verification
- **Mock**: pre-programmed expectations, verifies interactions
- **Fake**: working but simplified implementation (in-memory DB)

## Coverage
- Line coverage: percentage of lines executed
- Branch coverage: percentage of branches taken
- Path coverage: percentage of paths through code (usually impractical)
- Mutation coverage: percentage of mutations caught by tests

```bash
# pytest-cov
pytest --cov=myapp --cov-report=html --cov-branch
```

## TDD Cycle
1. Red: write a failing test
2. Green: write minimal code to pass
3. Refactor: improve code while tests stay green

```python
# Red
def test_fizzbuzz():
    assert fizzbuzz(3) == "Fizz"
    assert fizzbuzz(5) == "Buzz"
    assert fizzbuzz(15) == "FizzBuzz"
    assert fizzbuzz(1) == "1"

# Green (minimal)
def fizzbuzz(n):
    if n % 15 == 0: return "FizzBuzz"
    if n % 3 == 0: return "Fizz"
    if n % 5 == 0: return "Buzz"
    return str(n)

# Refactor (if needed)
```

## Common Testing Pitfalls
- Testing implementation instead of behavior
- Over-mocking: tests become brittle, test the mocks not the code
- Shared mutable state between tests
- Time-dependent tests (use freezegun or inject a clock)
- Random data without fixed seed
- I/O in unit tests (should be mocked or extracted)
- Testing too much in one test (one assertion concept per test)
- Not testing edge cases: empty, null, boundary, large, negative
""",
            "tags": ["testing", "unit tests", "TDD", "mocking", "fixtures", "patterns"],
        },
        {
            "title": "Code Review Checklist and Best Practices",
            "content": """# Code Review Checklist

## What to Review

### Correctness
- [ ] Does the code do what it claims?
- [ ] Are edge cases handled? (empty, null, zero, negative, max, min)
- [ ] Are error paths tested?
- [ ] Are there off-by-one errors?
- [ ] Are there race conditions?
- [ ] Are there resource leaks? (files, connections, memory)

### Design
- [ ] Does it follow SOLID principles?
- [ ] Is the right abstraction level used?
- [ ] Are there unnecessary abstractions? (YAGNI)
- [ ] Is the code DRY without being over-DRY?
- [ ] Are functions small and focused?
- [ ] Are classes cohesive?

### Readability
- [ ] Are names clear and meaningful?
- [ ] Is the code self-documenting?
- [ ] Are comments explaining WHY, not WHAT?
- [ ] Is the formatting consistent?
- [ ] Is the control flow clear?

### Security
- [ ] Is input validated and sanitized?
- [ ] Are there injection vulnerabilities?
- [ ] Are secrets handled properly? (not hardcoded, not logged)
- [ ] Are permissions checked?
- [ ] Are dependencies safe and up to date?

### Performance
- [ ] Are there unnecessary allocations?
- [ ] Are there N+1 query patterns?
- [ ] Is the algorithm complexity appropriate?
- [ ] Are there unnecessary synchronous operations?
- [ ] Is caching used where appropriate?

### Tests
- [ ] Are there tests for the new code?
- [ ] Do tests cover edge cases?
- [ ] Are tests meaningful (not just 100% coverage)?
- [ ] Do tests run fast?
- [ ] Are tests independent?

## Review Etiquette
- Review the code, not the person
- Ask questions instead of making demands ("Have you considered...?")
- Explain reasoning behind suggestions
- Distinguish between "must fix" and "nit" / "suggestion"
- Approve when the code is good enough, not perfect
- Don't block on style nits (use a linter)

## Anti-Patterns in Reviews
- Bikeshedding: arguing over trivial details
- LGTM without reading: rubber-stamp reviews
- Drive-by architecture changes in unrelated PRs
- Reviewing too much at once (>400 lines)
- Personal preference presented as objective requirement

## Code Smells to Flag
- Long method (>30 lines usually)
- Long parameter list (>4 params)
- Deep nesting (>3 levels)
- Duplicate code blocks
- Feature envy: method uses another class more than its own
- God class: class doing too many things
- Dead code: unused variables, methods, imports
- Magic numbers: unexplained constants
- Boolean flag arguments: usually means method does two things

## Refactoring Patterns
- Extract Method: break long method into named pieces
- Extract Class: split god class
- Rename: improve naming
- Move Method: relocate to more appropriate class
- Replace Conditional with Polymorphism: replace type checks with subclasses
- Replace Magic Number with Named Constant
- Introduce Parameter Object: group related parameters
""",
            "tags": ["code review", "checklist", "best practices", "refactoring", "patterns"],
        },
    ],
    "computing_software_architecture": [
        {
            "title": "Architectural Patterns - Detailed Reference",
            "content": """# Architectural Patterns

## Layered Architecture
```
┌─────────────────┐
│   Presentation   │  UI, controllers, views
├─────────────────┤
│    Business      │  domain logic, services
├─────────────────┤
│   Persistence    │  data access, repositories
├─────────────────┤
│     Database     │  storage
└─────────────────┘
```
- Each layer only depends on the layer directly below
- Pros: simple, well-understood, easy to test
- Cons: can become rigid; layers can leak

## Hexagonal Architecture (Ports and Adapters)
```
        ┌──────────┐
   HTTP │          │ CLI
   ───► │  Domain  │ ◄───
        │   Core   │
   SQL  │          │ Test
   ───► │          │ ◄───
        └──────────┘
```
- Domain core knows nothing about external interfaces
- Ports: interfaces defined by the domain
- Adapters: implementations of ports for specific technologies
- Pros: domain is testable in isolation; easy to swap infrastructure
- Cons: more boilerplate

```python
# Port (interface)
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    def find_by_id(self, user_id: int) -> User | None: pass
    @abstractmethod
    def save(self, user: User) -> None: pass

# Adapter (SQL implementation)
class SQLUserRepository(UserRepository):
    def __init__(self, session):
        self.session = session
    def find_by_id(self, user_id):
        return self.session.query(User).get(user_id)
    def save(self, user):
        self.session.add(user)
        self.session.commit()

# Adapter (in-memory for testing)
class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self._users = {}
    def find_by_id(self, user_id):
        return self._users.get(user_id)
    def save(self, user):
        self._users[user.id] = user

# Domain service depends on port, not adapter
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo
    def register(self, name, email):
        user = User(name=name, email=email)
        self.repo.save(user)
        return user
```

## Clean Architecture (Uncle Bob)
```
┌─────────────────────────────────┐
│        Frameworks/Drivers        │  UI, DB, frameworks
│  ┌───────────────────────────┐  │
│  │      Interface Adapters    │  │  controllers, presenters, gateways
│  │  ┌─────────────────────┐  │  │
│  │  │     Use Cases        │  │  │  application business rules
│  │  │  ┌───────────────┐  │  │  │
│  │  │  │    Entities    │  │  │  │  enterprise business rules
│  │  │  └───────────────┘  │  │  │
│  │  └─────────────────────┘  │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```
- Dependency rule: dependencies point inward only
- Inner layers don't know about outer layers
- Most testable at the center

## Microservices
- Each service owns its data
- Services communicate via network (REST, gRPC, events)
- Independent deployment
- Bounded contexts (DDD)

### When to use microservices
- Large team (>10 developers)
- Independent scaling needs per component
- Different technology stacks needed
- Clear domain boundaries exist

### When NOT to use
- Small team
- Simple domain
- Low traffic
- Early-stage startup (start monolithic, extract later)

### Microservice patterns
- API Gateway: single entry point, routing, auth
- Service Discovery: how services find each other (Consul, etcd, K8s DNS)
- Circuit Breaker: stop calling failing services (Hystrix, Resilience4j)
- Saga: distributed transaction via compensating events
- CQRS: separate read and write models
- Event Sourcing: store events as source of truth
- Strangler Fig: gradually replace monolith

## Event-Driven Architecture
```
Producer ──► Event Bus ──► Consumer A
                        ──► Consumer B
                        ──► Consumer C
```
- Producers emit events without knowing consumers
- Consumers react to events asynchronously
- Decoupled, scalable, but harder to trace

## CQRS (Command Query Responsibility Segregation)
```
Write Model ──► Command Handler ──► Event Store
                                        │
                                        ▼
Read Model ◄── Projection ◄── Events
```
- Commands change state, queries read state
- Different models for reading and writing
- Often combined with event sourcing
- Pros: independent scaling of reads/writes, optimized read models
- Cons: complexity, eventual consistency

## Choosing an Architecture
| Factor | Monolith | Microservices |
|--------|----------|---------------|
| Team size | Small-Medium | Large |
| Domain complexity | Simple | Complex |
| Deployment | Simple | Complex |
| Scaling | Whole app | Per-service |
| Latency | In-process | Network |
| Data consistency | ACID | Eventual |
| Testing | Easier | Harder |
| Observability | Easier | Harder |
""",
            "tags": ["architecture", "patterns", "hexagonal", "clean architecture", "microservices", "CQRS"],
        },
        {
            "title": "Design Patterns - Gang of Four Reference",
            "content": """# Design Patterns (Gang of Four)

## Creational Patterns

### Singleton
```python
class Database:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# Thread-safe version
import threading
class ThreadSafeSingleton:
    _instance = None
    _lock = threading.Lock()
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance
```
Use: single shared resource (DB connection, config)
Avoid: usually a code smell; prefer dependency injection

### Factory Method
```python
from abc import ABC, abstractmethod

class Animal(ABC):
    @abstractmethod
    def speak(self): pass

class Dog(Animal):
    def speak(self): return "Woof"

class Cat(Animal):
    def speak(self): return "Meow"

class AnimalFactory:
    @staticmethod
    def create(animal_type: str) -> Animal:
        if animal_type == "dog": return Dog()
        if animal_type == "cat": return Cat()
        raise ValueError(f"Unknown animal: {animal_type}")
```

### Abstract Factory
```python
class GUIFactory(ABC):
    @abstractmethod
    def create_button(self): pass
    @abstractmethod
    def create_textbox(self): pass

class WindowsFactory(GUIFactory):
    def create_button(self): return WindowsButton()
    def create_textbox(self): return WindowsTextbox()

class MacFactory(GUIFactory):
    def create_button(self): return MacButton()
    def create_textbox(self): return MacTextbox()
```

### Builder
```python
class Pizza:
    def __init__(self):
        self.size = None
        self.cheese = False
        self.pepperoni = False
        self.mushrooms = False

class PizzaBuilder:
    def __init__(self):
        self.pizza = Pizza()
    def size(self, s):
        self.pizza.size = s; return self
    def add_cheese(self):
        self.pizza.cheese = True; return self
    def add_pepperoni(self):
        self.pizza.pepperoni = True; return self
    def build(self):
        return self.pizza

pizza = PizzaBuilder().size(12).add_cheese().add_pepperoni().build()
```

### Prototype
```python
import copy
class Document:
    def clone(self):
        return copy.deepcopy(self)
```

## Structural Patterns

### Adapter
```python
class OldPrinter:
    def print_old(self, text): print(f"OLD: {text}")

class PrinterInterface(ABC):
    @abstractmethod
    def print(self, text): pass

class PrinterAdapter(PrinterInterface):
    def __init__(self, old_printer):
        self.old = old_printer
    def print(self, text):
        self.old.print_old(text)
```

### Decorator
```python
def log_calls(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}({args}, {kwargs})")
        result = func(*args, **kwargs)
        print(f"{func.__name__} returned {result}")
        return result
    return wrapper

@log_calls
def add(a, b):
    return a + b
```

### Facade
```python
class HomeTheaterFacade:
    def __init__(self, amp, dvd, projector, screen):
        self.amp = amp; self.dvd = dvd
        self.projector = projector; self.screen = screen
    def watch_movie(self, movie):
        self.screen.down()
        self.projector.on()
        self.amp.on()
        self.dvd.play(movie)
    def end_movie(self):
        self.dvd.stop()
        self.amp.off()
        self.projector.off()
        self.screen.up()
```

### Composite
```python
class Component(ABC):
    @abstractmethod
    def operation(self): pass

class Leaf(Component):
    def operation(self): return "Leaf"

class Composite(Component):
    def __init__(self):
        self.children = []
    def add(self, c): self.children.append(c)
    def operation(self):
        return "+".join(c.operation() for c in self.children)
```

### Proxy
```python
class RealImage:
    def __init__(self, filename):
        self.filename = filename
        self.load_from_disk()
    def load_from_disk(self):
        print(f"Loading {self.filename}")
    def display(self):
        print(f"Displaying {self.filename}")

class ProxyImage:
    def __init__(self, filename):
        self.filename = filename
        self.real = None
    def display(self):
        if self.real is None:
            self.real = RealImage(self.filename)
        self.real.display()
```

## Behavioral Patterns

### Observer
```python
class Subject:
    def __init__(self):
        self.observers = []
    def attach(self, o): self.observers.append(o)
    def detach(self, o): self.observers.remove(o)
    def notify(self):
        for o in self.observers:
            o.update(self)

class ConcreteSubject(Subject):
    def __init__(self):
        super().__init__()
        self.state = None
    def set_state(self, state):
        self.state = state
        self.notify()
```

### Strategy
```python
class SortStrategy(ABC):
    @abstractmethod
    def sort(self, data): pass

class QuickSort(SortStrategy):
    def sort(self, data): return sorted(data)  # simplified

class MergeSort(SortStrategy):
    def sort(self, data): return sorted(data)  # simplified

class Sorter:
    def __init__(self, strategy: SortStrategy):
        self.strategy = strategy
    def set_strategy(self, strategy):
        self.strategy = strategy
    def sort(self, data):
        return self.strategy.sort(data)
```

### Command
```python
class Command(ABC):
    @abstractmethod
    def execute(self): pass
    @abstractmethod
    def undo(self): pass

class LightOnCommand(Command):
    def __init__(self, light): self.light = light
    def execute(self): self.light.on()
    def undo(self): self.light.off()
```

### State
```python
class State(ABC):
    @abstractmethod
    def handle(self, context): pass

class RedState(State):
    def handle(self, context):
        print("Red -> Green")
        context.state = GreenState()

class GreenState(State):
    def handle(self, context):
        print("Green -> Yellow")
        context.state = YellowState()
```

### Template Method
```python
class DataProcessor(ABC):
    def process(self):
        data = self.read()
        result = self.transform(data)
        self.write(result)

    @abstractmethod
    def read(self): pass
    @abstractmethod
    def transform(self, data): pass
    @abstractmethod
    def write(self, result): pass
```

## When to Use Patterns
- Use a pattern when you have the problem it solves, not because it sounds cool
- Patterns add complexity; only use when the complexity is justified
- Most code should be simple procedural code
- Patterns emerge from refactoring, not upfront design
""",
            "tags": ["design patterns", "GoF", "singleton", "factory", "observer", "strategy", "reference"],
        },
    ],
    "computing_operating_systems": [
        {
            "title": "Linux System Programming Reference",
            "content": """# Linux System Programming Reference

## Process Management

### fork() and exec()
```c
#include <unistd.h>
#include <sys/wait.h>

pid_t pid = fork();
if (pid == 0) {
    // Child
    execlp("ls", "ls", "-la", NULL);
    _exit(1);  // only reached if exec fails
} else if (pid > 0) {
    // Parent
    int status;
    waitpid(pid, &status, 0);
} else {
    // Error
    perror("fork");
}
```

### Python: subprocess
```python
import subprocess

# Simple
result = subprocess.run(["ls", "-la"], capture_output=True, text=True)
print(result.stdout)

# With timeout
try:
    result = subprocess.run(
        ["sleep", "10"], timeout=5, capture_output=True
    )
except subprocess.TimeoutExpired:
    print("Timed out")

# Pipe
p1 = subprocess.Popen(["ls"], stdout=subprocess.PIPE)
p2 = subprocess.Popen(["grep", "py"], stdin=p1.stdout, stdout=subprocess.PIPE)
p1.stdout.close()
output = p2.communicate()[0]
```

## File I/O

### Low-level (file descriptors)
```python
import os

fd = os.open("file.txt", os.O_RDWR | os.O_CREAT, 0o644)
os.write(fd, b"Hello")
os.lseek(fd, 0, 0)  # seek to beginning
data = os.read(fd, 1024)
os.close(fd)
```

### Memory-mapped files
```python
import mmap

with open("large.bin", "r+b") as f:
    mm = mmap.mmap(f.fileno(), 0)
    # Read/write as if in memory
    print(mm[:10])
    mm[0] = 65  # write 'A'
    mm.close()
```

## Signals
```python
import signal

def handler(signum, frame):
    print(f"Received signal {signum}")

signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)

# Send signal
os.kill(pid, signal.SIGTERM)
```

## Pipes and FIFOs
```python
import os

# Anonymous pipe
r, w = os.pipe()
pid = os.fork()
if pid == 0:
    os.close(r)
    os.write(w, b"hello from child")
    os.close(w)
else:
    os.close(w)
    data = os.read(r, 1024)
    os.close(r)
    print(data)
```

## Sockets
```python
import socket

# TCP server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("127.0.0.1", 8080))
server.listen(5)

while True:
    conn, addr = server.accept()
    with conn:
        data = conn.recv(1024)
        conn.sendall(b"HTTP/1.1 200 OK\r\n\r\nHello")
```

## Threads
```python
import threading

def worker(n):
    print(f"Worker {n}")

threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
for t in threads: t.start()
for t in threads: t.join()
```

### Thread-safe queue
```python
import queue
import threading

q = queue.Queue()
def producer():
    for i in range(10):
        q.put(i)
    q.put(None)  # sentinel

def consumer():
    while True:
        item = q.get()
        if item is None: break
        print(item)
        q.task_done()

t = threading.Thread(target=consumer)
t.start()
producer()
t.join()
```

## Multiprocessing
```python
from multiprocessing import Process, Pool

def worker(n):
    return n * n

if __name__ == "__main__":
    with Pool(4) as pool:
        results = pool.map(worker, range(10))
        print(results)
```

## Async I/O
```python
import asyncio

async def fetch(url):
    reader, writer = await asyncio.open_connection(url, 80)
    writer.write(b"GET / HTTP/1.1\r\nHost: {url}\r\n\r\n")
    data = await reader.read(1024)
    writer.close()
    return data

async def main():
    results = await asyncio.gather(
        fetch("example.com"),
        fetch("example.org"),
    )

asyncio.run(main())
```

## File System Operations
```python
from pathlib import Path

# Create
Path("a/b/c").mkdir(parents=True, exist_ok=True)

# List
for p in Path(".").iterdir():
    print(p)

# Glob
for p in Path(".").rglob("*.py"):
    print(p)

# File info
stat = Path("file.txt").stat()
print(stat.st_size, stat.st_mtime)

# Permissions
Path("file.txt").chmod(0o755)
```

## Common Pitfalls
- Not closing file descriptors (use context managers)
- Zombie processes (always wait or set SIGCHLD handler)
- Deadlocks with locks (acquire in consistent order)
- Race conditions (use locks, queues, or atomic operations)
- Buffer not flushed (call flush() or use with statement)
- Signal handlers doing non-reentrant operations
- fork() only copies the calling thread; other threads are gone
""",
            "tags": ["Linux", "system programming", "processes", "threads", "sockets", "reference"],
        },
        {
            "title": "Process Scheduling and Memory Management",
            "content": """# Process Scheduling and Memory Management

## Process States
```
        ┌──────────┐
        │  Created  │
        └─────┬─────┘
              ▼
        ┌──────────┐  wait/I/O  ┌──────────┐
        │  Ready   │◄───────────│ Blocked   │
        └─────┬─────┘            └──────────┘
   scheduled   │   ▲  I/O done
              ▼   │
        ┌──────────┐
        │ Running  │
        └─────┬─────┘
              │ exit
              ▼
        ┌──────────┐
        │  Zombie   │
        └──────────┘
```

## Scheduling Algorithms

### Round Robin
- Each process gets a time quantum (e.g. 10ms)
- Preempted when quantum expires
- Fair, but context switch overhead

### Priority Scheduling
- Each process has a priority
- Highest priority runs first
- Starvation risk (low priority never runs)
- Solution: aging (priority increases over time)

### CFS (Completely Fair Scheduler, Linux)
- Each process gets fair share of CPU time
- Uses a red-black tree ordered by vruntime
- vruntime = actual runtime weighted by nice value
- Lower vruntime = scheduled next

### Multilevel Feedback Queue
- Multiple queues with different priorities
- Processes can move between queues
- I/O-bound processes get higher priority
- CPU-bound processes get demoted

## Memory Management

### Virtual Memory
- Each process has its own virtual address space
- MMU translates virtual to physical addresses
- Page table: virtual page -> physical frame
- TLB: cache for page table entries

### Paging
- Memory divided into fixed-size pages (typically 4KB)
- Page table maps virtual pages to physical frames
- Page fault: accessed page not in physical memory
  1. Hardware raises page fault exception
  2. OS finds the page on disk
  3. OS loads page into a free frame
  4. OS updates page table
  5. Instruction restarts

### Page Replacement Algorithms
- FIFO: replace oldest page (suffers Belady's anomaly)
- LRU: replace least recently used (good but expensive)
- Clock (second chance): approximation of LRU
- LFU: replace least frequently used
- Working set: keep pages used in recent window

### Thrashing
- Process spends more time paging than executing
- Caused by too many processes competing for memory
- Solution: reduce degree of multiprogramming, swap out processes

### Memory Hierarchy
```
Registers (<1ns) > L1 cache (1ns) > L2 (3ns) > L3 (10ns) 
> RAM (100ns) > SSD (100us) > HDD (10ms) > Network (ms-s)
```

### Allocation Strategies
- First fit: first hole big enough
- Best fit: smallest hole big enough (most fragmentation)
- Worst fit: largest hole (leaves large fragments)

### Buddy System
- Memory divided into power-of-2 blocks
- Split when needed, merge when freed
- Fast allocation, some internal fragmentation

### Slab Allocator (Linux)
- Pre-allocated pools for common object types
- Fast allocation/free for kernel objects
- Reduces internal fragmentation

## Inter-Process Communication

### Shared Memory
- Fastest IPC (no copying)
- Requires synchronization (semaphores, mutexes)
- POSIX: shm_open, mmap with MAP_SHARED

### Message Passing
- Slower (copying) but simpler
- Pipes, message queues, sockets

### Synchronization Primitives
- Mutex: mutual exclusion, one at a time
- Semaphore: count-based, N at a time
- Condition variable: wait for condition
- Read-write lock: multiple readers or one writer
- Spinlock: busy-wait (for very short critical sections)

### Deadlock Conditions (Coffman)
1. Mutual exclusion
2. Hold and wait
3. No preemption
4. Circular wait

All four must hold for deadlock. Break any one to prevent.

### Deadlock Prevention
- Resource ordering (break circular wait)
- Acquire all resources at once (break hold and wait)
- Banker's algorithm (safe state checking)

## Common Pitfalls
- Forgetting to release locks (use context managers)
- Lock ordering inconsistencies causing deadlock
- Busy waiting instead of blocking
- Not handling EINTR (interrupted system call)
- Assuming memory is zero-initialized (only calloc/mmap guarantees this)
- Ignoring OOM killer behavior
""",
            "tags": ["scheduling", "memory management", "virtual memory", "IPC", "deadlock", "reference"],
        },
    ],
    "computing_databases_information_systems": [
        {
            "title": "SQL Reference and Query Optimization",
            "content": """# SQL Reference and Query Optimization

## DDL (Data Definition)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role_id INTEGER REFERENCES roles(id)
);

CREATE INDEX idx_users_name ON users(name);
CREATE INDEX idx_users_created ON users(created_at DESC);

ALTER TABLE users ADD COLUMN active BOOLEAN DEFAULT true;
DROP TABLE users;
TRUNCATE TABLE users;
```

## DML (Data Manipulation)
```sql
INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com');
INSERT INTO users (name, email) VALUES ('Bob', 'bob@example.com'), ('Carol', 'carol@example.com');

UPDATE users SET name = 'Alice Smith' WHERE id = 1;
DELETE FROM users WHERE active = false;
```

## Queries
```sql
-- Basic
SELECT name, email FROM users WHERE active = true ORDER BY name;

-- Join
SELECT u.name, r.name AS role
FROM users u
JOIN roles r ON u.role_id = r.id
WHERE u.active = true;

-- Left join (include users without role)
SELECT u.name, r.name AS role
FROM users u
LEFT JOIN roles r ON u.role_id = r.id;

-- Aggregation
SELECT role_id, COUNT(*) as count, AVG(score) as avg_score
FROM users
GROUP BY role_id
HAVING COUNT(*) > 5
ORDER BY count DESC;

-- Subquery
SELECT name FROM users
WHERE id IN (SELECT user_id FROM orders WHERE total > 100);

-- EXISTS (often faster than IN)
SELECT name FROM users u
WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.user_id = u.id AND o.total > 100
);

-- Window functions
SELECT name, score,
    RANK() OVER (ORDER BY score DESC) as rank,
    AVG(score) OVER () as overall_avg,
    AVG(score) OVER (PARTITION BY role_id) as role_avg
FROM users;

-- CTE (Common Table Expression)
WITH active_users AS (
    SELECT * FROM users WHERE active = true
)
SELECT au.name, COUNT(o.id) as order_count
FROM active_users au
LEFT JOIN orders o ON au.id = o.user_id
GROUP BY au.name;

-- Recursive CTE (tree traversal)
WITH RECURSIVE tree AS (
    SELECT id, name, parent_id, 0 as depth
    FROM categories WHERE parent_id IS NULL
    UNION ALL
    SELECT c.id, c.name, c.parent_id, t.depth + 1
    FROM categories c JOIN tree t ON c.parent_id = t.id
)
SELECT * FROM tree ORDER BY depth;
```

## Indexing Strategy

### When to Index
- Columns in WHERE clauses
- Columns in JOIN conditions
- Columns in ORDER BY / GROUP BY
- Foreign keys (often auto-indexed in PostgreSQL, not MySQL)

### When NOT to Index
- Small tables
- Frequently updated columns
- Low cardinality (e.g. boolean)
- Columns rarely queried

### Index Types
- B-tree: default, good for equality and range
- Hash: equality only (PostgreSQL)
- GIN: composite values (arrays, JSON, full-text) (PostgreSQL)
- GiST: geometric, nearest neighbor (PostgreSQL)
- Partial: index subset of rows
```sql
CREATE INDEX idx_active_users ON users(email) WHERE active = true;
```
- Covering index: INCLUDE columns to avoid table lookup
```sql
CREATE INDEX idx_users_covering ON users(name) INCLUDE (email, created_at);
```

## Query Optimization

### EXPLAIN
```sql
EXPLAIN SELECT * FROM users WHERE email = 'alice@example.com';
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'alice@example.com';
```

### Common Issues
1. **Seq Scan on large table**: missing index
2. **Nested Loop with large outer**: missing index on join column
3. **Filesort**: missing index for ORDER BY
4. **Temporary table**: complex GROUP BY or DISTINCT
5. **N+1 queries**: use JOIN or batch loading instead

### Optimization Techniques
- Use covering indexes
- Avoid SELECT * (only fetch needed columns)
- Use LIMIT for pagination
- Use cursor-based pagination instead of OFFSET
```sql
-- Bad: OFFSET gets slower with deep pages
SELECT * FROM users ORDER BY id LIMIT 20 OFFSET 100000;

-- Good: cursor-based
SELECT * FROM users WHERE id > 100020 ORDER BY id LIMIT 20;
```
- Batch inserts
```sql
-- Bad
INSERT INTO t VALUES (1);
INSERT INTO t VALUES (2);

-- Good
INSERT INTO t VALUES (1), (2), (3), ...;
```
- Use prepared statements for repeated queries
- Avoid functions on indexed columns
```sql
-- Bad: index on created_at not used
SELECT * FROM users WHERE DATE(created_at) = '2024-01-01';

-- Good
SELECT * FROM users
WHERE created_at >= '2024-01-01' AND created_at < '2024-01-02';
```

## Transactions
```sql
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;
-- or ROLLBACK on error
```

### Isolation Levels
- READ UNCOMMITTED: dirty reads possible
- READ COMMITTED: no dirty reads, non-repeatable reads possible
- REPEATABLE READ: no non-repeatable reads, phantom reads possible
- SERIALIZABLE: full isolation, no anomalies

### Savepoints
```sql
BEGIN;
INSERT INTO orders ...;
SAVEPOINT after_order;
INSERT INTO items ...;
-- if items fail
ROLLBACK TO SAVEPOINT after_order;
-- retry or handle
COMMIT;
```

## Common Pitfalls
- Forgetting WHERE in UPDATE/DELETE (always test with SELECT first)
- SQL injection (use parameterized queries)
- Not handling NULL correctly (NULL != NULL, use IS NULL)
- Implicit type conversion causing index bypass
- Forgetting that COUNT(column) ignores NULLs (use COUNT(*))
- Not using transactions for multi-step operations
- Long-running transactions holding locks
""",
            "tags": ["SQL", "queries", "indexes", "optimization", "transactions", "reference"],
        },
        {
            "title": "Database Design and Normalization",
            "content": """# Database Design and Normalization

## Entity-Relationship Modeling

### Entities
- Nouns: User, Order, Product, Category
- Each entity becomes a table
- Each entity has attributes (columns)

### Relationships
- One-to-one: 1:1 (rare; often merged into one table)
- One-to-many: 1:N (most common; FK on the "many" side)
- Many-to-many: M:N (requires junction table)

### Example
```
User (1) ─── (N) Order (N) ─── (M) Product
                    │
                    └── via OrderItem (junction)
```

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) NOT NULL
);

CREATE TABLE order_items (
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (order_id, product_id)
);
```

## Normalization

### First Normal Form (1NF)
- Each column contains atomic values
- No repeating groups
- Each row is unique (has a primary key)

Violation: phone_numbers = "123,456,789"
Fix: separate table or separate columns

### Second Normal Form (2NF)
- 1NF + no partial dependency on composite key
- Every non-key column depends on the whole key

Violation: order_items(order_id, product_id, product_name)
  product_name depends only on product_id, not the full key
Fix: move product_name to products table

### Third Normal Form (3NF)
- 2NF + no transitive dependency
- Non-key columns don't depend on other non-key columns

Violation: users(id, name, zip, city, state)
  city and state depend on zip, not directly on id
Fix: separate locations(zip, city, state) table

### BCNF (Boyce-Codd)
- Stricter 3NF: every determinant is a candidate key

### When to Denormalize
- Reporting/analytics (OLAP)
- Read-heavy workloads
- When joins become too expensive
- When you need computed/cached fields
- Always document why and handle updates carefully

## Data Types

### Choosing Types
- Use the smallest type that fits (INT vs BIGINT)
- Use DECIMAL for money, never FLOAT
- Use TIMESTAMP WITH TIME ZONE for timestamps
- Use VARCHAR(n) for bounded strings, TEXT for unbounded
- Use BOOLEAN for true/false
- Use ENUM for small fixed sets
- Use JSON/JSONB for flexible schemas (PostgreSQL)

### PostgreSQL Specific
- SERIAL/BIGSERIAL: auto-increment integer
- UUID: for distributed IDs
- JSONB: binary JSON, indexable
- ARRAY: for lists (use sparingly)
- HSTORE: key-value (legacy, prefer JSONB)
- Range types: int4range, tsrange

## Constraints
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    category VARCHAR(50) NOT NULL,
    CONSTRAINT valid_category CHECK (category IN ('electronics', 'books', 'food'))
);
```

## Indexing Strategy

### Primary Keys
- Always have a primary key
- Surrogate key (auto-increment) vs natural key (e.g. email)
- Surrogate keys are usually simpler

### Foreign Keys
- PostgreSQL auto-creates indexes for PKs but NOT FKs
- Always index FK columns (used in JOINs)

### Composite Indexes
- Order matters: (last_name, first_name) helps "WHERE last_name = ?" 
  but NOT "WHERE first_name = ?"
- Put most selective column first (usually)

### Unique Constraints
```sql
ALTER TABLE users ADD CONSTRAINT unique_email UNIQUE (email);
```

## Migration Patterns

### Adding a Column
```sql
-- Safe: no table rewrite
ALTER TABLE users ADD COLUMN active BOOLEAN DEFAULT true;
```

### Backfilling Data
```sql
-- Batch backfill to avoid locking
UPDATE users SET status = 'active'
WHERE status IS NULL AND id BETWEEN 1 AND 10000;
-- repeat in batches
```

### Renaming a Column
```sql
-- 1. Add new column
ALTER TABLE users ADD COLUMN email_new VARCHAR(255);
-- 2. Backfill
UPDATE users SET email_new = email;
-- 3. Switch in application
-- 4. Drop old column later
ALTER TABLE users DROP COLUMN email;
ALTER TABLE users RENAME COLUMN email_new TO email;
```

## Common Pitfalls
- Using FLOAT for money (use DECIMAL)
- Not handling time zones (always store UTC)
- Not using transactions for multi-step operations
- Over-normalizing (5NF is rarely needed)
- Under-normalizing (data duplication, update anomalies)
- Not planning for schema evolution
- Not considering query patterns in design
- Storing computed values without keeping them updated
""",
            "tags": ["database design", "normalization", "ER modeling", "schema", "reference"],
        },
    ],
}
