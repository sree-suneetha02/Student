# Student Management API

REST API for managing students with full CRUD operations.  
Implemented in **Python (Flask)**, **Node.js (Express)**, and **Go (Gin)** — all sharing identical endpoints, validation rules, and database schema.

---

## Project Structure

```
src/
├── python/             # Flask backend — port 5015
│   ├── app.py
│   └── test_app.py     # pytest test suite (31 tests)
├── nodejs/             # Express backend — port 5016
│   ├── app.js
│   └── package.json
├── golang/             # Gin backend — port 5017
│   ├── main.go
│   └── go.mod
├── tests/              # Shared curl-based test suite
│   ├── test_suite.sh   # Bash test suite (18 cases × 3 backends)
│   └── generate_curl.py # Python curl command generator
└── requirements.txt    # Python dependencies
```

---

## Ports

| Backend        | Port |
|----------------|------|
| Python / Flask | 5015 |
| Node.js / Express | 5016 |
| Go / Gin       | 5017 |

---

## API Endpoints

| Method | Endpoint         | Description         | Success |
|--------|-----------------|---------------------|---------|
| GET    | `/health`        | Health check        | 200     |
| GET    | `/students`      | Get all students    | 200     |
| GET    | `/students/:id`  | Get student by ID   | 200     |
| POST   | `/students`      | Create new student  | 201     |
| PUT    | `/students/:id`  | Update student      | 200     |
| DELETE | `/students/:id`  | Delete student      | 200     |

---

## Request & Response

### Student Object

```json
{
  "id": 1,
  "name": "Alice",
  "age": 22,
  "email": "alice@example.com"
}
```

### Create / Update Request Body

```json
{
  "name": "Alice",
  "age": 22,
  "email": "alice@example.com"
}
```

For `PUT`, all fields are optional — only the provided fields are updated.

### Error Response

```json
{ "error": ["name is required and must be non-empty", "age must be between 15 and 100"] }
```

---

## Validation Rules

| Field   | Rules |
|---------|-------|
| `name`  | Required, non-empty string |
| `age`   | Required, integer, must be **15–100** (inclusive) |
| `email` | Required, valid email format, **globally unique** |

**HTTP status codes for errors:**

| Code | Meaning |
|------|---------|
| 400  | Validation error (missing / invalid field) |
| 404  | Student not found |
| 409  | Email already exists |

---

## Database Schema

All backends use **SQLite** with the same schema:

```sql
CREATE TABLE IF NOT EXISTS students (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    age        INTEGER NOT NULL,
    email      TEXT    UNIQUE NOT NULL
);
```

---

## Setup & Run

### Python / Flask

```bash
cd python
pip install -r ../requirements.txt
python3 app.py
# → http://localhost:5015
```

### Node.js / Express

```bash
cd nodejs
npm install
npm start
# → http://localhost:5016
```

### Go / Gin

```bash
cd golang
go mod tidy
go run main.go
# → http://localhost:5017
```

---

## curl Commands

### 1. Health Check

```bash
# Python (5015)
curl http://localhost:5015/health

# Node.js (5016)
curl http://localhost:5016/health

# Go (5017)
curl http://localhost:5017/health
```

---

### 2. Get All Students

```bash
# Python (5015)
curl http://localhost:5015/students

# Node.js (5016)
curl http://localhost:5016/students

# Go (5017)
curl http://localhost:5017/students
```

---

### 3. Get Student by ID

```bash
# Python (5015)
curl http://localhost:5015/students/1

# Node.js (5016)
curl http://localhost:5016/students/1

# Go (5017)
curl http://localhost:5017/students/1
```

---

### 4. Create Student — Valid

```bash
# Python (5015)
curl -X POST http://localhost:5015/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "age": 22, "email": "alice@example.com"}'

# Node.js (5016)
curl -X POST http://localhost:5016/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "age": 22, "email": "alice@example.com"}'

# Go (5017)
curl -X POST http://localhost:5017/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "age": 22, "email": "alice@example.com"}'
```

---

### 5. Update Student — Full Update

```bash
# Python (5015)
curl -X PUT http://localhost:5015/students/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Updated", "age": 24, "email": "alice.new@example.com"}'

# Node.js (5016)
curl -X PUT http://localhost:5016/students/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Updated", "age": 24, "email": "alice.new@example.com"}'

# Go (5017)
curl -X PUT http://localhost:5017/students/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Updated", "age": 24, "email": "alice.new@example.com"}'
```

