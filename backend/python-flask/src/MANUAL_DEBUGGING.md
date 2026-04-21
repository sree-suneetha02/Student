# Manual Debugging Guide — Python, Node.js, Go

Step-by-step debugging for each language without any IDE.

---

## What is Manual Debugging?

Manual debugging means adding print/log statements to your code to see:
- What data is coming in
- What value a variable has
- Where exactly the code fails
- What path the code is taking

---

## 1. Python (Flask) Manual Debugging

### Step 1 — Add print() statements

Open `python/app.py` and add prints inside any function:

```python
@app.route('/students', methods=['POST'])
def create_student():
    data = request.get_json()

    print("=== CREATE STUDENT ===")
    print("Request data received:", data)          # see what came in

    if data is None:
        print("ERROR: No JSON body")
        return jsonify({'error': 'Request body must be JSON'}), 400

    errors = validate_student(data)
    print("Validation errors:", errors)             # see validation result

    if errors:
        return jsonify({'error': errors}), 400

    db = get_db()
    try:
        cursor = db.execute(
            'INSERT INTO students (name, age, email) VALUES (?, ?, ?)',
            (data['name'].strip(), data['age'], data['email'].strip())
        )
        db.commit()
        print("Student inserted, ID:", cursor.lastrowid)   # see new ID
        return jsonify({'message': 'Student created successfully'}), 201
    except sqlite3.IntegrityError as e:
        print("DB ERROR:", e)                        # see exact DB error
        return jsonify({'error': 'Email already exists'}), 409
```

### Step 2 — Run the server

```bash
cd backend/python-flask/src/python
python3 app.py
```

### Step 3 — Send a request

```bash
curl -X POST http://localhost:5015/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","age":22,"email":"alice@test.com"}'
```

### Step 4 — Read the terminal output

```
=== CREATE STUDENT ===
Request data received: {'name': 'Alice', 'age': 22, 'email': 'alice@test.com'}
Validation errors: []
Student inserted, ID: 1
```

If there is a bug, the print stops at the line that failed.

---

### Python Debug — Validation Function

Add prints inside `validate_student()`:

```python
def validate_student(data, is_update=False):
    errors = []
    print("--- Validating data:", data)

    if not is_update or 'name' in data:
        name = data.get('name', '').strip()
        print("  name value:", repr(name))
        if not name:
            errors.append('name is required and must be non-empty')

    if not is_update or 'age' in data:
        age = data.get('age')
        print("  age value:", age, "| type:", type(age))
        if age is None:
            errors.append('age is required')
        elif not isinstance(age, int):
            errors.append('age must be an integer')
        elif age < 15 or age > 100:
            errors.append('age must be between 15 and 100')

    if not is_update or 'email' in data:
        email = data.get('email', '').strip()
        print("  email value:", repr(email))

    print("--- Errors found:", errors)
    return errors
```

**Terminal output when age is wrong:**

```
--- Validating data: {'name': 'Alice', 'age': 5, 'email': 'alice@test.com'}
  name value: 'Alice'
  age value: 5 | type: <class 'int'>
  email value: 'alice@test.com'
--- Errors found: ['age must be between 15 and 100']
```

---

### Python Debug — Database Issues

```python
def init_db():
    with app.app_context():
        db = get_db()
        print("DB connected:", db)
        db.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
        ''')
        db.commit()
        print("Table created successfully")
```

---

### Python Debug — Run Tests with Print Output

By default pytest hides print output. Use `-s` flag to see it:

```bash
python3 -m pytest test_app.py -v -s
```

---

## 2. Node.js (Express) Manual Debugging

### Step 1 — Add console.log() statements

Open `nodejs/app.js` and add logs:

```js
app.post('/students', (req, res) => {
  const data = req.body;

  console.log('=== CREATE STUDENT ===');
  console.log('Request data:', data);               // see what came in
  console.log('Type of age:', typeof data.age);     // check type

  const errors = validateStudent(data);
  console.log('Validation errors:', errors);        // see validation result

  if (errors.length) return res.status(400).json({ error: errors });

  db.run(
    'INSERT INTO students (name, age, email) VALUES (?, ?, ?)',
    [data.name.trim(), data.age, data.email.trim()],
    function(err) {
      if (err) {
        console.log('DB ERROR:', err.message);       // see exact DB error
        if (err.message.includes('UNIQUE')) {
          return res.status(409).json({ error: 'Email already exists' });
        }
        return res.status(500).json({ error: err.message });
      }
      console.log('Student inserted, ID:', this.lastID);  // see new ID
      res.status(201).json({ message: 'Student created successfully' });
    }
  );
});
```

