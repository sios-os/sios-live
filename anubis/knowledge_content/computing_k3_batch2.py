"""K3 advanced content for Computing specialties - Batch 2.

Covers: networking, web_development, cybersecurity, devops, cloud_computing
"""

COMPUTING_K3_BATCH2: dict[str, list[dict]] = {
    "computing_networking_telecommunications": [
        {
            "title": "TCP/IP Protocol Suite Reference",
            "content": """# TCP/IP Protocol Suite

## Layer Model (TCP/IP)
```
Application  | HTTP, HTTPS, DNS, SMTP, SSH, FTP, gRPC
Transport    | TCP, UDP, QUIC, SCTP
Internet     | IP (v4/v6), ICMP, IGMP, IPsec
Link         | Ethernet, Wi-Fi, PPP, ARP
```

## IP Addressing

### IPv4
- 32-bit: 4.3 billion addresses
- Classes (legacy): A (/8), B (/16), C (/24)
- CIDR: 192.168.1.0/24 (256 addresses)
- Private ranges: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
- Loopback: 127.0.0.0/8 (127.0.0.1)
- Subnet mask: 255.255.255.0 = /24

### IPv6
- 128-bit: 340 undecillion addresses
- Format: 2001:0db8:85a3:0000:0000:8a2e:0370:7334
- Shortened: 2001:db8:85a3::8a2e:370:7334
- Link-local: fe80::/10
- Unique local: fc00::/7
- Loopback: ::1

### Subnetting
```
/24 = 256 addresses (254 usable)
/25 = 128 addresses (126 usable)
/26 = 64 addresses (62 usable)
/27 = 32 addresses (30 usable)
/30 = 4 addresses (2 usable, point-to-point)
```

## TCP (Transmission Control Protocol)
- Connection-oriented, reliable, ordered
- Three-way handshake: SYN, SYN-ACK, ACK
- Four-way teardown: FIN, ACK, FIN, ACK
- Flow control: sliding window
- Congestion control: slow start, AIMD, fast retransmit
- States: LISTEN, SYN_SENT, SYN_RECV, ESTABLISHED, FIN_WAIT, CLOSE_WAIT, LAST_ACK, TIME_WAIT

### TCP Header
```
Source Port (16) | Dest Port (16)
Sequence Number (32)
Ack Number (32)
Data Offset (4) | Reserved (3) | Flags (9) | Window (16)
Checksum (16) | Urgent Pointer (16)
```

### Flags
- SYN: synchronize sequence numbers
- ACK: acknowledgment
- FIN: finish (no more data)
- RST: reset connection
- PSH: push data to application
- URG: urgent pointer valid

## UDP (User Datagram Protocol)
- Connectionless, unreliable, unordered
- No handshake, no retransmission, no flow control
- Lower overhead, lower latency
- Use cases: DNS, DHCP, TFTP, VoIP, gaming, QUIC

### UDP Header
```
Source Port (16) | Dest Port (16)
Length (16) | Checksum (16)
```

## DNS (Domain Name System)
- Hierarchical: root -> TLD -> authoritative
- Record types:
  - A: IPv4 address
  - AAAA: IPv6 address
  - CNAME: canonical name (alias)
  - MX: mail exchange
  - TXT: text record (SPF, DKIM, verification)
  - NS: name server
  - SOA: start of authority
  - PTR: reverse DNS
  - SRV: service record

### Resolution
1. Browser asks OS resolver
2. OS checks cache
3. OS queries recursive resolver (ISP or 8.8.8.8)
4. Recursive resolver queries root -> TLD -> authoritative
5. Answer cached with TTL

### Tools
```bash
dig example.com
dig @8.8.8.8 example.com MX
nslookup example.com
host example.com
```

## HTTP/HTTPS

### HTTP Methods
| Method | Safe | Idempotent | Cacheable |
|--------|------|------------|-----------|
| GET | Yes | Yes | Yes |
| POST | No | No | Maybe |
| PUT | No | Yes | No |
| PATCH | No | No | No |
| DELETE | No | Yes | No |
| HEAD | Yes | Yes | Yes |
| OPTIONS | Yes | Yes | No |

### Status Codes
- 200 OK, 201 Created, 204 No Content
- 301 Moved Permanently, 302 Found, 304 Not Modified
- 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable
- 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout

### HTTP/1.1 vs HTTP/2 vs HTTP/3
- HTTP/1.1: text, pipelining (rarely used), keep-alive
- HTTP/2: binary, multiplexing, header compression (HPACK), server push
- HTTP/3: over QUIC (UDP), no head-of-line blocking, faster connection setup

### HTTPS (TLS)
- TLS handshake: ClientHello, ServerHello, certificate, key exchange, finished
- TLS 1.3: 1-RTT handshake, 0-RTT for resumed sessions
- Certificate: X.509, signed by CA, contains public key
- Cipher suite: key exchange + authentication + encryption + MAC

## Common Ports
| Port | Protocol |
|------|----------|
| 20/21 | FTP |
| 22 | SSH |
| 25 | SMTP |
| 53 | DNS |
| 80 | HTTP |
| 110 | POP3 |
| 143 | IMAP |
| 443 | HTTPS |
| 587 | SMTP submission |
| 993 | IMAPS |
| 995 | POP3S |
| 3306 | MySQL |
| 5432 | PostgreSQL |
| 6379 | Redis |
| 8080 | HTTP alt |

## Diagnostic Tools
```bash
# Connectivity
ping example.com
traceroute example.com
mtr example.com  # continuous traceroute

# Port scanning
nmap -sS -p 1-1000 example.com
nmap -sV example.com  # version detection

# Packet capture
tcpdump -i eth0 port 80
tcpdump -i eth0 -w capture.pcap
wireshark capture.pcap

# DNS
dig +trace example.com

# HTTP
curl -v https://example.com
curl -X POST -d '{"key":"value"}' -H "Content-Type: application/json" https://api.example.com
```

## Common Pitfalls
- TIME_WAIT accumulation (use SO_REUSEADDR)
- DNS caching causing stale results (check TTL)
- MTU mismatch causing fragmentation or black holes
- NAT breaking protocols that embed IP addresses
- Not handling IPv6 (dual-stack or v6-only)
- Assuming TCP is reliable over unreliable networks (it's not; connections drop)
- Forgetting to set timeouts (causing hangs)
""",
            "tags": ["TCP/IP", "networking", "DNS", "HTTP", "protocols", "reference"],
        },
        {
            "title": "Network Security and Firewalls",
            "content": """# Network Security and Firewalls

## Firewall Types

### Packet Filter
- Examines headers (IP, port, protocol)
- Stateless: each packet evaluated independently
- Fast but limited (no connection tracking)

### Stateful Firewall
- Tracks connection state (NEW, ESTABLISHED, RELATED, INVALID)
- Allows return traffic for established connections
- Most common firewall type

### Application Layer (Layer 7)
- Inspects packet content (HTTP headers, payloads)
- Can block specific applications or content
- Slower, more CPU intensive

### Next-Generation Firewall (NGFW)
- Stateful + application awareness + IPS + identity
- Deep packet inspection
- TLS decryption (SSL inspection)

## iptables (Linux)
```bash
# Tables: filter (default), nat, mangle, raw
# Chains: INPUT, OUTPUT, FORWARD (filter table)

# Allow established connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT

# Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Drop everything else
iptables -A INPUT -j DROP
iptables -P INPUT DROP

# Save
iptables-save > /etc/iptables/rules.v4
```

### nftables (modern replacement)
```bash
nft add table inet filter
nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'
nft add rule inet filter input ct state established,related accept
nft add rule inet filter input iif lo accept
nft add rule inet filter input tcp dport 22 accept
```

## TLS/SSL Configuration

### Good Cipher Suites (TLS 1.3)
- TLS_AES_256_GCM_SHA384
- TLS_CHACHA20_POLY1305_SHA256
- TLS_AES_128_GCM_SHA256

### TLS 1.2 Recommended
- ECDHE-ECDSA-AES256-GCM-SHA384
- ECDHE-RSA-AES256-GCM-SHA384
- ECDHE-ECDSA-CHACHA20-POLY1305
- ECDHE-RSA-CHACHA20-POLY1305

### Disable
- SSLv3, TLS 1.0, TLS 1.1 (deprecated)
- RC4, DES, 3DES, MD5
- Export-grade ciphers

### HSTS Header
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

## VPN Protocols
- WireGuard: modern, simple, fast, UDP-only
- OpenVPN: mature, flexible, TCP or UDP
- IPsec: standard, kernel-level, complex
- TLS-based VPNs (OpenVPN, AnyConnect)

## Zero Trust Architecture
- Never trust, always verify
- No implicit trust based on network location
- Authenticate and authorize every request
- Microsegmentation
- Principle of least privilege
- Continuous verification

### Implementation
- Identity provider (OIDC, SAML)
- Per-request authorization
- Device posture checks
- Network microsegmentation
- Encrypted all traffic (mTLS)

## Common Network Attacks

### MITM (Man-in-the-Middle)
- Attacker intercepts and relays traffic
- Prevention: TLS, certificate pinning, HSTS

### DDoS
- Volumetric: overwhelm bandwidth (UDP flood, amplification)
- Protocol: exhaust connection state (SYN flood)
- Application: HTTP flood, slowloris
- Mitigation: rate limiting, CDN, scrubbing services, SYN cookies

### DNS Attacks
- DNS hijacking: change DNS records
- DNS poisoning: inject fake records into cache
- DNS tunneling: exfiltrate data via DNS queries
- Prevention: DNSSEC, DNS over HTTPS/TLS

### ARP Spoofing
- Attacker sends fake ARP replies
- Prevention: static ARP, DHCP snooping, dynamic ARP inspection

## Security Headers
```
Content-Security-Policy: default-src 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

## Pitfalls
- Open ports on public interfaces
- Default credentials on network devices
- Not patching firewall firmware
- Overly permissive rules (ALLOW ANY ANY)
- No logging or monitoring on firewall
- TLS termination at load balancer without securing internal traffic
- Forgetting IPv6 firewall rules (often left open)
""",
            "tags": ["network security", "firewall", "iptables", "TLS", "zero trust", "reference"],
        },
    ],
    "computing_web_development": [
        {
            "title": "HTTP and REST API Design Reference",
            "content": """# HTTP and REST API Design

## REST Principles
1. Client-Server: separation of concerns
2. Stateless: each request contains all needed info
3. Cacheable: responses declare cacheability
4. Uniform Interface: consistent resource identification
5. Layered: intermediaries allowed (proxies, gateways)
6. Code on Demand (optional): server can send executable code

## Resource Naming
```
GET    /users          # list users
GET    /users/123      # get specific user
POST   /users          # create user
PUT    /users/123      # replace user
PATCH  /users/123      # partial update
DELETE /users/123      # delete user

GET    /users/123/orders        # list user's orders
GET    /users/123/orders/456    # get specific order
POST   /users/123/orders        # create order for user
```

### Naming Conventions
- Use nouns, not verbs (GET /users not GET /getUsers)
- Use plural for collections (/users not /user)
- Use kebab-case for multi-word (/order-items not /orderItems)
- Use query params for filtering, sorting, pagination
  ```
  GET /users?role=admin&sort=name&page=2&limit=20
  ```

## Status Codes
```
200 OK - successful GET, PUT, PATCH, DELETE
201 Created - successful POST (include Location header)
204 No Content - successful DELETE, no body needed
400 Bad Request - malformed request
401 Unauthorized - not authenticated
403 Forbidden - authenticated but not allowed
404 Not Found - resource doesn't exist
409 Conflict - duplicate or state conflict
422 Unprocessable Entity - valid format but invalid data
429 Too Many Requests - rate limited
500 Internal Server Error - server bug
502 Bad Gateway - upstream error
503 Service Unavailable - temporarily down
504 Gateway Timeout - upstream timeout
```

## Response Format

### JSON API
```json
{
  "id": 123,
  "name": "Alice",
  "email": "alice@example.com",
  "created_at": "2024-01-15T10:30:00Z",
  "links": {
    "self": "/users/123",
    "orders": "/users/123/orders"
  }
}
```

### Collection with pagination
```json
{
  "data": [...],
  "meta": {
    "page": 2,
    "limit": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

### Error format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email is required",
    "details": [
      {"field": "email", "message": "is required"}
    ]
  }
}
```

## Authentication

### Bearer Token (JWT)
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### API Key
```
X-API-Key: abc123def456
```

### Basic Auth (deprecated for APIs, use only over HTTPS)
```
Authorization: Basic dXNlcjpwYXNz
```

### OAuth 2.0
```
Authorization: Bearer <access_token>
```
Flow: authorization code, client credentials, password (deprecated), device code

## JWT Structure
```
header.payload.signature

header: {"alg": "HS256", "typ": "JWT"}
payload: {"sub": "123", "name": "Alice", "exp": 1700000000}
signature: HMACSHA256(base64(header) + "." + base64(payload), secret)
```

### JWT Pitfalls
- Don't store sensitive data in JWT (it's base64, not encrypted)
- Set short expiration times
- Use refresh tokens for long sessions
- Validate signature and expiration on every request
- Don't accept "alg: none"

## CORS (Cross-Origin Resource Sharing)
```
# Server response headers
Access-Control-Allow-Origin: https://example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 3600
```

### Preflight Request
- Browser sends OPTIONS before non-simple requests
- Server responds with allowed methods/headers
- Browser then sends actual request

## Rate Limiting
```
# Headers
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1700000000

# 429 response
Retry-After: 60
```

### Strategies
- Fixed window: N requests per time window
- Sliding window: N requests in trailing window
- Token bucket: tokens refill at rate R, max M
- Leaky bucket: smooth out bursts

## Versioning
- URL: /v1/users, /v2/users (most common)
- Header: Accept: application/vnd.api.v2+json
- Query: /users?version=2

## Idempotency
- GET, PUT, DELETE: inherently idempotent
- POST: not idempotent (use idempotency keys)
```
Idempotency-Key: client-generated-uuid
```
Server stores key + response for 24h; duplicate requests return same response.

## WebSockets
```javascript
const ws = new WebSocket("wss://example.com/ws");
ws.onopen = () => ws.send("Hello");
ws.onmessage = (event) => console.log(event.data);
ws.onclose = () => console.log("closed");
```

## GraphQL (comparison)
```graphql
query {
  user(id: 123) {
    name
    email
    orders {
      id
      total
    }
  }
}
```
- Single endpoint (/graphql)
- Client specifies fields
- No over/under-fetching
- Schema with types
- Trade-off: more complex server, caching harder

## Common Pitfalls
- Not using HTTPS
- Returning internal error details in production
- Not validating input
- Not setting rate limits
- Inconsistent error formats
- Not versioning the API
- Using GET for state changes
- Not handling pagination (returning all records)
- N+1 queries in ORM
- Not setting proper cache headers
""",
            "tags": ["HTTP", "REST", "API", "web", "reference"],
        },
        {
            "title": "Frontend Development Reference",
            "content": """# Frontend Development Reference

## HTML Essentials

### Semantic Elements
```html
<header>, <nav>, <main>, <article>, <section>, <aside>, <footer>
<h1>-<h6>, <p>, <ul>, <ol>, <table>, <figure>
<form>, <input>, <textarea>, <select>, <button>
<a>, <img>, <video>, <audio>, <canvas>
```

### Forms
```html
<form action="/submit" method="POST">
  <label for="email">Email</label>
  <input type="email" id="email" name="email" required>
  
  <label for="pwd">Password</label>
  <input type="password" id="pwd" name="password" 
         minlength="8" required>
  
  <select name="role">
    <option value="admin">Admin</option>
    <option value="user">User</option>
  </select>
  
  <button type="submit">Submit</button>
</form>
```

## CSS

### Layout
```css
/* Flexbox */
.container {
  display: flex;
  justify-content: center;  /* horizontal */
  align-items: center;      /* vertical */
  gap: 1rem;
}

/* Grid */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
}
```

### Responsive Design
```css
/* Mobile-first */
.card { padding: 1rem; }

@media (min-width: 768px) {
  .card { padding: 2rem; }
}

/* Container queries (modern) */
@container (min-width: 400px) {
  .card { padding: 2rem; }
}
```

### Units
- `rem`: relative to root font size (accessibility-friendly)
- `em`: relative to parent font size
- `vh/vw`: viewport height/width (1vh = 1% of viewport)
- `%`: relative to parent
- `fr`: fraction of available space (grid)
- `clamp(min, preferred, max)`: fluid sizing

## JavaScript

### ES6+ Features
```javascript
// Destructuring
const { name, email } = user;
const [first, ...rest] = array;

// Spread/rest
const merged = { ...obj1, ...obj2 };
function sum(...nums) { return nums.reduce((a, b) => a + b, 0); }

// Arrow functions
const add = (a, b) => a + b;

// Template literals
const greeting = `Hello, ${name}!`;

// Optional chaining
const city = user?.address?.city;

// Nullish coalescing
const name = input ?? "Anonymous";

// Async/await
async function fetchUser(id) {
  try {
    const resp = await fetch(`/api/users/${id}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  } catch (err) {
    console.error(err);
    return null;
  }
}
```

### Modules
```javascript
// math.js
export const add = (a, b) => a + b;
export default function multiply(a, b) { return a * b; }

// main.js
import multiply, { add } from './math.js';
```

### Fetch API
```javascript
// GET
const resp = await fetch('/api/users');
const users = await resp.json();

// POST
const resp = await fetch('/api/users', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'Alice' }),
});
const created = await resp.json();
```

## React Patterns

### Component
```jsx
function UserCard({ user, onSelect }) {
  return (
    <div className="card" onClick={() => onSelect(user.id)}>
      <h3>{user.name}</h3>
      <p>{user.email}</p>
    </div>
  );
}
```

### Hooks
```jsx
function App() {
  const [count, setCount] = useState(0);
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch('/api/data')
      .then(r => r.json())
      .then(setData);
  }, []);  // run once

  useEffect(() => {
    document.title = `Count: ${count}`;
  }, [count]);  // run when count changes

  return <button onClick={() => setCount(count + 1)}>{count}</button>;
}
```

### Custom Hook
```jsx
function useFetch(url) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetch(url)
      .then(r => r.json())
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [url]);

  return { data, loading, error };
}
```

## Performance

### Core Web Vitals
- LCP (Largest Contentful Paint): < 2.5s
- INP (Interaction to Next Paint): < 200ms
- CLS (Cumulative Layout Shift): < 0.1

### Optimization Techniques
- Minify and compress (gzip, brotli)
- Lazy load images (`loading="lazy"`)
- Code splitting (dynamic imports)
- Tree shaking (remove unused code)
- CDN for static assets
- Cache headers (Cache-Control, ETag)
- Preload critical resources
- Defer non-critical JavaScript
- Use `srcset` for responsive images
- Avoid layout thrashing

### Measuring
```bash
# Lighthouse
npx lighthouse https://example.com --view

# Chrome DevTools
# Performance tab: record and analyze
# Network tab: waterfall analysis
```

## Accessibility (WCAG)
- Semantic HTML (use <button> not <div onclick>)
- Alt text for images
- Keyboard navigation (tab order)
- Focus indicators visible
- ARIA labels where needed
- Color contrast: 4.5:1 for normal text, 3:1 for large
- Don't rely on color alone to convey information

## Common Pitfalls
- Not handling loading states
- Not handling error states
- Memory leaks from uncleared intervals/timeouts
- Stale closures in hooks
- Prop drilling (use context or state management)
- Not debouncing input handlers
- Layout thrashing (read then write DOM)
- Not using semantic HTML
- Inline styles instead of CSS
- Not testing on real devices
""",
            "tags": ["frontend", "HTML", "CSS", "JavaScript", "React", "reference"],
        },
    ],
    "computing_cybersecurity": [
        {
            "title": "OWASP Top 10 and Web Security",
            "content": """# OWASP Top 10 and Web Security

## OWASP Top 10 (2021)

### A01: Broken Access Control
- Users access resources they shouldn't
- Prevention: deny by default, server-side checks, fail closed

```python
# Bad
@app.route("/users/<id>")
def get_user(id):
    return User.query.get(id)  # anyone can see any user

# Good
@app.route("/users/<id>")
@login_required
def get_user(id):
    if current_user.id != int(id) and not current_user.is_admin:
        abort(403)
    return User.query.get(id)
```

### A02: Cryptographic Failures
- Sensitive data exposed or weakly encrypted
- Prevention: encrypt at rest, TLS in transit, strong algorithms

```python
# Bad
password_hash = md5(password).hexdigest()

# Good
import bcrypt
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# Verification
if bcrypt.checkpw(input_password.encode(), stored_hash):
    # authenticated
```

### A03: Injection
- SQL, NoSQL, command, LDAP, XPath injection
- Prevention: parameterized queries, input validation

```python
# Bad: SQL injection
cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")

# Good: parameterized
cursor.execute("SELECT * FROM users WHERE name = ?", (name,))

# ORM (automatic parameterization)
user = User.query.filter_by(name=name).first()
```

```python
# Bad: command injection
import os
os.system(f"ping {host}")

# Good: subprocess with list
subprocess.run(["ping", host], check=True)
```

### A04: Insecure Design
- Missing security in design phase
- Prevention: threat modeling, secure design patterns

### A05: Security Misconfiguration
- Default credentials, verbose errors, open S3 buckets
- Prevention: hardening, disable defaults, security headers

### A06: Vulnerable and Outdated Components
- Known CVEs in dependencies
- Prevention: dependency scanning, patching, SBOM

```bash
# Check for vulnerabilities
npm audit
pip-audit
safety check
snyk test
```

### A07: Identification and Authentication Failures
- Weak passwords, no MFA, session fixation
- Prevention: strong password policy, MFA, secure session management

### A08: Software and Data Integrity Failures
- Unsigned updates, insecure deserialization
- Prevention: code signing, integrity checks

```python
# Bad: insecure deserialization
import pickle
data = pickle.loads(request.data)  # arbitrary code execution!

# Good: use safe format
import json
data = json.loads(request.data)
```

### A09: Security Logging and Monitoring Failures
- No audit logs, no alerting
- Prevention: log security events, monitor, alert

### A10: Server-Side Request Forgery (SSRF)
- Server makes requests to attacker-specified URLs
- Prevention: allowlist URLs, block internal ranges

```python
# Bad
import requests
resp = requests.get(user_url)  # could hit http://169.254.169.254/

# Good
from urllib.parse import urlparse
import ipaddress

def is_safe_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False
    except ValueError:
        pass  # hostname, not IP
    return True

if not is_safe_url(user_url):
    abort(400, "URL not allowed")
```

## XSS (Cross-Site Scripting)

### Types
- Stored: payload saved on server, served to victims
- Reflected: payload in URL, reflected in response
- DOM: payload executed in browser via DOM manipulation

### Prevention
```python
# Template auto-escaping (Jinja2, Django, etc.)
{{ user_input }}  # auto-escaped

# If you must output raw HTML, sanitize
import bleach
clean = bleach.clean(user_input, tags=['b', 'i', 'a'], attributes={'a': ['href']})
```

```javascript
// React auto-escapes
<div>{userInput}</div>  // safe

// dangerouslySetInnerHTML is dangerous
<div dangerouslySetInnerHTML={{__html: userInput}} />  // XSS risk!
```

### CSP Header
```
Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.example.com; style-src 'self' 'unsafe-inline'
```

## CSRF (Cross-Site Request Forgery)
- Attacker makes user's browser send request to vulnerable site
- Prevention: CSRF tokens, SameSite cookies

```python
# Flask-WTF
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

# In template
<form method="POST">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
</form>
```

```
Set-Cookie: session=abc123; SameSite=Strict; Secure; HttpOnly
```

## Session Security
- Use HttpOnly cookies (no JS access)
- Use Secure flag (HTTPS only)
- Use SameSite (Strict or Lax)
- Regenerate session ID on login
- Set reasonable timeout
- Store session ID, not session data, in cookie

## Password Storage
```python
# Argon2 (recommended)
from argon2 import PasswordHasher
ph = PasswordHasher()
hash = ph.hash(password)
try:
    ph.verify(hash, input_password)
except VerifyMismatchError:
    # wrong password
```

## API Security
- Validate all input
- Use rate limiting
- Authenticate every request
- Use HTTPS only
- Don't expose internal errors
- Validate content types
- Use CORS properly
- Implement idempotency for writes

## Security Headers Checklist
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=()
```

## Pitfalls
- Trusting client-side validation (always validate on server)
- Storing passwords in plain text or with weak hashing
- Using GET for sensitive data (logged in URLs)
- Not using HTTPS
- Exposing stack traces in production
- Not rotating keys/secrets
- Hardcoding secrets in source code
- Not sanitizing file upload names/paths
- Allowing redirect to arbitrary URLs (open redirect)
""",
            "tags": ["OWASP", "web security", "XSS", "CSRF", "injection", "reference"],
        },
        {
            "title": "Cryptography Reference",
            "content": """# Cryptography Reference

## Symmetric Encryption
Same key for encryption and decryption. Fast, used for bulk data.

### AES (Advanced Encryption Standard)
- Block cipher: 128-bit blocks
- Key sizes: 128, 192, 256 bits
- AES-256-GCM: recommended (authenticated encryption)

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

key = AESGCM.generate_key(bit_length=256)
cipher = AESGCM(key)
nonce = os.urandom(12)  # 96-bit nonce
ciphertext = cipher.encrypt(nonce, plaintext, associated_data)
plaintext = cipher.decrypt(nonce, ciphertext, associated_data)
```

### ChaCha20-Poly1305
- Stream cipher + MAC
- Often faster than AES on devices without AES-NI
- Used in TLS, WireGuard

### Modes
- ECB: DON'T USE (reveals patterns)
- CBC: vulnerable to padding oracle
- GCM: authenticated, recommended
- ChaCha20-Poly1305: authenticated, recommended

## Asymmetric Encryption
Different keys for encryption and decryption. Slower, used for key exchange and signatures.

### RSA
- Key sizes: 2048 (minimum), 3072, 4096 bits
- Used for encryption and signatures
- Slow; use to encrypt symmetric key, then use symmetric for data

### ECC (Elliptic Curve Cryptography)
- Smaller keys for same security (256-bit ECC ~ 3072-bit RSA)
- Curves: P-256, P-384, P-521, Curve25519, secp256k1
- Used for ECDH key exchange and ECDSA signatures

### Key Exchange
- Diffie-Hellman: establish shared secret over public channel
- ECDH: elliptic curve DH (faster, smaller keys)

## Hashing
One-way function. Fixed-size output from any input.

### Algorithms
- SHA-256: 256-bit output, recommended
- SHA-3: newer, different structure
- BLAKE2/BLAKE3: faster, modern
- MD5: BROKEN, don't use for security
- SHA-1: BROKEN, don't use for security

```python
import hashlib
h = hashlib.sha256(data).hexdigest()
```

### Keyed Hashing (HMAC)
```python
import hmac
mac = hmac.new(key, message, hashlib.sha256).hexdigest()
# Verify
hmac.compare_digest(mac, expected_mac)  # constant-time comparison
```

## Digital Signatures
- Sign with private key, verify with public key
- Provides authenticity, integrity, non-repudiation

### Algorithms
- RSA-PSS: recommended for RSA
- ECDSA: elliptic curve signatures
- Ed25519: modern, fast, deterministic

```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
private_key = Ed25519PrivateKey.generate()
public_key = private_key.public_key()
signature = private_key.sign(message)
public_key.verify(signature, message)  # raises on invalid
```

## Key Derivation
- Derive keys from passwords (which are low entropy)
- Use salt + slow function

### PBKDF2
```python
import hashlib
key = hashlib.pbkdf2_hmac('sha256', password, salt, iterations=600000, dklen=32)
```

### Argon2 (recommended for passwords)
```python
from argon2 import PasswordHasher
ph = PasswordHasher(
    time_cost=3,      # iterations
    memory_cost=65536, # 64 MB
    parallelism=4,
)
hash = ph.hash(password)
```

### scrypt
```python
import hashlib
key = hashlib.scrypt(password, salt=salt, n=16384, r=8, p=1, dklen=32)
```

## Random Number Generation
```python
# SECURE (use for crypto)
import secrets
token = secrets.token_hex(32)  # 256-bit random
password = secrets.token_urlsafe(16)

# NOT SECURE (don't use for crypto)
import random
random.randint(0, 100)  # predictable
```

## TLS (Transport Layer Security)
- Provides confidentiality, integrity, authentication
- TLS 1.3: current standard, 1-RTT handshake
- TLS 1.2: still acceptable with proper config
- TLS 1.0/1.1, SSL: deprecated, disable

### Certificate Chain
- Root CA -> Intermediate CA -> Server certificate
- Server presents chain during handshake
- Client verifies chain to trusted root

## Common Pitfalls
- Using ECB mode (reveals patterns)
- Reusing nonce with same key (catastrophic in GCM/ChaCha20)
- Using MD5 or SHA-1 for security
- Not using authenticated encryption (use GCM or ChaCha20-Poly1305)
- Storing passwords with plain hash (use Argon2/bcrypt/scrypt)
- Using `random` instead of `secrets` for crypto
- Not verifying TLS certificates
- Hardcoding keys in source code
- Not rotating keys
- Using RSA without padding (use OAEP or PSS)
- Comparing hashes with `==` (timing attack; use hmac.compare_digest)
""",
            "tags": ["cryptography", "AES", "RSA", "hashing", "TLS", "reference"],
        },
    ],
    "computing_devops_site_reliability": [
        {
            "title": "CI/CD Pipeline Reference",
            "content": """# CI/CD Pipeline Reference

## Pipeline Stages
```
Source → Build → Test → Package → Deploy → Verify
```

## GitHub Actions Example
```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Lint
        run: ruff check .
      - name: Type check
        run: mypy .
      - name: Test
        run: pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v4

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t myapp:${{ github.sha }} .
      - name: Push to registry
        run: |
          docker tag myapp:${{ github.sha }} registry.example.com/myapp:${{ github.sha }}
          docker push registry.example.com/myapp:${{ github.sha }}

  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Deploy
        run: kubectl set image deployment/myapp myapp=registry.example.com/myapp:${{ github.sha }}
```

## GitLab CI Example
```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

test:
  stage: test
  image: python:3.12
  script:
    - pip install -r requirements.txt
    - pytest --cov
  coverage: '/TOTAL.*\s+(\d+\%)$/'

build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main

deploy:
  stage: deploy
  script:
    - kubectl set image deployment/app app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main
  when: manual
```

## Docker
```dockerfile
# Multi-stage build
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY . .
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8000/health || exit 1
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "app:app"]
```

### Docker Compose
```yaml
version: '3.9'
services:
  web:
    build: .
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql://user:pass@db:5432/app
    depends_on:
      db:
        condition: service_healthy
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: app
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

## Kubernetes
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: registry.example.com/myapp:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "128Mi"
            cpu: "250m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### Ingress
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt
spec:
  tls:
  - hosts: [app.example.com]
    secretName: app-tls
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp
            port:
              number: 80
```

## Terraform (IaC)
```hcl
# main.tf
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "web" {
  ami           = "ami-0c7217cdde317cfec"
  instance_type = "t3.micro"
  
  tags = {
    Name = "WebServer"
    Environment = "production"
  }
}

resource "aws_s3_bucket" "data" {
  bucket = "my-app-data-${random_id.suffix.hex}"
}

resource "random_id" "suffix" {
  byte_length = 4
}
```

## Deployment Strategies

### Blue/Green
- Two identical environments
- Switch traffic from old to new
- Instant rollback (switch back)

### Canary
- Deploy to small % of traffic
- Monitor metrics
- Gradually increase if healthy

### Rolling
- Replace instances gradually
- No downtime but mixed versions during rollout

### Feature Flags
```python
if feature_flags.is_enabled("new_checkout", user_id):
    return new_checkout()
return old_checkout()
```

## Observability

### Metrics (Prometheus)
```python
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('http_requests_total', 'Total requests', ['method', 'endpoint'])
request_latency = Histogram('http_request_duration_seconds', 'Request latency')

@app.route("/api/users")
@request_latency.time()
def get_users():
    request_count.labels(method='GET', endpoint='/api/users').inc()
    # ...
```

### Structured Logging
```python
import structlog
logger = structlog.get_logger()

logger.info("user_registered", user_id=123, email="alice@example.com")
# {"event": "user_registered", "user_id": 123, "email": "alice@example.com", "timestamp": "..."}
```

### Tracing (OpenTelemetry)
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@app.route("/api/users/<id>")
def get_user(id):
    with tracer.start_as_current_span("get_user"):
        with tracer.start_as_current_span("db_query"):
            user = db.query(User).get(id)
        return user
```

## SLO/SLI/Error Budget
```python
# SLO: 99.9% of requests succeed in 28 days
# Error budget: 0.1% of requests can fail
# If 1M requests/day, budget = 1000 failures/day

# SLI: success_rate = successful_requests / total_requests
# Burn rate: actual_error_rate / allowed_error_rate
# If burn rate > 1, you're consuming budget too fast
```

## Pitfalls
- Not caching dependencies (slow CI)
- Not running tests in parallel
- Deploying without tests
- No rollback strategy
- Not using immutable artifacts
- Secrets in CI logs
- Not pinning action versions
- Manual approval as only gate (automate checks)
- Not monitoring after deploy
- No health checks
""",
            "tags": ["CI/CD", "Docker", "Kubernetes", "Terraform", "DevOps", "reference"],
        },
    ],
    "computing_cloud_computing": [
        {
            "title": "AWS Core Services Reference",
            "content": """# AWS Core Services Reference

## Compute

### EC2 (Virtual Machines)
```bash
# Launch instance
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \
  --instance-type t3.micro \
  --key-name my-key \
  --security-group-ids sg-12345 \
  --subnet-id subnet-12345

# Instance types
t3.nano  - 2 vCPU, 0.5 GB  - $0.0052/hr
t3.micro - 2 vCPU, 1 GB    - $0.0104/hr
t3.small - 2 vCPU, 2 GB    - $0.0208/hr
m5.large - 2 vCPU, 8 GB    - $0.096/hr
c5.large - 2 vCPU, 4 GB    - $0.085/hr
r5.large - 2 vCPU, 16 GB   - $0.126/hr
```

### Lambda (Serverless)
```python
import json

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Hello'})
    }
```

```bash
# Deploy
aws lambda create-function \
  --function-name my-func \
  --runtime python3.12 \
  --handler index.lambda_handler \
  --zip-file fileb://function.zip \
  --role arn:aws:iam::123:role/lambda-role
```

### ECS (Container orchestration)
- Fargate: serverless containers
- EC2: manage your own container instances

## Storage

### S3 (Object storage)
```bash
# Create bucket
aws s3 mb s3://my-bucket

# Upload
aws s3 cp file.txt s3://my-bucket/

# Sync
aws s3 sync ./local-dir s3://my-bucket/dir/

# Website hosting
aws s3 website s3://my-bucket/ --index-document index.html
```

### EBS (Block storage for EC2)
- gp3: general purpose SSD (recommended)
- io2: high IOPS
- st1: throughput-optimized HDD
- sc1: cold HDD

## Database

### RDS (Managed relational DB)
- Engines: PostgreSQL, MySQL, Aurora, SQL Server, Oracle
- Multi-AZ for HA
- Read replicas for scaling reads

### DynamoDB (NoSQL)
```python
import boto3
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('users')

# Put
table.put_item(Item={'user_id': '123', 'name': 'Alice'})

# Get
response = table.get_item(Key={'user_id': '123'})

# Query
response = table.query(
    KeyConditionExpression='user_id = :uid',
    ExpressionAttributeValues={':uid': '123'}
)
```

## Networking

### VPC
```
VPC (10.0.0.0/16)
├── Public subnet (10.0.1.0/24)  - has route to internet gateway
├── Private subnet (10.0.2.0/24) - no direct internet
└── Private subnet (10.0.3.0/24) - different AZ
```

### Key Services
- Route 53: DNS
- CloudFront: CDN
- ELB/ALB/NLB: load balancers
- API Gateway: managed API
- CloudWatch: monitoring/logs
- IAM: identity and access
- KMS: key management
- Secrets Manager: secret storage

## IAM
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::my-bucket/*"
    }
  ]
}
```

### Best Practices
- Use roles, not access keys, for EC2/Lambda
- Follow least privilege
- Use IAM Identity Center (SSO) for humans
- Enable MFA for all users
- Rotate access keys
- Use permission boundaries for delegation

## Cost Optimization
- Use Spot instances for batch workloads (up to 90% off)
- Use Reserved Instances/Savings Plans for steady workloads
- Right-size instances (monitor CloudWatch)
- Use S3 lifecycle policies (transition to cheaper tiers)
- Delete unused EBS volumes and snapshots
- Use Aurora Serverless for variable workloads
- Set billing alerts

## Well-Architected Framework
1. Operational Excellence
2. Security
3. Reliability
4. Performance Efficiency
5. Cost Optimization
6. Sustainability

## Pitfalls
- Hardcoding region (use environment variable)
- Not using IAM roles for services
- Overly permissive security groups (0.0.0.0/0 on all ports)
- Not enabling Multi-AZ for production databases
- Forgetting to enable backups
- Not setting CloudWatch alarms
- Ignoring cost until bill arrives
- Using on-demand for steady workloads
""",
            "tags": ["AWS", "cloud", "EC2", "S3", "Lambda", "IAM", "reference"],
        },
    ],
}
