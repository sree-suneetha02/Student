# VSCode Debugging & Running Guide

All 3 backends — Python (Flask), Node.js (Express), Go (Gin)

---

## 1. VSCode Extensions to Install

| Extension | Purpose |
|-----------|---------|
| **Python** (Microsoft) | Python debugging, IntelliSense |
| **Go** (Google) | Go debugging, IntelliSense |
| **ESLint** | Node.js code quality |
| **REST Client** | Test API directly from VSCode |

Install via: `Ctrl+Shift+X` → search and install each

---

## 2. launch.json — Debug All 3 Languages

Create this file at the root of your project:
`.vscode/launch.json`

```json
{
  "version": "0.2.0",
  "configurations": [

    {
      "name": "Python: Flask",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/backend/python-flask/src/python/app.py",
      "console": "integratedTerminal",
      "env": {
        "FLASK_ENV": "development",
        "FLASK_DEBUG": "1"
      },
      "args": []
    },

    {
      "name": "Node.js: Express",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/backend/python-flask/src/nodejs/app.js",
      "console": "integratedTerminal",
      "restart": true
    },

    {
      "name": "Go: Gin",
      "type": "go",
      "request": "launch",
      "mode": "auto",
      "program": "${workspaceFolder}/backend/python-flask/src/golang/main.go",
      "console": "integratedTerminal"
    }

  ]
}
```

---

## 3. How to Set a Breakpoint

1. Open any source file (e.g. `app.py`)
2. Click the **red dot** to the left of a line number
3. The dot turns red = breakpoint is set
4. Press **F5** to start debugging
5. When the code hits that line, execution **pauses**

### What you can do when paused:

| Action | Key | What it does |
|--------|-----|-------------|
| Continue | F5 | Run until next breakpoint |
| Step Over | F10 | Run current line, go to next |
| Step Into | F11 | Enter the function being called |
| Step Out | Shift+F11 | Exit current function |
| Stop | Shift+F5 | Stop the debugger |

---

## 4. Python (Flask) — Port 5015

### Run in Terminal

```bash
cd backend/python-flask/src/python
pip install -r ../requirements.txt
python3 app.py
```

Server starts at: `http://localhost:5015`

### Run Tests

```bash
python3 -m pytest test_app.py -v
```

### Debug in VSCode

1. Open `python/app.py`
2. Set a breakpoint — example: line inside `create_student()` function
3. Press **F5** → select **"Python: Flask"**
4. Send a request:
   ```bash
   curl -X POST http://localhost:5015/students \
     -H "Content-Type: application/json" \
     -d '{"name":"Alice","age":22,"email":"alice@test.com"}'
   ```
5. VSCode pauses at your breakpoint
6. See variables in the **Variables** panel on the left

### Debug Panel — What to Watch

```
Variables:
  data = {'name': 'Alice', 'age': 22, 'email': 'alice@test.com'}
  errors = []
```

---

## 5. Node.js (Express) — Port 5016

### Run in Terminal

```bash
cd backend/python-flask/src/nodejs
npm install
node app.js
```

Server starts at: `http://localhost:5016`

### Run Tests

```bash
npm test
```

### Debug in VSCode

1. Open `nodejs/app.js`
2. Set a breakpoint — example: inside `app.post('/students', ...)` handler
3. Press **F5** → select **"Node.js: Express"**
4. Send a request:
   ```bash
   curl -X POST http://localhost:5016/students \
     -H "Content-Type: application/json" \
     -d '{"name":"Bob","age":25,"email":"bob@test.com"}'
   ```
5. Execution pauses at breakpoint
6. Inspect `data`, `errors`, `req.body` in the Variables panel

### Debug Panel — What to Watch

```
Variables:
  data = { name: 'Bob', age: 25, email: 'bob@test.com' }
  errors = []
```

---

## 6. Go (Gin) — Port 5017

### Run in Terminal

```bash
cd backend/python-flask/src/golang
go mod tidy
go run main.go
```

Server starts at: `http://localhost:5017`

### Run Tests

```bash
go test -v ./...
```

### Debug in VSCode

1. Install **Delve** (Go debugger):
   ```bash
   go install github.com/go-delve/delve/cmd/dlv@latest
   ```
2. Open `golang/main.go`
3. Set a breakpoint — example: inside the `r.POST("/students", ...)` handler
4. Press **F5** → select **"Go: Gin"**
5. Send a request:
   ```bash
   curl -X POST http://localhost:5017/students \
     -H "Content-Type: application/json" \
     -d '{"name":"Charlie","age":30,"email":"charlie@test.com"}'
   ```
6. Execution pauses — inspect `name`, `age`, `email`, `errors`

### Debug Panel — What to Watch

```
Variables:
  data = map[age:30 email:charlie@test.com name:Charlie]
  errors = []
  name = "Charlie"
  age = 30
```

---

## 7. Debug the Tests (not just the server)

### Python Tests

1. Open `python/test_app.py`
2. Set a breakpoint inside any test function
3. In VSCode: click **Testing** icon (beaker) on the left sidebar
4. Click the **play** button next to the test
5. Execution pauses at your breakpoint

### Node.js Tests

1. Open `nodejs/test_app.js`
2. Set a breakpoint inside any test
3. Add this to `launch.json`:
   ```json
   {
     "name": "Node.js: Jest Tests",
     "type": "node",
     "request": "launch",
     "program": "${workspaceFolder}/backend/python-flask/src/nodejs/node_modules/.bin/jest",
     "args": ["--runInBand"],
     "cwd": "${workspaceFolder}/backend/python-flask/src/nodejs",
     "console": "integratedTerminal"
   }
   ```
4. Press **F5** → select **"Node.js: Jest Tests"**

### Go Tests

1. Open `golang/main_test.go`
2. Click **"debug test"** link that appears above each test function
3. VSCode runs only that test with the debugger attached

---

## 8. Quick Reference — All Commands

### Run Servers

| Language | Command | Port |
|----------|---------|------|
| Python | `python3 app.py` | 5015 |
| Node.js | `node app.js` | 5016 |
| Go | `go run main.go` | 5017 |

### Run Tests

| Language | Command | Tests |
|----------|---------|-------|
| Python | `python3 -m pytest test_app.py -v` | 31 |
| Node.js | `npm test` | 31 |
| Go | `go test -v ./...` | 31 |
| All 3 | `./run_all_tests.sh` | 93 |

### Test a Running Server (curl)

```bash
# Health check
curl http://localhost:5015/health   # Python
curl http://localhost:5016/health   # Node.js
curl http://localhost:5017/health   # Go

# Create student
curl -X POST http://localhost:5015/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","age":22,"email":"alice@example.com"}'

# Get all students
curl http://localhost:5015/students

# Get one student
curl http://localhost:5015/students/1

# Update student
curl -X PUT http://localhost:5015/students/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice Updated"}'

# Delete student
curl -X DELETE http://localhost:5015/students/1
```

---

## 9. Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Address already in use` | Port is busy | Kill old process: `lsof -ti:5015 \| xargs kill` |
| `ModuleNotFoundError` | Missing Python package | `pip install -r requirements.txt` |
| `Cannot find module` | Missing npm package | `npm install` |
| `go: command not found` | Go not installed | Install from golang.org |
| `dlv: command not found` | Delve not installed | `go install github.com/go-delve/delve/cmd/dlv@latest` |
| `sqlite3: no such table` | DB not initialized | Restart the server (initDB runs on start) |