### 5b. Update Student — Partial Update (name only)

```bash
# Python (5015)
curl -X PUT http://localhost:5015/students/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "New Name"}'

# Node.js (5016)
curl -X PUT http://localhost:5016/students/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "New Name"}'

# Go (5017)
curl -X PUT http://localhost:5017/students/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "New Name"}'
```

---

### 6. Delete Student

```bash
# Python (5015)
curl -X DELETE http://localhost:5015/students/1

# Node.js (5016)
curl -X DELETE http://localhost:5016/students/1

# Go (5017)
curl -X DELETE http://localhost:5017/students/1
```

---

### 7. Error Cases — Validation (400)

```bash
# Missing name
# Python (5015)
curl -X POST http://localhost:5015/students \
  -H "Content-Type: application/json" \
  -d '{"age": 20, "email": "noname@example.com"}'

# Node.js (5016)
curl -X POST http://localhost:5016/students \
  -H "Content-Type: application/json" \
  -d '{"age": 20, "email": "noname@example.com"}'

# Go (5017)
curl -X POST http://localhost:5017/students \
  -H "Content-Type: application/json" \
  -d '{"age": 20, "email": "noname@example.com"}'


# Age below minimum (< 15)
# Python (5015)
curl -X POST http://localhost:5015/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Kid", "age": 10, "email": "kid@example.com"}'

# Node.js (5016)
curl -X POST http://localhost:5016/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Kid", "age": 10, "email": "kid@example.com"}'

# Go (5017)
curl -X POST http://localhost:5017/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Kid", "age": 10, "email": "kid@example.com"}'


# Age above maximum (> 100)
# Python (5015)
curl -X POST http://localhost:5015/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Elder", "age": 150, "email": "elder@example.com"}'

# Node.js (5016)
curl -X POST http://localhost:5016/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Elder", "age": 150, "email": "elder@example.com"}'

# Go (5017)
curl -X POST http://localhost:5017/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Elder", "age": 150, "email": "elder@example.com"}'


# Invalid email format
# Python (5015)
curl -X POST http://localhost:5015/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Dave", "age": 25, "email": "not-an-email"}'

# Node.js (5016)
curl -X POST http://localhost:5016/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Dave", "age": 25, "email": "not-an-email"}'

# Go (5017)
curl -X POST http://localhost:5017/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Dave", "age": 25, "email": "not-an-email"}'


# Missing age
# Python (5015)
curl -X POST http://localhost:5015/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Eve", "email": "eve@example.com"}'

# Node.js (5016)
curl -X POST http://localhost:5016/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Eve", "email": "eve@example.com"}'

# Go (5017)
curl -X POST http://localhost:5017/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Eve", "email": "eve@example.com"}'


# Empty body (all fields missing)
# Python (5015)
curl -X POST http://localhost:5015/students \
  -H "Content-Type: application/json" \
  -d '{}'

# Node.js (5016)
curl -X POST http://localhost:5016/students \
  -H "Content-Type: application/json" \
  -d '{}'

# Go (5017)
curl -X POST http://localhost:5017/students \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

### 8. Error Cases — Not Found (404)

```bash
# Get non-existent student
# Python (5015)
curl http://localhost:5015/students/99999

# Node.js (5016)
curl http://localhost:5016/students/99999

# Go (5017)
curl http://localhost:5017/students/99999


# Update non-existent student
# Python (5015)
curl -X PUT http://localhost:5015/students/99999 \
  -H "Content-Type: application/json" \
  -d '{"name": "Ghost"}'

# Node.js (5016)
curl -X PUT http://localhost:5016/students/99999 \
  -H "Content-Type: application/json" \
  -d '{"name": "Ghost"}'

# Go (5017)
curl -X PUT http://localhost:5017/students/99999 \
  -H "Content-Type: application/json" \
  -d '{"name": "Ghost"}'


# Delete non-existent student
# Python (5015)
curl -X DELETE http://localhost:5015/students/99999

# Node.js (5016)
curl -X DELETE http://localhost:5016/students/99999

# Go (5017)
curl -X DELETE http://localhost:5017/students/99999
```

---

### 9. Error Cases — Duplicate Email (409)

```bash
# Step 1: Create first student
# Python (5015)
curl -X POST http://localhost:5015/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "age": 22, "email": "alice@example.com"}'

# Node.js (5016)
curl -X POST http://localhost:5016/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "age": 22, "email": "alice@example.com"}'

