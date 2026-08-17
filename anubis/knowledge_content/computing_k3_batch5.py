"""K3 advanced content for Computing specialties - Batch 5.

Covers the remaining 13 specialties:
- computer_engineering, speech_audio, digital_forensics, privacy_engineering
- highperformance_computing, computer_graphics, firmware, robotics
- accessibility_engineering, it_support_administration, technology_project_management
- quantum_computing, ai_safety_evaluation
"""

COMPUTING_K3_BATCH5: dict[str, list[dict]] = {
    "computing_computer_engineering": [
        {
            "title": "CPU Architecture and Pipeline Reference",
            "content": '''# CPU Architecture Reference

## Pipeline Stages
1. Fetch: get instruction from memory/instruction cache
2. Decode: interpret opcode and operands
3. Execute: ALU operation
4. Memory: load/store if needed
5. Writeback: write result to register

## Hazards
- Data hazard: instruction depends on result of previous (RAW, WAW, WAR)
  - Fix: forwarding/bypassing, pipeline stall (bubble)
- Control hazard: branch changes flow, fetched instructions wrong
  - Fix: branch prediction, speculative execution, delay slot
- Structural hazard: two instructions need same hardware
  - Fix: duplicate hardware, stall

## Cache Hierarchy
```
L1: 32-64KB, 1-3 cycles, per-core
L2: 256KB-1MB, 10-15 cycles, per-core
L3: 4-32MB, 30-50 cycles, shared
RAM: GBs, 100-300 cycles
```

### Cache Policies
- Write-through: write to cache and memory simultaneously
- Write-back: write to cache only, flush to memory later
- Write-allocate: on miss, load block then write
- No-write-allocate: on miss, write directly to memory

### Cache Mapping
- Direct-mapped: each block maps to one cache line (simple, conflicts)
- Fully associative: block can go anywhere (complex, expensive)
- Set-associative: block maps to a set of N lines (compromise)

## Memory Models
- Sequential consistency: all operations in program order
- TSO (Total Store Order): x86, allows store-load reordering
- Relaxed: ARM/RISC-V, allows most reorderings

## Instruction Set Architectures
- x86-64: CISC, variable length, complex
- ARM64/AArch64: RISC, fixed 32-bit, simpler
- RISC-V: open ISA, modular, extensible
- MIPS: classic RISC, educational

## Performance Formula
- CPU Time = Instruction Count x CPI x Clock Cycle Time
- CPI = Cycles Per Instruction
- Amdahl: Speedup = 1 / ((1-p) + p/s) where p is parallel fraction, s is speedup

## Common Pitfalls
- Cache thrashing (working set larger than cache)
- False sharing (different variables on same cache line)
- Branch misprediction (unpredictable branches)
- Memory-bound vs compute-bound (know which)
- Not considering SIMD for parallelizable work
''',
            "tags": ["CPU", "architecture", "pipeline", "cache", "reference"],
        },
    ],
    "computing_speech_audio_processing": [
        {
            "title": "Audio Processing and Speech Recognition Reference",
            "content": '''# Audio Processing Reference

## Digital Audio Fundamentals
- Sample rate: 8000 (phone), 16000 (ASR), 44100 (CD), 48000 (pro) Hz
- Bit depth: 16-bit (CD), 24-bit (pro), 32-bit float
- Channels: mono (1), stereo (2), 5.1 (6)
- Nyquist: max frequency = sample_rate / 2

## librosa Basics
```python
import librosa
import numpy as np

# Load
y, sr = librosa.load("audio.wav", sr=16000)

# Duration
duration = len(y) / sr

# Spectrogram
S = librosa.stft(y)
S_db = librosa.amplitude_to_db(np.abs(S))

# Mel spectrogram
mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
mel_db = librosa.power_to_db(mel)

# MFCC
mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

# Pitch
f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=80, fmax=400)

# Tempo
tempo, beats = librosa.beat.tempo(y=y, sr=sr)
```

## Speech Recognition (Whisper)
```python
import whisper

model = whisper.load_model("base")
result = model.transcribe("audio.wav")
print(result["text"])
print(result["language"])

# With timestamps
for segment in result["segments"]:
    print(f"[{segment['start']:.1f}-{segment['end']:.1f}] {segment['text']}")
```

## Text-to-Speech
```python
# pyttsx3 (offline, simple)
import pyttsx3
engine = pyttsx3.init()
engine.say("Hello, world!")
engine.runAndWait()

# Coqui TTS (neural)
from TTS.api import TTS
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
tts.tts_to_file("Hello world", file_path="output.wav")
```

## Audio Effects
```python
import numpy as np

# Normalize
def normalize(y):
    return y / np.max(np.abs(y))

# Noise gate
def noise_gate(y, threshold=0.01):
    y[np.abs(y) < threshold] = 0
    return y

# Fade in/out
def fade(y, fade_samples=1000):
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    y[:fade_samples] *= fade_in
    y[-fade_samples:] *= fade_out
    return y
```

## Common Pitfalls
- Wrong sample rate (resample before processing)
- Not normalizing audio levels
- Clipping (amplitude > 1.0)
- Forgetting to convert stereo to mono
- Not handling silence at start/end
- Using FFT size too small for low frequencies
''',
            "tags": ["audio", "speech", "Whisper", "librosa", "MFCC", "reference"],
        },
    ],
    "computing_digital_forensics": [
        {
            "title": "Digital Forensics Procedures Reference",
            "content": '''# Digital Forensics Reference

## Evidence Handling
1. Identify: determine what evidence exists
2. Preserve: prevent alteration (write blocker, hash)
3. Collect: acquire copy (forensic image)
4. Analyze: examine the copy
5. Report: document findings

## Disk Imaging
```bash
# Create forensic image (dd)
dcfldd if=/dev/sda of=disk.img hash=sha256 hashwindow=1M

# Or using ewf (Expert Witness Format)
ewfacquire /dev/sda

# Verify integrity
sha256sum disk.img
# Compare with hash recorded during acquisition
```

## Autopsy / Sleuth Kit
```bash
# List filesystem
fls disk.img

# List deleted files
fls -rd disk.img

# Extract file by inode
icat disk.img 123 > recovered_file

# Timeline
mactime -b bodyfile > timeline.csv
```

## Memory Forensics (Volatility)
```bash
# Identify OS profile
volatility -f memory.dmp imageinfo

# List processes
volatility -f memory.dmp --profile=Win10x64 pslist

# Network connections
volatility -f memory.dmp --profile=Win10x64 netscan

# Extract process
volatility -f memory.dmp --profile=Win10x64 procdump -p 1234 -D output/

# Registry
volatility -f memory.dmp --profile=Win10x64 printkey -K "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
```

## Network Forensics
```bash
# Capture
tcpdump -i eth0 -w capture.pcap

# Analyze with tshark
tshark -r capture.pcap -Y "http" -T fields -e http.host -e http.request.uri

# Extract files
tshark -r capture.pcap --export-objects http,extracted_files/

# Follow TCP stream
tshark -r capture.pcap -z "follow,tcp,ascii,0"
```

## File Carving
```bash
# foremost
foremost -i disk.img -o recovered/

# photorec
photorec disk.img

# bulk_extractor
bulk_extractor -o output/ disk.img
```

## Log Analysis
```bash
# Linux auth log
grep "Failed password" /var/log/auth.log | awk '{print $NF}' | sort | uniq -c | sort -rn

# Windows event log (with python-evtx)
python -m Evtx.Evtx dump security.evtx | grep "4625"

# Apache access log
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -20
```

## Common Pitfalls
- Working on original evidence (always work on copy)
- Not using write blocker
- Breaking chain of custody
- Not documenting every step
- Not verifying image integrity
- Contaminating evidence with own tools
- Not following jurisdictional legal requirements
''',
            "tags": ["forensics", "evidence", "Volatility", "Autopsy", "pcap", "reference"],
        },
    ],
    "computing_privacy_engineering": [
        {
            "title": "Privacy Engineering Implementation Reference",
            "content": '''# Privacy Engineering Implementation Reference

## Data Minimization
```python
# Collect only what is needed
# Bad: store full name, DOB, SSN, address for a newsletter
# Good: store only email

# Pseudonymization
import hashlib
import secrets

def pseudonymize(identifier: str, salt: str = None) -> str:
    if salt is None:
        salt = secrets.token_hex(16)
    return hashlib.sha256(f"{salt}:{identifier}".encode()).hexdigest()

# Tokenization (reversible with key)
from cryptography.fernet import Fernet
key = Fernet.generate_key()
cipher = Fernet(key)
token = cipher.encrypt(b"alice@example.com")
# Store token; original can be recovered with key
```

## k-Anonymity
```python
import pandas as pd

def check_k_anonymity(df, quasi_identifiers, k=5):
    groups = df.groupby(quasi_identifiers)
    counts = groups.size()
    return (counts >= k).all(), counts.min()

# Generalization to achieve k-anonymity
def generalize_zip(zip_code):
    # 12345 -> 1234* -> 123** -> 12*** -> 1****
    if len(zip_code) > 3:
        return zip_code[:3] + "**"
    return zip_code[:1] + "***"
```

## Differential Privacy
```python
import numpy as np

def laplace_mechanism(true_value, sensitivity=1.0, epsilon=0.1):
    noise = np.random.laplace(0, sensitivity / epsilon)
    return true_value + noise

# Count queries
def dp_count(df, condition, epsilon=0.1):
    true_count = len(df[condition])
    return laplace_mechanism(true_count, sensitivity=1.0, epsilon=epsilon)

# Mean queries
def dp_mean(df, column, lower, upper, epsilon=0.1):
    clipped = df[column].clip(lower, upper)
    true_mean = clipped.mean()
    sensitivity = (upper - lower) / len(df)
    return laplace_mechanism(true_mean, sensitivity=sensitivity, epsilon=epsilon)
```

## Consent Management
```python
class ConsentRecord:
    user_id: str
    purpose: str  # "marketing", "analytics", "third_party"
    granted: bool
    timestamp: float
    expiry: float  # when consent expires

class ConsentManager:
    def __init__(self):
        self.records = []
    
    def grant(self, user_id, purpose, duration_days=365):
        self.records.append(ConsentRecord(
            user_id=user_id, purpose=purpose, granted=True,
            timestamp=time.time(),
            expiry=time.time() + duration_days * 86400,
        ))
    
    def check(self, user_id, purpose):
        for r in reversed(self.records):
            if r.user_id == user_id and r.purpose == purpose:
                if r.granted and time.time() < r.expiry:
                    return True
        return False
    
    def withdraw(self, user_id, purpose):
        self.records.append(ConsentRecord(
            user_id=user_id, purpose=purpose, granted=False,
            timestamp=time.time(), expiry=0,
        ))
```

## Right to be Forgotten
```python
def delete_user_data(user_id):
    # Delete from all stores
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.execute("DELETE FROM orders WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM logs WHERE user_id = ?", (user_id,))
    # Delete from backups (mark for purge on next backup cycle)
    # Delete from caches
    cache.delete(f"user:{user_id}")
    # Delete from analytics (if identifiable)
    # Log the deletion (without storing the user data)
    log.info(f"User data deleted: user_id={hash(user_id)}")
```

## GDPR Key Requirements
- Lawful basis for processing (consent, contract, legitimate interest)
- Data subject rights: access, rectification, erasure, portability, objection
- Data Protection Impact Assessment (DPIA) for high-risk processing
- 72-hour breach notification
- Data Protection Officer (DPO) for certain organizations
- Privacy by design and by default

## Common Pitfalls
- Collecting too much data "just in case"
- Not implementing consent withdrawal
- Not deleting data when consent is withdrawn
- Storing PII in logs
- Not encrypting PII at rest
- Sharing data with third parties without consent
- Not conducting DPIA for high-risk processing
- Not documenting data flows
''',
            "tags": ["privacy", "differential privacy", "GDPR", "k-anonymity", "reference"],
        },
    ],
    "computing_highperformance_computing": [
        {
            "title": "Parallel Programming Reference",
            "content": '''# Parallel Programming Reference

## OpenMP (shared memory)
```c
#include <omp.h>

// Parallel for
#pragma omp parallel for
for (int i = 0; i < N; i++) {
    c[i] = a[i] + b[i];
}

// Reduction
#pragma omp parallel for reduction(+:sum)
for (int i = 0; i < N; i++) {
    sum += a[i];
}

// Sections
#pragma omp parallel sections
{
    #pragma omp section
    task_a();
    #pragma omp section
    task_b();
}
```

## MPI (distributed memory)
```python
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# Send/Receive
if rank == 0:
    data = {"message": "hello"}
    comm.send(data, dest=1, tag=0)
else:
    data = comm.recv(source=0, tag=0)

# Broadcast
data = None
if rank == 0:
    data = [1, 2, 3, 4]
data = comm.bcast(data, root=0)

# Scatter
local_data = comm.scatter([data[i::size] for i in range(size)], root=0)

# Gather
result = comm.gather(sum(local_data), root=0)

# Reduce
total = comm.reduce(local_sum, op=MPI.SUM, root=0)
```

## CUDA (GPU)
```python
import numpy as np
from numba import cuda

@cuda.kernel
def add(a, b, c):
    i = cuda.grid(1)
    if i < a.size:
        c[i] = a[i] + b[i]

# Allocate
a = cuda.to_device(np.arange(100, dtype=np.float32))
b = cuda.to_device(np.arange(100, dtype=np.float32))
c = cuda.device_array_like(a)

# Launch
threads_per_block = 256
blocks_per_grid = (a.size + threads_per_block - 1) // threads_per_block
add[blocks_per_grid, threads_per_block](a, b, c)

# Copy back
result = c.copy_to_host()
```

## Profiling
```bash
# perf (Linux)
perf record ./myprogram
perf report

# gprof
gcc -pg -o myprogram myprogram.c
./myprogram
gprof myprogram gmon.out > profile.txt

# Nsight (NVIDIA GPU)
nsys profile ./my_cuda_program
```

## Amdahls Law
```
Speedup = 1 / ((1 - p) + p/n)
p = parallel fraction
n = number of processors

Example: 90% parallel, 10 processors
Speedup = 1 / (0.1 + 0.09) = 5.26x (not 10x)
```

## Common Pitfalls
- False sharing (threads writing to adjacent cache lines)
- Load imbalance (one thread does more work)
- Excessive synchronization (barriers)
- Not considering memory bandwidth (compute-bound vs memory-bound)
- Race conditions in shared memory
- Not pinning threads to cores
- GPU: not coalescing memory accesses
- GPU: too few threads to saturate GPU
''',
            "tags": ["HPC", "parallel", "OpenMP", "MPI", "CUDA", "reference"],
        },
    ],
    "computing_computer_graphics": [
        {
            "title": "Rendering and Shaders Reference",
            "content": '''# Rendering and Shaders Reference

## Rendering Pipeline
1. Vertex processing: transform vertices to screen space
2. Triangle assembly: form triangles from vertices
3. Rasterization: convert triangles to fragments
4. Fragment processing: compute color per fragment
5. Output merging: depth test, blending, write to framebuffer

## OpenGL Shader (GLSL)
```glsl
// Vertex shader
#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec2 aTexCoord;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec2 TexCoord;

void main() {
    gl_Position = projection * view * model * vec4(aPos, 1.0);
    TexCoord = aTexCoord;
}

// Fragment shader
#version 330 core
in vec2 TexCoord;
out vec4 FragColor;

uniform sampler2D texture1;
uniform vec3 lightColor;

void main() {
    vec4 texColor = texture(texture1, TexCoord);
    FragColor = texColor * vec4(lightColor, 1.0);
}
```

## PBR (Physically Based Rendering)
```
BRDF = KD * Lambert + KS * Cook-Torrance

Lambert: albedo / PI
Cook-Torrance: (DFG) / (4 * (VoN) * (LoN))

D = Normal Distribution (GGX)
F = Fresnel (Schlick)
G = Geometry (Smith)
```

```glsl
// GGX normal distribution
float D_GGX(float NoH, float roughness) {
    float a = roughness * roughness;
    float a2 = a * a;
    float NoH2 = NoH * NoH;
    float denom = NoH2 * (a2 - 1.0) + 1.0;
    return a2 / (PI * denom * denom);
}

// Schlick Fresnel
vec3 F_Schlick(float VoH, vec3 F0) {
    return F0 + (1.0 - F0) * pow(1.0 - VoH, 5.0);
}
```

## Matrix Transformations
```python
import numpy as np

def translation(x, y, z):
    return np.array([
        [1, 0, 0, x],
        [0, 1, 0, y],
        [0, 0, 1, z],
        [0, 0, 0, 1],
    ], dtype=np.float32)

def rotation_y(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array([
        [c, 0, s, 0],
        [0, 1, 0, 0],
        [-s, 0, c, 0],
        [0, 0, 0, 1],
    ], dtype=np.float32)

def perspective(fov, aspect, near, far):
    f = 1.0 / np.tan(fov / 2)
    return np.array([
        [f/aspect, 0, 0, 0],
        [0, f, 0, 0],
        [0, 0, (far+near)/(near-far), 2*far*near/(near-far)],
        [0, 0, -1, 0],
    ], dtype=np.float32)
```

## Common Pitfalls
- Not normalizing vectors after interpolation
- Z-fighting (coplanar surfaces; use polygon offset)
- Not using depth testing
- Gamma correction (linear vs sRGB)
- Not handling aspect ratio
- Too many draw calls (batch)
- Not using texture compression
''',
            "tags": ["graphics", "rendering", "shaders", "OpenGL", "PBR", "reference"],
        },
    ],
    "computing_firmware": [
        {
            "title": "Firmware Development Reference",
            "content": '''# Firmware Development Reference

## Boot Process
1. Power on
2. ROM code: minimal init, load bootloader
3. Bootloader (U-Boot): init RAM, load OS kernel
4. Kernel: init drivers, mount root filesystem
5. Init (systemd): start services

## U-Boot
```bash
# Common commands
=> printenv          # show environment
=> setenv bootargs "console=ttyS0,115200 root=/dev/mmcblk0p2"
=> bootm 0x80008000  # boot from memory address
=> tftpboot 0x80008000 kernel.img  # load via TFTP
=> saveenv           # save environment

# Boot script (boot.scr)
setenv bootargs "console=ttyS0,115200 root=/dev/mmcblk0p2 rw"
load mmc 0:1 0x80008000 zImage
load mmc 0:1 0x88000000 dtb
bootz 0x80008000 - 0x88000000
```

## Device Tree
```dts
/dts-v1/;

/ {
    model = "My Board";
    compatible = "myvendor,myboard";

    chosen {
        bootargs = "console=ttyS0,115200";
        stdout-path = &uart0;
    };

    memory@80000000 {
        device_type = "memory";
        reg = <0x80000000 0x10000000>;  /* 256MB */
    };

    uart0: serial@40002000 {
        compatible = "myvendor,uart";
        reg = <0x40002000 0x1000>;
        interrupts = <0 32 4>;
        clock-frequency = <48000000>;
        status = "okay";
    };
};
```

## Secure Boot
```
1. Boot ROM verifies bootloader signature
2. Bootloader verifies kernel signature
3. Kernel verifies initramfs signature
4. Chain of trust established

Keys:
- Root key (in ROM/OTP, immutable)
- Bootloader key (signed by root key)
- Kernel key (signed by bootloader key)
```

## Firmware Update
```c
// A/B update pattern
typedef struct {
    uint32_t active_slot;  // 0 or 1
    uint32_t slot0_status; // VALID, INVALID, UPDATING
    uint32_t slot1_status;
    uint32_t slot0_version;
    uint32_t slot1_version;
    uint32_t slot0_retries;
    uint32_t slot1_retries;
} boot_ctrl_t;

// Update flow:
// 1. Write new firmware to inactive slot
// 2. Mark inactive slot as UPDATING
// 3. Verify signature
// 4. Mark as VALID
// 5. Set active_slot to new slot
// 6. Reboot
// 7. On successful boot, mark old slot as fallback
// 8. On failure (retries exhausted), revert to old slot
```

## Common Pitfalls
- Not handling power failure during update
- Not verifying firmware signature before boot
- Not having rollback mechanism
- Hardcoded memory addresses (use device tree)
- Not using watchdog during long operations
- Not testing with corrupted firmware
- Not versioning firmware properly
''',
            "tags": ["firmware", "bootloader", "U-Boot", "device tree", "secure boot", "reference"],
        },
    ],
    "computing_robotics": [
        {
            "title": "ROS 2 and Robotics Reference",
            "content": '''# ROS 2 and Robotics Reference

## ROS 2 Basics
```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class MinimalPublisher(Node):
    def __init__(self):
        super().__init__('minimal_publisher')
        self.publisher = self.create_publisher(String, 'topic', 10)
        timer_period = 0.5
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0

    def timer_callback(self):
        msg = String()
        msg.data = f'Hello World: {self.i}'
        self.publisher.publish(msg)
        self.get_logger().info(f'Published: "{msg.data}"')
        self.i += 1

def main():
    rclpy.init()
    node = MinimalPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

## Subscriber
```python
class MinimalSubscriber(Node):
    def __init__(self):
        super().__init__('minimal_subscriber')
        self.subscription = self.create_subscription(
            String, 'topic', self.listener_callback, 10)

    def listener_callback(self, msg):
        self.get_logger().info(f'Received: "{msg.data}"')
```

## PID Controller
```python
class PID:
    def __init__(self, kp, ki, kd, setpoint=0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.integral = 0
        self.prev_error = 0

    def update(self, measurement, dt):
        error = self.setpoint - measurement
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt
        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        self.prev_error = error
        return output
```

## Transforms (TF2)
```python
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

def broadcast_transform():
    br = TransformBroadcaster(node)
    t = TransformStamped()
    t.header.stamp = node.get_clock().now().to_msg()
    t.header.frame_id = 'odom'
    t.child_frame_id = 'base_link'
    t.transform.translation.x = 1.0
    t.transform.rotation.w = 1.0
    br.sendTransform(t)
```

## Path Planning (A*)
```python
import heapq

def astar(grid, start, goal):
    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            return reconstruct_path(came_from, current)

        for neighbor in get_neighbors(grid, current):
            tentative_g = g_score[current] + 1
            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    return None

def heuristic(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])
```

## Common Pitfalls
- Not handling sensor noise
- Not having safety stops
- Coordinate frame confusion (use TF2)
- Not handling communication delays
- Real-time constraints not met
- Not testing in simulation first
- Not handling edge cases (boundaries, obstacles)
''',
            "tags": ["ROS", "robotics", "PID", "path planning", "TF2", "reference"],
        },
    ],
    "computing_accessibility_engineering": [
        {
            "title": "Accessibility Implementation Reference",
            "content": '''# Accessibility Implementation Reference

## Semantic HTML
```html
<!-- Bad -->
<div onclick="submit()" class="button">Submit</div>

<!-- Good -->
<button type="submit">Submit</button>

<!-- Bad -->
<div class="heading">Title</div>

<!-- Good -->
<h1>Title</h1>

<!-- Navigation -->
<nav role="navigation" aria-label="Main">
  <ul>
    <li><a href="/" aria-current="page">Home</a></li>
    <li><a href="/about">About</a></li>
  </ul>
</nav>
```

## ARIA
```html
<!-- Live regions -->
<div aria-live="polite" id="status"></div>
<div aria-live="assertive" id="errors"></div>

<!-- Labels -->
<button aria-label="Close dialog">X</button>
<input aria-label="Search" type="text">
<input aria-labelledby="email-label" type="email">
<label id="email-label">Email address</label>

<!-- Roles -->
<div role="dialog" aria-modal="true" aria-labelledby="title">
  <h2 id="title">Settings</h2>
</div>

<!-- States -->
<button aria-expanded="false" aria-controls="menu">Menu</button>
<div id="menu" aria-hidden="true">...</div>
```

## Keyboard Navigation
```html
<!-- Skip link -->
<a href="#main" class="skip-link">Skip to main content</a>
<main id="main">...</main>

<!-- Focus management -->
<div tabindex="-1" id="dialog">...</div>
<script>
  dialog.focus();
  // Trap focus in dialog
  // Return focus to trigger on close
</script>
```

## Focus Management
```javascript
// Show dialog
function openDialog() {
  const dialog = document.getElementById('dialog');
  dialog.style.display = 'block';
  dialog.setAttribute('aria-hidden', 'false');
  // Store current focus
  previousFocus = document.activeElement;
  // Focus first focusable element
  const focusable = dialog.querySelectorAll('button, [href], input, select, textarea');
  focusable[0].focus();
  // Trap focus
  document.addEventListener('keydown', trapFocus);
}

function closeDialog() {
  const dialog = document.getElementById('dialog');
  dialog.style.display = 'none';
  dialog.setAttribute('aria-hidden', 'true');
  document.removeEventListener('keydown', trapFocus);
  previousFocus.focus();
}

function trapFocus(e) {
  if (e.key !== 'Tab') return;
  const focusable = dialog.querySelectorAll('button, [href], input, select, textarea');
  if (e.shiftKey && document.activeElement === focusable[0]) {
    e.preventDefault();
    focusable[focusable.length - 1].focus();
  } else if (!e.shiftKey && document.activeElement === focusable[focusable.length - 1]) {
    e.preventDefault();
    focusable[0].focus();
  }
}
```

## Color Contrast
```css
/* WCAG AA: 4.5:1 for normal text, 3:1 for large text */
/* WCAG AAA: 7:1 for normal text, 4.5:1 for large text */

/* Good */
body { color: #333; background: #fff; }  /* 12.6:1 */
.text { color: #767676; background: #fff; }  /* 4.5:1 */

/* Bad */
.text { color: #999; background: #fff; }  /* 2.85:1 - fails AA */
```

## Testing
```bash
# Automated
axe-core
npx @axe-core/cli http://localhost:3000

# Lighthouse
npx lighthouse http://localhost:3000 --only-categories=accessibility

# pa11y
pa11y http://localhost:3000
```

```javascript
// Jest with axe
import { axe } from 'jest-axe';

test('should have no violations', async () => {
  const { container } = render(<App />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

## Common Pitfalls
- Using div instead of button/link
- Missing alt text on images
- No focus indicators (outline: none without replacement)
- Inaccessible forms (no labels)
- Color-only error indication
- No skip link
- Not handling keyboard for custom widgets
- Forgetting aria-hidden on hidden content
- Not testing with screen reader
''',
            "tags": ["accessibility", "ARIA", "WCAG", "screen reader", "keyboard", "reference"],
        },
    ],
    "computing_it_support_administration": [
        {
            "title": "System Administration Reference",
            "content": '''# System Administration Reference

## Linux Administration

### User Management
```bash
# Create user
useradd -m -s /bin/bash alice
passwd alice

# Add to group
usermod -aG sudo alice
usermod -aG docker alice

# Remove user
userdel -r alice

# Lock/unlock
passwd -l alice  # lock
passwd -u alice  # unlock
```

### File Permissions
```bash
# Symbolic
chmod u+x file      # owner execute
chmod g-w file      # group remove write
chmod o=r file      # others read only
chmod a+r file      # all read

# Numeric (owner|group|other: r=4 w=2 x=1)
chmod 755 file      # rwxr-xr-x
chmod 644 file      # rw-r--r--
chmod 600 file      # rw-------
chmod 777 file      # rwxrwxrwx (avoid)

# Ownership
chown alice:staff file
chgrp staff file

# Recursive
chmod -R 755 directory/
```

### Process Management
```bash
# List
ps aux
ps aux | grep python
top
htop

# Kill
kill 1234          # SIGTERM
kill -9 1234       # SIGKILL (force)
killall python
pkill -f "python script.py"

# Background
nohup python script.py &
disown -h %1

# Systemd
systemctl status nginx
systemctl start nginx
systemctl enable nginx
systemctl restart nginx
journalctl -u nginx -f
```

### Disk Management
```bash
# Disk usage
df -h
du -sh /var/log
du -h --max-depth=1 /

# Find large files
find / -type f -size +100M 2>/dev/null

# Mount
mount /dev/sdb1 /mnt/data
umount /mnt/data

# fstab
/dev/sdb1 /mnt/data ext4 defaults 0 2

# LVM
pvcreate /dev/sdb
vgcreate vg0 /dev/sdb
lvcreate -L 50G -n data vg0
mkfs.ext4 /dev/vg0/data
```

### Networking
```bash
# IP
ip addr show
ip route show
ip link set eth0 up

# DNS
cat /etc/resolv.conf
dig example.com
nslookup example.com

# Connections
ss -tlnp    # listening TCP
ss -tnp     # established TCP
netstat -tlnp  # legacy

# Firewall (ufw)
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
ufw status verbose
```

## Backup Strategies
```bash
# rsync
rsync -avz --delete /data/ backup-server:/backup/

# tar
tar czf backup-$(date +%F).tar.gz /important/

# cron backup
# /etc/cron.d/backup
0 2 * * * root rsync -avz --delete /data/ backup:/backup/ >> /var/log/backup.log 2>&1

# Incremental with rsnapshot
rsnapshot hourly
rsnapshot daily
```

## Monitoring
```bash
# CPU
top, htop, mpstat 1

# Memory
free -h, vmstat 1

# Disk I/O
iostat 1, iotop

# Network
iftop, nethogs

# Logs
tail -f /var/log/syslog
journalctl -f
journalctl --since "1 hour ago"
journalctl -u nginx --since today
```

## Ansible
```yaml
# playbook.yml
- hosts: webservers
  become: yes
  tasks:
    - name: Install nginx
      apt:
        name: nginx
        state: present
        update_cache: yes

    - name: Start nginx
      service:
        name: nginx
        state: started
        enabled: yes

    - name: Copy config
      copy:
        src: nginx.conf
        dest: /etc/nginx/nginx.conf
      notify: restart nginx

  handlers:
    - name: restart nginx
      service:
        name: nginx
        state: restarted
```

## Common Pitfalls
- Running services as root (use service users)
- Not setting up SSH keys (using password auth)
- Not disabling root SSH login
- No firewall configured
- Not monitoring disk space (server crashes)
- Not setting up log rotation (logs fill disk)
- Not testing backups (cant restore when needed)
- Hardcoded paths in scripts
- Not using configuration management
''',
            "tags": ["sysadmin", "Linux", "permissions", "systemd", "Ansible", "reference"],
        },
    ],
    "computing_technology_project_management": [
        {
            "title": "Agile and Scrum Reference",
            "content": '''# Agile and Scrum Reference

## Scrum Framework

### Roles
- Product Owner: owns the backlog, prioritizes, represents stakeholders
- Scrum Master: facilitates process, removes impediments
- Development Team: self-organizing, cross-functional, 3-9 people

### Events
- Sprint: 2-4 week iteration
- Sprint Planning: select backlog items, create plan (timeboxed to 8h for 4-week sprint)
- Daily Scrum: 15-minute sync (what did, what will, impediments)
- Sprint Review: demonstrate working increment (timeboxed to 4h)
- Sprint Retrospective: improve process (timeboxed to 3h)

### Artifacts
- Product Backlog: ordered list of all desired features
- Sprint Backlog: selected items for current sprint + plan
- Increment: working, potentially shippable product

### Definition of Done
- Code written
- Unit tests written and passing
- Code reviewed
- Integration tests passing
- Documentation updated
- Deployed to staging

## User Stories
```
As a [type of user]
I want [some goal]
So that [some reason]

Acceptance Criteria:
- Given [context]
  When [action]
  Then [outcome]
```

### Story Points
- Relative complexity, not hours
- Fibonacci: 1, 2, 3, 5, 8, 13, 21
- Planning Poker: team estimates together

### Velocity
- Average story points completed per sprint
- Used for forecasting, not targets
- Should stabilize over 3-4 sprints

## Kanban
- Visualize workflow (columns: backlog, todo, in progress, review, done)
- Limit WIP (work in progress) per column
- Manage flow (identify bottlenecks)
- Make policies explicit
- Implement feedback loops
- Improve collaboratively

## Estimation
```
Story Points: relative complexity
Ideal Hours: best-case effort
T-Shirt Sizes: XS, S, M, L, XL

# Planning Poker
1. Each team member gets cards (1,2,3,5,8,13)
2. Story is read
3. Everyone picks a card privately
4. Reveal simultaneously
5. Discuss outliers
6. Re-vote until consensus
```

## Common Anti-Patterns
- Sprint backlog changes mid-sprint (scope creep)
- Daily scrum becomes status report to manager
- Product owner absent or disengaged
- Team too large or too small
- No retrospectives (no improvement)
- Velocity used as target/schedule
- Technical debt ignored
- QA done outside sprint
- Stories too large (should be split)
- No definition of done

## Pitfalls
- Treating Agile as no planning
- Skipping retrospectives
- Not measuring anything
- Measuring the wrong things (hours instead of outcomes)
- Ceremonies without purpose
- Agile in name only (waterfall with daily standups)
''',
            "tags": ["agile", "scrum", "kanban", "project management", "reference"],
        },
    ],
    "computing_quantum_computing": [
        {
            "title": "Quantum Computing with Qiskit Reference",
            "content": '''# Quantum Computing with Qiskit Reference

## Qubits
- |0> = [1, 0]
- |1> = [0, 1]
- Superposition: a|0> + b|1> where |a|^2 + |b|^2 = 1
- Measurement: collapses to |0> (prob |a|^2) or |1> (prob |b|^2)

## Gates
- X (NOT): flip |0> to |1>
- H (Hadamard): create superposition
- CNOT: entangle two qubits
- Z: phase flip
- T, S: phase gates

## Qiskit Basics
```python
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Create circuit
qc = QuantumCircuit(2, 2)  # 2 qubits, 2 classical bits

# Build circuit
qc.h(0)          # Hadamard on qubit 0
qc.cx(0, 1)      # CNOT: control=0, target=1
qc.measure([0, 1], [0, 1])  # Measure

# Simulate
simulator = AerSimulator()
compiled = transpile(qc, simulator)
result = simulator.run(compiled, shots=1000).result()
counts = result.get_counts()
print(counts)  # {'00': 500, '11': 500} (Bell state)
```

## Bell State (Entanglement)
```python
qc = QuantumCircuit(2, 2)
qc.h(0)       # |0> -> (|0>+|1>)/sqrt(2)
qc.cx(0, 1)   # entangle
qc.measure([0,1], [0,1])
# Result: 50% |00>, 50% |11> (never |01> or |10>)
```

## Grover Search
```python
from qiskit import QuantumCircuit
from qiskit.circuit.library import GroverOperator

# Oracle for finding |11>
oracle = QuantumCircuit(2)
oracle.cz(0, 1)  # mark |11>

grover = GroverOperator(oracle)
qc = QuantumCircuit(2)
qc.h([0, 1])  # superposition
qc.compose(grover, inplace=True)
qc.measure_all()
```

## Shor Algorithm (simplified)
```python
# Factor N = 15
# 1. Pick random a < N
# 2. Check gcd(a, N) > 1 -> found factor
# 3. Find period r of a^x mod N (quantum part)
# 4. If r is even, gcd(a^(r/2) +/- 1, N) may give factors

from math import gcd
from qiskit.algorithms import Shor

shor = Shor(15)
result = shor.run(AerSimulator())
print(result.factors)  # [[3, 5]]
```

## Common Pitfalls
- Decoherence: qubits lose quantum state quickly
- Noise: real quantum computers are error-prone
- Not enough shots (statistical errors)
- Forgetting to measure
- Not transpiling for target backend
- Expecting exponential speedup for all problems
''',
            "tags": ["quantum", "Qiskit", "qubits", "Grover", "Shor", "reference"],
        },
    ],
    "computing_ai_safety_evaluation": [
        {
            "title": "AI Safety and Evaluation Reference",
            "content": '''# AI Safety and Evaluation Reference

## Alignment Techniques

### RLHF (Reinforcement Learning from Human Feedback)
1. Train reward model on human preferences
2. Optimize policy with PPO against reward model
3. KL penalty to prevent policy from drifting too far

### DPO (Direct Preference Optimization)
- Simpler than RLHF
- Directly optimize on preference data
- No separate reward model needed

### Constitutional AI
- AI evaluates its own outputs against principles
- Reduces need for human labeling
- Anthropic approach

## Failure Modes

### Hallucination
- Model generates confident but false information
- Detection: cross-reference with sources, confidence calibration
- Mitigation: RAG (retrieval-augmented generation), grounding

### Sycophancy
- Model agrees with user even when user is wrong
- Detection: adversarial prompts, factual consistency checks
- Mitigation: training on disagreement data

### Reward Hacking
- Model optimizes proxy metric instead of true goal
- Example: model outputs long text to maximize "helpfulness" score
- Mitigation: multiple reward models, adversarial evaluation

### Distribution Shift
- Model trained on data A, deployed on data B
- Detection: monitor input distribution, OOD detection
- Mitigation: diverse training data, domain adaptation

## Evaluation Methods

### Benchmarks
```python
# MMLU (massive multitask language understanding)
# HellaSwag (commonsense reasoning)
# GSM8K (grade school math)
# HumanEval (code generation)
# TruthfulQA (truthfulness)

# Running benchmarks
from lm_eval import simple_evaluate
results = simple_evaluate(
    model="hf",
    model_args="pretrained=meta-llama/Llama-2-7b",
    tasks=["mmlu", "hellaswag", "gsm8k"],
)
```

### Red Teaming
- Adversarial probing for failures
- Manual: human testers craft attacks
- Automated: generate attacks with another model
- Categories: jailbreaks, bias, misinformation, harmful content

### Human Evaluation
- Side-by-side comparison (A/B testing)
- Likert scale ratings
- Chatbot arena (crowdsourced)

## Safety Frameworks

### NIST AI RMF
1. Govern: policies, accountability
2. Map: identify risks and context
3. Measure: assess and track risks
4. Manage: prioritize and mitigate

### EU AI Act Risk Levels
- Unacceptable: banned (social scoring, manipulation)
- High: strict requirements (biometric, critical infrastructure)
- Limited: transparency obligations (chatbots)
- Minimal: no obligations (spam filters)

## Responsible AI Practices
- Document training data (datasheets)
- Document models (model cards)
- Test for bias across demographic groups
- Monitor in production (drift, performance)
- Human oversight for high-stakes decisions
- Right to appeal automated decisions
- Privacy-preserving (federated learning, DP)

## Common Pitfalls
- Evaluating on training data distribution only
- Not testing for bias
- Not monitoring post-deployment
- Trusting benchmarks too much (Goodharts law)
- Not having human oversight for critical decisions
- Not documenting limitations
- Deploying too quickly without safety testing
''',
            "tags": ["AI safety", "alignment", "evaluation", "RLHF", "red teaming", "reference"],
        },
    ],
}
