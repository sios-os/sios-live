"""K3 advanced content for Computing specialties - Batch 4.

Covers: game_development, embedded_systems, quality_assurance, 
distributed_systems, mobile_development, humancomputer_interaction
"""

COMPUTING_K3_BATCH4: dict[str, list[dict]] = {
    "computing_game_development": [
        {
            "title": "Game Development with Godot Reference",
            "content": '''# Game Development with Godot Reference

## Godot Architecture
- Scene: a tree of nodes, saved as .tscn
- Node: the basic building block (Sprite, RigidBody, Camera, etc.)
- Script: GDScript or C# attached to a node
- Signal: event notification between nodes

## GDScript Essentials
```gdscript
extends Node2D

# Variables
var speed: float = 200.0
var health: int = 100
@export var max_health: int = 100  # editable in inspector

# Ready (called when node enters scene)
func _ready() -> void:
    print("Ready!")

# Process (called every frame)
func _process(delta: float) -> void:
    position.x += speed * delta

# Input
func _input(event: InputEvent) -> void:
    if event is InputEventKey and event.pressed:
        if event.keycode == KEY_ESCAPE:
            get_tree().quit()

# Physics process (fixed timestep)
func _physics_process(delta: float) -> void:
    var direction = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
    velocity = direction * speed
    move_and_slide()
```

## Scene Script Pattern
```gdscript
# Player.gd
extends CharacterBody2D

signal health_changed(new_health: int)
signal died

@export var speed: float = 300.0
@export var max_health: int = 100
var current_health: int

func _ready() -> void:
    current_health = max_health
    health_changed.emit(current_health)

func take_damage(amount: int) -> void:
    current_health = max(current_health - amount, 0)
    health_changed.emit(current_health)
    if current_health <= 0:
        died.emit()
        queue_free()

func _physics_process(delta: float) -> void:
    var direction = Input.get_axis("ui_left", "ui_right")
    velocity.x = direction * speed
    move_and_slide()
```

## Common Node Types
- Node2D / Node3D: base 2D/3D nodes
- Sprite2D / Sprite3D: display textures
- CharacterBody2D / CharacterBody3D: physics body for characters
- RigidBody2D / RigidBody3D: physics body with dynamics
- StaticBody2D / StaticBody3D: static physics body
- Camera2D / Camera3D: view into the scene
- AnimationPlayer: keyframe animations
- Timer: countdown timer
- AudioStreamPlayer: play audio
- Label / RichTextLabel: display text
- Button / LineEdit: UI controls

## Signals
```gdscript
# Define
signal coin_collected(amount: int)

# Emit
coin_collected.emit(10)

# Connect (in another node)
func _ready() -> void:
    player.coin_collected.connect(_on_coin_collected)

func _on_coin_collected(amount: int) -> void:
    score += amount
```

## Scene Switching
```gdscript
func change_scene(path: String) -> void:
    get_tree().change_scene_to_file(path)

# With transition
func change_scene_with_transition(path: String) -> void:
    var transition = preload("res://scenes/PortalTransition.tscn").instantiate()
    get_tree().root.add_child(transition)
    await transition.fade_out()
    get_tree().change_scene_to_file(path)
```

## Resource Management
```gdscript
# Preload (compile time)
const PlayerScene = preload("res://scenes/Player.tscn")

# Load (runtime)
var texture = load("res://assets/player.png")

# Instantiate
var player = PlayerScene.instantiate()
add_child(player)
```

## Saving/Loading
```gdscript
func save_game() -> void:
    var save_data = {
        "player_x": player.position.x,
        "player_y": player.position.y,
        "score": score,
    }
    var file = FileAccess.open("user://savegame.json", FileAccess.WRITE)
    file.store_string(JSON.stringify(save_data))
    file.close()

func load_game() -> void:
    if not FileAccess.file_exists("user://savegame.json"):
        return
    var file = FileAccess.open("user://savegame.json", FileAccess.READ)
    var data = JSON.parse_string(file.get_as_text())
    file.close()
    player.position = Vector2(data["player_x"], data["player_y"])
    score = data["score"]
```

## Performance Tips
- Use object pooling for frequently spawned/despawned objects
- Avoid creating nodes in _process
- Use call_deferred for scene modifications during physics
- Disable _process when not needed (set_process(false))
- Use SimpleCollisionShape over complex polygons
- Bake lighting for static scenes
- Use LOD for 3D models
- Profile with Godot debugger and monitor

## Common Pitfalls
- Forgetting to free nodes (memory leak)
- Modifying scene tree during physics callback (use call_deferred)
- Not using delta for movement (frame-dependent speed)
- Hardcoding paths instead of using export variables
- Not using groups for batch operations
- Overusing get_node() instead of cached references
''',
            "tags": ["Godot", "game development", "GDScript", "scenes", "reference"],
        },
    ],
    "computing_embedded_systems": [
        {
            "title": "Embedded Systems Programming Reference",
            "content": '''# Embedded Systems Programming Reference

## C for Embedded
```c
#include <stdint.h>

// Bit manipulation
#define BIT(n) (1U << (n))
#define SET_BIT(reg, n) ((reg) |= BIT(n))
#define CLEAR_BIT(reg, n) ((reg) &= ~BIT(n))
#define TOGGLE_BIT(reg, n) ((reg) ^= BIT(n))
#define READ_BIT(reg, n) ((reg) & BIT(n))

// Register access
#define GPIO_BASE 0x40020000
#define GPIO_MODER (*(volatile uint32_t*)(GPIO_BASE + 0x00))
#define GPIO_ODR   (*(volatile uint32_t*)(GPIO_BASE + 0x14))

// Set pin 5 as output
GPIO_MODER &= ~(0x3 << (5 * 2));
GPIO_MODER |= (0x1 << (5 * 2));

// Set pin 5 high
GPIO_ODR |= BIT(5);
```

## Interrupts
```c
// ISR should be short and fast
void EXTI0_IRQHandler(void) {
    if (EXTI->PR & BIT(0)) {
        // Handle interrupt
        EXTI->PR = BIT(0);  // clear pending
    }
}

// Enable interrupt
NVIC_EnableIRQ(EXTI0_IRQn);
```

## Common Peripherals

### GPIO
```c
// Input with pullup
GPIO_MODER &= ~(0x3 << (pin * 2));  // input mode
GPIO_PUPDR |= (0x1 << (pin * 2));   // pull-up
```

### UART
```c
void uart_init(uint32_t baud) {
    uint32_t divisor = SystemCoreClock / baud;
    USART1->BRR = divisor;
    USART1->CR1 = USART_CR1_TE | USART_CR1_RE | USART_CR1_UE;
}

void uart_write(char c) {
    while (!(USART1->ISR & USART_ISR_TXE));
    USART1->TDR = c;
}

char uart_read(void) {
    while (!(USART1->ISR & USART_ISR_RXNE));
    return USART1->RDR;
}
```

### I2C
```c
// Simplified I2C write
void i2c_write(uint8_t addr, uint8_t reg, uint8_t data) {
    I2C1->CR1 |= I2C_CR1_START;
    while (!(I2C1->SR1 & I2C_SR1_SB));
    I2C1->DR = addr << 1;
    while (!(I2C1->SR1 & I2C_SR1_ADDR));
    (void)I2C1->SR2;
    I2C1->DR = reg;
    while (!(I2C1->SR1 & I2C_SR1_TXE));
    I2C1->DR = data;
    while (!(I2C1->SR1 & I2C_SR1_BTF));
    I2C1->CR1 |= I2C_CR1_STOP;
}
```

### SPI
```c
void spi_write(uint8_t data) {
    while (!(SPI1->SR & SPI_SR_TXE));
    SPI1->DR = data;
    while (SPI1->SR & SPI_SR_BSY);
}

uint8_t spi_transfer(uint8_t data) {
    spi_write(data);
    while (!(SPI1->SR & SPI_SR_RXNE));
    return SPI1->DR;
}
```

## FreeRTOS Basics
```c
#include "FreeRTOS.h"
#include "task.h"
#include "semphr.h"

void led_task(void *pvParameters) {
    while (1) {
        GPIO_ODR ^= BIT(5);
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}

void sensor_task(void *pvParameters) {
    while (1) {
        read_sensor();
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

int main(void) {
    xTaskCreate(led_task, "LED", 128, NULL, 1, NULL);
    xTaskCreate(sensor_task, "Sensor", 256, NULL, 2, NULL);
    vTaskStartScheduler();
    while(1);
}
```

### Mutex
```c
SemaphoreHandle_t mutex = xSemaphoreCreateMutex();

void safe_print(const char *msg) {
    xSemaphoreTake(mutex, portMAX_DELAY);
    printf("%s\\n", msg);
    xSemaphoreGive(mutex);
}
```

## Power Management
```c
// Sleep mode
void enter_sleep(void) {
    SCB->SCR &= ~SCB_SCR_SLEEPDEEP_Msk;
    __WFI();  // wait for interrupt
}

// Deep sleep / stop mode
void enter_stop(void) {
    PWR->CR |= PWR_CR_PDDS;
    SCB->SCR |= SCB_SCR_SLEEPDEEP_Msk;
    __WFI();
}
```

## Watchdog Timer
```c
// Independent watchdog
IWDG->KR = 0xCCCC;  // enable
IWDG->KR = 0x5555;  // allow access
IWDG->PR = 4;       // prescaler
IWDG->RLR = 4095;   // reload value
IWDG->KR = 0xAAAA;  // refresh (kick)

// Must call periodically:
void watchdog_kick(void) {
    IWDG->KR = 0xAAAA;
}
```

## Common Pitfalls
- Not using volatile for hardware registers
- Race conditions between ISR and main loop
- ISRs that are too long
- Stack overflow (check with stack overflow hook)
- Not handling watchdog (system hangs)
- Floating point in ISR (slow on devices without FPU)
- Not debouncing button inputs
- Memory fragmentation with malloc/free (use static allocation)
- Not considering endianness in communication protocols
- Forgetting to enable peripheral clocks
''',
            "tags": ["embedded", "C", "microcontroller", "FreeRTOS", "interrupts", "reference"],
        },
    ],
    "computing_quality_assurance_software_testing": [
        {
            "title": "Test Automation Frameworks Reference",
            "content": '''# Test Automation Frameworks Reference

## pytest
```python
import pytest

# Basic test
def test_addition():
    assert 1 + 1 == 2

# Fixtures
@pytest.fixture
def db():
    db = Database(":memory:")
    db.create_tables()
    yield db
    db.close()

def test_user_insert(db):
    db.insert(User(name="Alice"))
    assert db.count() == 1

# Parametrized
@pytest.mark.parametrize("input,expected", [
    ("hello", 5),
    ("", 0),
    ("a b c", 5),
])
def test_length(input, expected):
    assert len(input) == expected

# Marks
@pytest.mark.slow
def test_large_dataset():
    # long test
    pass

@pytest.mark.skip(reason="not implemented")
def test_future():
    pass

@pytest.mark.xfail
def test_known_bug():
    pass

# conftest.py (shared fixtures)
import pytest

@pytest.fixture(scope="session")
def app():
    app = create_app()
    yield app
    app.cleanup()

@pytest.fixture(scope="function")
def client(app):
    return app.test_client()
```

## Mocking
```python
from unittest.mock import Mock, patch, MagicMock, call

# Basic mock
mock_db = Mock()
mock_db.query.return_value = [User("Alice")]
users = mock_db.query("SELECT * FROM users")
assert users[0].name == "Alice"
mock_db.query.assert_called_once_with("SELECT * FROM users")

# Patch
@patch("myapp.requests.get")
def test_api(mock_get):
    mock_get.return_value.json.return_value = {"status": "ok"}
    result = fetch_status()
    assert result == "ok"

# Side effects
def fake_response(url):
    if "error" in url:
        raise ConnectionError()
    return Mock(json=Mock(return_value={"ok": True}))

mock_get.side_effect = fake_response

# Assert calls
mock_send.assert_called()
mock_send.assert_called_once()
mock_send.assert_called_with("alice@example.com", "Hello")
mock_send.assert_called_once_with(...)
assert mock_send.call_count == 3
mock_send.assert_has_calls([
    call("alice@example.com", "Hello"),
    call("bob@example.com", "Hi"),
], any_order=True)
```

## Integration Testing
```python
import pytest
from testcontainers import PostgresContainer

@pytest.fixture(scope="session")
def postgres():
    with PostgresContainer("postgres:16") as pg:
        yield pg

def test_database(postgres):
    engine = create_engine(postgres.get_connection_url())
    # Run actual database tests
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
```

## Load Testing (locust)
```python
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)
    
    @task
    def view_home(self):
        self.client.get("/")
    
    @task(3)
    def view_products(self):
        self.client.get("/products")
    
    @task
    def login(self):
        self.client.post("/login", json={
            "username": "test",
            "password": "test"
        })
```

## Performance Testing
```python
import time
import pytest

def test_response_time():
    start = time.perf_counter()
    result = api_call()
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5, f"Too slow: {elapsed:.3f}s"
    assert result is not None

# Benchmarking with pytest-benchmark
def test_sort_benchmark(benchmark):
    result = benchmark(sorted, [3, 1, 4, 1, 5, 9, 2, 6])
    assert result == [1, 1, 2, 3, 4, 5, 6, 9]
```

## Coverage
```bash
# Run with coverage
pytest --cov=src --cov-report=html --cov-branch --cov-fail-under=80

# .coveragerc
[run]
source = src
omit = tests/*, */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
```

## Test Organization
```
tests/
├── unit/           # fast, isolated
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/    # slower, real dependencies
│   ├── test_api.py
│   └── test_database.py
├── e2e/            # slowest, full system
│   └── test_user_flow.py
├── conftest.py     # shared fixtures
└── pytest.ini
```

## pytest.ini
```ini
[pytest]
testpaths = tests
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow
    integration: marks as integration tests
    e2e: marks as end-to-end tests
```

## Common Pitfalls
- Tests depending on order (use unique fixtures per test)
- Shared mutable state between tests
- Not cleaning up after tests (database pollution)
- Over-mocking (testing the mock, not the code)
- Testing implementation instead of behavior
- Not testing edge cases
- Flaky tests (time, random, network)
- 100% coverage but poor tests (coverage != quality)
- Not running tests in CI
- Tests that create files but dont clean up
''',
            "tags": ["pytest", "testing", "mocking", "coverage", "automation", "reference"],
        },
    ],
    "computing_distributed_systems": [
        {
            "title": "Distributed Systems Patterns Reference",
            "content": '''# Distributed Systems Patterns Reference

## Consensus: Raft
```
Leader Election:
- Nodes start as followers
- If no heartbeat within timeout, become candidate
- Candidate requests votes; majority wins
- Leader sends heartbeats

Log Replication:
- Client sends command to leader
- Leader appends to log, sends to followers
- Once majority replicated, commit
- Leader notifies followers of commit
```

## Consistency Models

### Strong / Linearizable
- All operations appear to execute atomically in some order
- After write completes, all reads see new value
- Most expensive; requires coordination

### Sequential Consistency
- Operations appear in some sequential order
- All nodes agree on order
- No real-time ordering requirement

### Causal Consistency
- Causally related operations seen in same order by all
- Concurrent operations can be seen in different orders

### Eventual Consistency
- Given no new updates, all replicas converge
- Weakest; highest availability

## CAP Theorem
- Consistency: all nodes see same data
- Availability: every request gets response
- Partition tolerance: system works despite network splits
- Can only guarantee 2 of 3
- In practice: CP (sacrifice availability) or AP (sacrifice consistency)

## Patterns

### Circuit Breaker
```python
import time

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open

    def call(self, func, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker open")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise
```

### Retry with Exponential Backoff
```python
import time
import random

def retry_with_backoff(func, max_retries=5, base_delay=1.0, max_delay=60.0):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
            time.sleep(delay)
```

### Saga Pattern (distributed transaction)
```python
# Choreography-based saga
class OrderSaga:
    def create_order(self, order):
        # Step 1: Create order
        order = save_order(order)
        try:
            # Step 2: Reserve inventory
            reserve_inventory(order.id, order.items)
            try:
                # Step 3: Process payment
                process_payment(order.id, order.total)
            except PaymentFailed:
                # Compensate: release inventory
                release_inventory(order.id)
                raise
        except InventoryUnavailable:
            # Compensate: cancel order
            cancel_order(order.id)
            raise
```

### Idempotency Key
```python
import hashlib
from functools import wraps

processed_keys = {}  # in production, use Redis or DB

def idempotent(func):
    @wraps(func)
    def wrapper(*args, idempotency_key=None, **kwargs):
        if idempotency_key:
            key_hash = hashlib.sha256(idempotency_key.encode()).hexdigest()
            if key_hash in processed_keys:
                return processed_keys[key_hash]
        
        result = func(*args, **kwargs)
        
        if idempotency_key:
            processed_keys[key_hash] = result
        
        return result
    return wrapper
```

### Leader Election (simple)
```python
# Using a distributed lock (e.g., Redis)
import redis

r = redis.Redis()

def try_acquire_leadership(node_id, ttl=30):
    acquired = r.set("leader_lock", node_id, nx=True, ex=ttl)
    return bool(acquired)

def renew_leadership(node_id):
    # Only renew if we still hold the lock
    current = r.get("leader_lock")
    if current == node_id.encode():
        r.expire("leader_lock", 30)
        return True
    return False
```

## Message Queue Patterns

### Producer-Consumer
```python
# Producer
queue.put({"task": "process", "data": item})

# Consumer
while True:
    item = queue.get()
    try:
        process(item)
    finally:
        queue.task_done()
```

### Publish-Subscribe
```python
# Publisher
channel.publish("user.created", {"user_id": 123})

# Subscriber
channel.subscribe("user.created", handler)
```

### Dead Letter Queue
- Messages that fail processing go to DLQ
- Allows investigation without blocking main queue

## Sharding
```
# Hash-based sharding
shard = hash(key) % num_shards

# Range-based sharding
shard_0: keys 0-999
shard_1: keys 1000-1999
shard_2: keys 2000-2999

# Consistent hashing
# Minimizes data movement when shards added/removed
```

## Common Pitfalls
- Assuming network is reliable
- Not handling partial failures
- Clock skew between nodes (use logical clocks or NTP)
- Not setting timeouts (hangs forever)
- Not handling duplicate messages (idempotency)
- Distributed deadlocks
- Thundering herd (all clients retry at once)
- Not testing partition scenarios
- Assuming linearizability when you have eventual consistency
- Not monitoring queue depth and lag
''',
            "tags": ["distributed systems", "consensus", "Raft", "CAP", "patterns", "reference"],
        },
    ],
    "computing_mobile_development": [
        {
            "title": "Mobile Development Patterns Reference",
            "content": '''# Mobile Development Patterns Reference

## Flutter (Cross-platform)
```dart
// Stateful widget
class CounterWidget extends StatefulWidget {
  @override
  _CounterState createState() => _CounterState();
}

class _CounterState extends State<CounterWidget> {
  int _count = 0;

  void _increment() {
    setState(() {
      _count++;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text('Count: $_count'),
        ElevatedButton(
          onPressed: _increment,
          child: Text('Increment'),
        ),
      ],
    );
  }
}

// HTTP request
Future<User> fetchUser(int id) async {
  final response = await http.get(
    Uri.parse('https://api.example.com/users/$id'),
  );
  if (response.statusCode == 200) {
    return User.fromJson(jsonDecode(response.body));
  }
  throw Exception('Failed to load user');
}

// FutureBuilder
FutureBuilder<User>(
  future: fetchUser(123),
  builder: (context, snapshot) {
    if (snapshot.hasData) {
      return Text(snapshot.data!.name);
    } else if (snapshot.hasError) {
      return Text('Error: ${snapshot.error}');
    }
    return CircularProgressIndicator();
  },
)
```

## State Management
```dart
// Provider pattern
class UserModel extends ChangeNotifier {
  User? _user;
  User? get user => _user;

  void setUser(User user) {
    _user = user;
    notifyListeners();
  }
}

// In widget
Consumer<UserModel>(
  builder: (context, model, child) {
    return Text(model.user?.name ?? 'Not logged in');
  },
)
```

## Local Storage
```dart
// SharedPreferences (key-value)
final prefs = await SharedPreferences.getInstance();
await prefs.setString('token', 'abc123');
String? token = prefs.getString('token');

// SQLite
final db = await openDatabase('my.db');
await db.insert('users', {'name': 'Alice'});
List<Map> users = await db.query('users');
```

## React Native
```javascript
import { View, Text, Button, StyleSheet } from 'react-native';
import { useState, useEffect } from 'react';

function App() {
  const [count, setCount] = useState(0);
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch('https://api.example.com/data')
      .then(r => r.json())
      .then(setData)
      .catch(console.error);
  }, []);

  return (
    <View style={styles.container}>
      <Text>Count: {count}</Text>
      <Button title="Increment" onPress={() => setCount(count + 1)} />
      {data && <Text>{data.message}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center' },
});
```

## Navigation
```dart
// Flutter Navigator
Navigator.push(
  context,
  MaterialPageRoute(builder: (context) => DetailScreen(item: item)),
);

Navigator.pop(context);

// Named routes
Navigator.pushNamed(context, '/details', arguments: item);
```

## Performance Optimization
- Use FlatList/ListView for long lists (virtualization)
- Memoize expensive computations
- Avoid unnecessary re-renders
- Lazy load images
- Use skeleton loading states
- Minimize main thread work
- Use native modules for heavy computation
- Profile with Flutter DevTools / React Native Debugger

## Platform-Specific Code
```dart
import 'dart:io' show Platform;

if (Platform.isIOS) {
  // iOS-specific code
} else if (Platform.isAndroid) {
  // Android-specific code
}
```

## Common Pitfalls
- Not handling offline state
- Not handling loading and error states
- Memory leaks from uncleared listeners/timers
- Not testing on real devices (simulators differ)
- Ignoring platform-specific UX conventions
- Not handling keyboard appearing (layout shifts)
- Not handling safe area (notches)
- Blocking main thread with heavy computation
- Not optimizing image sizes
- Not handling app lifecycle (background/foreground)
''',
            "tags": ["mobile", "Flutter", "React Native", "state management", "reference"],
        },
    ],
    "computing_humancomputer_interaction": [
        {
            "title": "UI/UX Design Principles Reference",
            "content": '''# UI/UX Design Principles Reference

## Nielsen 10 Heuristics
1. Visibility of system status (show what is happening)
2. Match between system and real world (use familiar language)
3. User control and freedom (undo, cancel, exit)
4. Consistency and standards (follow platform conventions)
5. Error prevention (prevent mistakes before they happen)
6. Recognition rather than recall (show options, dont require memory)
7. Flexibility and efficiency (shortcuts for power users)
8. Aesthetic and minimalist design (no irrelevant info)
9. Help users recognize and recover from errors (plain language)
10. Help and documentation (when needed, findable)

## Design Principles

### Fitts Law
- Time to reach target = f(distance, size)
- Larger targets are faster to hit
- Closer targets are faster to hit
- Place important buttons at edges/corners (infinite size)

### Hicks Law
- Decision time grows with number of choices
- Minimize options at each decision point
- Group related options
- Use progressive disclosure

### Millers Law
- Working memory holds 7 +/- 2 items
- Chunk information (phone numbers: 555-123-4567)
- Group navigation items into categories

### Jakobs Law
- Users spend most time on other sites
- They expect your site to work like sites they know
- Follow conventions unless you have a very good reason not to

## Color
- Use 60-30-10 rule: 60% primary, 30% secondary, 10% accent
- Maintain contrast: 4.5:1 for normal text, 3:1 for large text
- Dont rely on color alone (also use shape/label)
- Limit palette to 3-5 colors
- Test with colorblind simulation

## Typography
- Body text: 16px minimum (web)
- Line height: 1.4-1.6 for body text
- Line length: 45-75 characters
- Use max 2-3 font families
- Hierarchy: size + weight + color
- Use rem (relative) not px for accessibility

## Layout
- Grid system: 12-column or 8pt grid
- Spacing scale: 4, 8, 12, 16, 24, 32, 48, 64
- Alignment: consistent (left, center, or right)
- Whitespace: use generously to reduce cognitive load
- Visual hierarchy: important elements larger/bolder

## Forms
- Label above input (not placeholder as label)
- Group related fields
- Show validation inline (not on submit)
- Clear error messages (what went wrong, how to fix)
- Sensible defaults
- Allow autofill
- Big touch targets (44x44pt minimum)

## Mobile UX
- Touch targets: 44x44pt minimum (Apple), 48x48dp (Google)
- Thumb zone: place important actions in reach of thumb
- Bottom navigation for main sections
- Swipe gestures for common actions
- Pull to refresh (familiar pattern)
- Handle keyboard (dont cover inputs)

## Accessibility
- Semantic HTML (screen readers)
- Keyboard navigation (tab order)
- Focus indicators (visible)
- Alt text for images
- ARIA labels where needed
- Color contrast: 4.5:1 (normal), 3:1 (large)
- Dont rely on color alone
- Test with screen reader (NVDA, VoiceOver)

## Common Pitfalls
- Too many CTAs (call to action) competing
- Mystery meat navigation (unclear icons)
- Autoplaying media
- Intrusive popups
- Tiny touch targets
- Low contrast text
- Inconsistent spacing
- No loading/empty/error states
- No feedback on user actions
- Forms that clear on error
''',
            "tags": ["UI", "UX", "design", "accessibility", "heuristics", "reference"],
        },
    ],
}