# Go (5017)
curl -X POST http://localhost:5017/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "age": 22, "email": "alice@example.com"}'


# Step 2: Create duplicate email → 409
# Python (5015)
curl -X POST http://localhost:5015/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice2", "age": 23, "email": "alice@example.com"}'

# Node.js (5016)
curl -X POST http://localhost:5016/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice2", "age": 23, "email": "alice@example.com"}'

# Go (5017)
curl -X POST http://localhost:5017/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice2", "age": 23, "email": "alice@example.com"}'


# Step 3: Update another student to use existing email → 409
# Python (5015)
curl -X PUT http://localhost:5015/students/2 \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com"}'

# Node.js (5016)
curl -X PUT http://localhost:5016/students/2 \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com"}'

# Go (5017)
curl -X PUT http://localhost:5017/students/2 \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com"}'
```

---

### 10. Age Boundary — Valid Edge Cases (201)

```bash
# Age exactly 15 — minimum valid
# Python (5015)
curl -X POST http://localhost:5015/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Young", "age": 15, "email": "young@example.com"}'

# Node.js (5016)
curl -X POST http://localhost:5016/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Young", "age": 15, "email": "young@example.com"}'

# Go (5017)
curl -X POST http://localhost:5017/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Young", "age": 15, "email": "young@example.com"}'


# Age exactly 100 — maximum valid
# Python (5015)
curl -X POST http://localhost:5015/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Senior", "age": 100, "email": "senior@example.com"}'

# Node.js (5016)
curl -X POST http://localhost:5016/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Senior", "age": 100, "email": "senior@example.com"}'

# Go (5017)
curl -X POST http://localhost:5017/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Senior", "age": 100, "email": "senior@example.com"}'
```

---

## Running Tests

### Python — pytest (31 tests, no server needed)

```bash
cd python
pip install -r ../requirements.txt
python3 -m pytest test_app.py -v

# Run a single class
python3 -m pytest test_app.py::TestCreateStudent -v

# Run a single test
python3 -m pytest test_app.py::TestCreateStudent::test_tc09_valid_create_returns_201 -v
```

### Bash Test Suite (18 cases × 3 backends = 54 tests)

Start the backends first, then:

```bash
cd tests
chmod +x test_suite.sh

./test_suite.sh             # all 3 backends
./test_suite.sh python      # Python only  (port 5015)
./test_suite.sh nodejs      # Node.js only (port 5016)
./test_suite.sh golang      # Go only      (port 5017)
```

### Python curl Generator

```bash
cd tests

# Print curl commands (no server needed)
python3 generate_curl.py
python3 generate_curl.py --backend python

# Execute commands + verify status codes (server must be running)
python3 generate_curl.py --run
python3 generate_curl.py --run --backend golang
```

---

## Test Coverage

| Suite | File | Tests | Needs Server |
|-------|------|-------|-------------|
| pytest | `python/test_app.py` | 31 | No |
| Bash curl | `tests/test_suite.sh` | 18 × 3 = 54 | Yes |
| Python generator | `tests/generate_curl.py` | 18 × 3 = 54 | Optional |

### Test Cases Covered

| # | Test Case | Expected |
|---|-----------|----------|
| TC01 | GET /health | 200 |
| TC02 | GET /students (empty) | 200 |
| TC03 | POST /students (valid) | 201 |
| TC04 | GET /students/:id (found) | 200 |
| TC05 | GET /students/99999 (not found) | 404 |
| TC06 | POST — missing name | 400 |
| TC07 | POST — age < 15 | 400 |
| TC08 | POST — age > 100 | 400 |
| TC09 | POST — invalid email format | 400 |
| TC10 | POST — empty body | 400 |
| TC11 | POST — missing age | 400 |
| TC12 | POST — duplicate email | 409 |
| TC13 | PUT /students/:id (valid) | 200 |
| TC14 | PUT /students/99999 (not found) | 404 |
| TC15 | PUT — duplicate email | 409 |
| TC16 | DELETE /students/:id (success) | 200 |
| TC17 | DELETE /students/99999 (not found) | 404 |
| TC18 | GET /students (after changes) | 200 |

---

## Frontend

The `templates/` folder in each backend contains HTML UIs.  
Change the API port in the template to point to any backend:

```javascript
const API = 'http://localhost:5015';  // Python
const API = 'http://localhost:5016';  // Node.js
const API = 'http://localhost:5017';  // Go
```
