# Python vs Go vs Node.js — Student API Comparison

## 1. Language & Framework

| Aspect        | Python (Flask)         | Go (Gin)               | Node.js (Express)       |
|---------------|------------------------|------------------------|-------------------------|
| Language type | Interpreted, dynamic   | Compiled, static       | Interpreted, dynamic    |
| Framework     | Flask                  | Gin                    | Express                 |
| Port          | 5015                   | 5017                   | 5016                    |
| Typing        | Duck typing            | Strong static types    | Duck typing             |

---

## 2. How the Server Starts

**Python**
```python
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5015, debug=True)
```
- Database is initialized before the server starts.
- Single-threaded by default (dev mode).

**Go**
```go
func main() {
    initDB()
    defer db.Close()
    r := gin.Default()
    r.Run(":5017")
}
```
- Compiled to a binary — no interpreter needed at runtime.
- Handles many concurrent requests natively (goroutines).

**Node.js**
```js
app.listen(PORT, '0.0.0.0', () => {
    console.log(`Node.js server running on http://localhost:${PORT}`);
});
```
- Event-loop based — non-blocking I/O by default.
- Database is created at module load time (top-level `db.run`).

---

## 3. Database Connection

| Aspect           | Python                        | Go                         | Node.js                   |
|------------------|-------------------------------|----------------------------|---------------------------|
| DB library       | `sqlite3` (built-in)          | `go-sqlite3` (CGo)         | `sqlite3` (npm package)   |
| Connection style | Per-request via Flask `g`     | Single global `*sql.DB`    | Single global `Database`  |
| Connection close | `@teardown_appcontext`        | `defer db.Close()`         | Not explicitly closed      |

---

## 4. Defining the Student

**Python** — no explicit model, rows returned as `dict`:
```python
db.row_factory = sqlite3.Row
student = dict(cursor.fetchone())
```

**Go** — explicit struct with JSON tags:
```go
type Student struct {
    ID    int    `json:"id"`
    Name  string `json:"name"`
    Age   int    `json:"age"`
    Email string `json:"email"`
}
```

**Node.js** — no model, rows returned as plain JS objects:
```js
db.get('SELECT * FROM students WHERE id = ?', [id], (err, row) => {
    res.json(row);
});
```

---

## 5. Request Handling Style

**Python** — synchronous, decorator-based routing:
```python
@app.route('/students', methods=['POST'])
def create_student():
    data = request.get_json()
```

**Go** — synchronous, handler functions (but goroutine-concurrent):
```go
r.POST("/students", func(c *gin.Context) {
    var data map[string]interface{}
    c.ShouldBindJSON(&data)
})
```

**Node.js** — asynchronous, callback-based:
```js
app.post('/students', (req, res) => {
    db.run('INSERT ...', [...], function(err) {
        res.status(201).json(...)
    });
});
```

---

## 6. Validation

All three implement the same rules manually:
- `name` — required, non-empty string
- `age` — integer, 15–100
- `email` — required, valid format, unique

The key difference is **type checking**:

| Language  | Age type check                         |
|-----------|----------------------------------------|
| Python    | `isinstance(age, int)`                 |
| Go        | JSON numbers arrive as `float64`       |
| Node.js   | `typeof age !== 'number'`              |

---

## 7. Error Handling

**Python** — try/except:
```python
try:
    cursor = db.execute('INSERT ...')
except sqlite3.IntegrityError:
    return jsonify({'error': 'Email already exists'}), 409
```

**Go** — error return values (no exceptions):
```go
_, err = db.Exec("INSERT ...")
if err != nil {
    c.JSON(http.StatusConflict, gin.H{"error": "Email already exists"})
}
```

**Node.js** — error-first callbacks:
```js
db.run('INSERT ...', [...], function(err) {
    if (err && err.message.includes('UNIQUE')) {
        return res.status(409).json({ error: 'Email already exists' });
    }
});
```

---

## 8. Performance Characteristics

| Aspect              | Python (Flask)    | Go (Gin)          | Node.js (Express) |
|---------------------|-------------------|-------------------|-------------------|
| Startup time        | Slow              | Very fast         | Fast              |
| Memory usage        | High              | Low               | Medium            |
| Concurrency model   | Threads (WSGI)    | Goroutines        | Event loop        |
| Raw throughput      | Low               | Very high         | High              |
| Ease of development | Easiest           | Moderate          | Easy              |

---

## 9. Testing

| Aspect        | Python              | Go                    | Node.js               |
|---------------|---------------------|-----------------------|-----------------------|
| Test file     | `test_app.py`       | (manual/curl)         | `test_app.js`         |
| Framework     | pytest              | —                     | Jest + Supertest      |
| DB for tests  | Temp file (mkstemp) | —                     | In-memory (`:memory:`) |
| Test count    | 31                  | —                     | 31                    |
| Run command   | `pytest test_app.py`| —                     | `npm test`            |

---

## 10. Summary

| Want...                        | Use          |
|--------------------------------|--------------|
| Fastest development speed      | Python       |
| Best runtime performance       | Go           |
| Large npm ecosystem / JS stack | Node.js      |
| Type safety                    | Go           |
| Simplest syntax                | Python       |
| Non-blocking I/O by default    | Node.js      |