### Step 2 — Run the server

```bash
cd backend/python-flask/src/nodejs
node app.js
```

### Step 3 — Send a request

```bash
curl -X POST http://localhost:5016/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Bob","age":25,"email":"bob@test.com"}'
```

### Step 4 — Read the terminal output

```
=== CREATE STUDENT ===
Request data: { name: 'Bob', age: 25, email: 'bob@test.com' }
Type of age: number
Validation errors: []
Student inserted, ID: 1
```

---

### Node.js Debug — Validation Function

```js
function validateStudent(data, isUpdate = false) {
  const errors = [];
  console.log('--- Validating:', JSON.stringify(data));

  if (!isUpdate || 'name' in data) {
    const name = (data.name || '').trim();
    console.log('  name:', JSON.stringify(name));
    if (!name) errors.push('name is required and must be non-empty');
  }

  if (!isUpdate || 'age' in data) {
    const age = data.age;
    console.log('  age:', age, '| typeof:', typeof age);
    if (age === undefined)            errors.push('age is required');
    else if (typeof age !== 'number') errors.push('age must be an integer');
    else if (age < 15 || age > 100)   errors.push('age must be between 15 and 100');
  }

  if (!isUpdate || 'email' in data) {
    const email = (data.email || '').trim();
    console.log('  email:', JSON.stringify(email));
    if (!email) errors.push('email is required');
  }

  console.log('--- Errors:', errors);
  return errors;
}
```

**Terminal output when name is missing:**

```
--- Validating: {"age":22,"email":"x@test.com"}
  name: ""
  age: 22 | typeof: number
  email: "x@test.com"
--- Errors: [ 'name is required and must be non-empty' ]
```

---

### Node.js Debug — Use console.error() for Errors

```js
app.get('/students/:id', (req, res) => {
  const id = req.params.id;
  console.log('Fetching student with ID:', id);

  db.get('SELECT * FROM students WHERE id = ?', [id], (err, row) => {
    if (err) {
      console.error('DB query failed:', err);       // red output in terminal
      return res.status(500).json({ error: err.message });
    }
    if (!row) {
      console.log('Student not found for ID:', id);
      return res.status(404).json({ error: 'Student not found' });
    }
    console.log('Found student:', row);
    res.json(row);
  });
});
```

---

### Node.js Debug — Run Tests with Logs Visible

```bash
npm test -- --verbose
```

---

## 3. Go (Gin) Manual Debugging

### Step 1 — Add fmt.Println() statements

Open `golang/main.go` and add prints:

```go
import (
    "fmt"           // add this import
    "database/sql"
    ...
)

r.POST("/students", func(c *gin.Context) {
    var data map[string]interface{}
    if err := c.ShouldBindJSON(&data); err != nil {
        fmt.Println("ERROR: Could not parse JSON:", err)
        c.JSON(http.StatusBadRequest, gin.H{"error": "Request body must be JSON"})
        return
    }

    fmt.Println("=== CREATE STUDENT ===")
    fmt.Printf("Request data: %v\n", data)           // see what came in

    errors := validateStudent(data, false)
    fmt.Println("Validation errors:", errors)         // see validation result

    if len(errors) > 0 {
        c.JSON(http.StatusBadRequest, gin.H{"error": errors})
        return
    }

    name := data["name"].(string)
    age := int(data["age"].(float64))
    email := data["email"].(string)

    fmt.Printf("Inserting: name=%s age=%d email=%s\n", name, age, email)

    result, err := db.Exec(
        "INSERT INTO students (name, age, email) VALUES (?, ?, ?)",
        name, age, email,
    )
    if err != nil {
        fmt.Println("DB ERROR:", err)                 // see exact DB error
        c.JSON(http.StatusConflict, gin.H{"error": "Email already exists"})
        return
    }

    id, _ := result.LastInsertId()
    fmt.Println("Student inserted, ID:", id)           // see new ID

    c.JSON(http.StatusCreated, gin.H{"message": "Student created successfully"})
})
```

### Step 2 — Run the server

```bash
cd backend/python-flask/src/golang
go run main.go
```

### Step 3 — Send a request

```bash
curl -X POST http://localhost:5017/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Charlie","age":30,"email":"charlie@test.com"}'
```

### Step 4 — Read the terminal output

```
=== CREATE STUDENT ===
Request data: map[age:30 email:charlie@test.com name:Charlie]
Validation errors: []
Inserting: name=Charlie age=30 email=charlie@test.com
Student inserted, ID: 1
```

---

### Go Debug — Validation Function

```go
func validateStudent(data map[string]interface{}, isUpdate bool) []string {
    errors := []string{}
    fmt.Printf("--- Validating: %v\n", data)

    if !isUpdate || data["name"] != nil {
        name, ok := data["name"].(string)
        fmt.Printf("  name: %q  ok: %v\n", name, ok)
        if !ok || len(name) == 0 {
            errors = append(errors, "name is required and must be non-empty")
        }
    }

    if !isUpdate || data["age"] != nil {
        age := data["age"]
        fmt.Printf("  age: %v  type: %T\n", age, age)
        if age == nil {
            errors = append(errors, "age is required")
        } else {
            switch v := age.(type) {
            case float64:
                if v < 15 || v > 100 {
                    errors = append(errors, "age must be between 15 and 100")
                }
            default:
                errors = append(errors, "age must be an integer")
            }
        }
    }

    if !isUpdate || data["email"] != nil {
        email, ok := data["email"].(string)
        fmt.Printf("  email: %q  ok: %v\n", email, ok)
    }

    fmt.Println("--- Errors:", errors)
    return errors
}
```

**Terminal output when age is out of range:**

```
--- Validating: map[age:5 email:x@test.com name:Alice]
  name: "Alice"  ok: true
  age: 5  type: float64
  email: "x@test.com"  ok: true
--- Errors: [age must be between 15 and 100]
```

---

### Go Debug — Run Tests with Logs Visible

```bash
go test -v -count=1 ./...
```

The `-count=1` flag disables test result caching so tests always re-run.

---

## 4. Debugging Comparison Table

| What to debug | Python | Node.js | Go |
|---------------|--------|---------|-----|
| Print a value | `print(x)` | `console.log(x)` | `fmt.Println(x)` |
| Print formatted | `print(f"x={x}")` | `console.log('x=', x)` | `fmt.Printf("x=%v\n", x)` |
| Print an error | `print("ERR:", e)` | `console.error(e)` | `fmt.Println("ERR:", err)` |
| Print JSON/dict | `print(data)` | `console.log(JSON.stringify(data))` | `fmt.Printf("%v\n", data)` |
| Show variable type | `print(type(x))` | `console.log(typeof x)` | `fmt.Printf("%T\n", x)` |

---

## 5. Step-by-Step: Find a Bug Manually

### Example Bug: Student created with age=5 returns 201 instead of 400

**Step 1 — Reproduce the bug:**

```bash
curl -X POST http://localhost:5015/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","age":5,"email":"test@test.com"}'
```

Expected: `400 Bad Request`
Got: `201 Created` ← bug!

**Step 2 — Add prints at the entry point:**

```python
def create_student():
    data = request.get_json()
    print("DATA IN:", data)
    errors = validate_student(data)
    print("ERRORS:", errors)
```

**Step 3 — Run and check output:**

```
DATA IN: {'name': 'Test', 'age': 5, 'email': 'test@test.com'}
ERRORS: []          ← bug is here! Should not be empty
```

**Step 4 — Add prints inside validation:**

```python
def validate_student(data, is_update=False):
    age = data.get('age')
    print("AGE:", age, "TYPE:", type(age))
    print("CHECK: age < 15?", age < 15)
```

**Step 5 — Read output and find root cause:**

```
AGE: 5 TYPE: <class 'int'>
CHECK: age < 15? True
```

The condition is correct but the error is not being appended — check the if/elif chain for a logic error.

**Step 6 — Fix the bug, remove debug prints, re-test.**

---

## 6. Quick Debug Commands

```bash
# Python — run with visible prints
python3 app.py

# Python — test with visible prints
python3 -m pytest test_app.py -v -s

# Node.js — run with visible logs
node app.js

# Node.js — test with visible logs
npm test -- --verbose

# Go — run with visible prints
go run main.go

# Go — test with visible prints
go test -v -count=1 ./...
```
