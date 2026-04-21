const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const app = express();
const PORT = 5016;
const DB_PATH = path.join(__dirname, 'students.db');

app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

app.use(express.json());
app.use(express.static(path.join(__dirname, '../templates')));

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../templates/index-nodejs.html'));
});

const db = new sqlite3.Database(DB_PATH);

db.run(`
  CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    email TEXT UNIQUE NOT NULL
  )
`);

function validateStudent(data, isUpdate = false) {
  const errors = [];

  if (!isUpdate || 'name' in data) {
    const name = (data.name || '').trim();
    if (!name) errors.push('name is required and must be non-empty');
  }

  if (!isUpdate || 'age' in data) {
    const age = data.age;
    if (age === undefined) errors.push('age is required');
    else if (typeof age !== 'number') errors.push('age must be an integer');
    else if (age < 15 || age > 100) errors.push('age must be between 15 and 100');
  }

  if (!isUpdate || 'email' in data) {
    const email = (data.email || '').trim();
    if (!email) errors.push('email is required');
    else if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(email)) {
      errors.push('email must be a valid format');
    }
  }

  return errors;
}

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

app.get('/students', (req, res) => {
  db.all('SELECT * FROM students ORDER BY id', [], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

app.get('/students/:id', (req, res) => {
  db.get('SELECT * FROM students WHERE id = ?', [req.params.id], (err, row) => {
    if (err) return res.status(500).json({ error: err.message });
    if (!row) return res.status(404).json({ error: 'Student not found' });
    res.json(row);
  });
});

app.post('/students', (req, res) => {
  const data = req.body;
  const errors = validateStudent(data);
  if (errors.length) return res.status(400).json({ error: errors });

  db.run(
    'INSERT INTO students (name, age, email) VALUES (?, ?, ?)',
    [data.name.trim(), data.age, data.email.trim()],
    function(err) {
      if (err) {
        if (err.message.includes('UNIQUE')) {
          return res.status(409).json({ error: 'Email already exists' });
        }
        return res.status(500).json({ error: err.message });
      }
      res.status(201).json({ message: 'Student created successfully' });
    }
  );
});

app.put('/students/:id', (req, res) => {
  const data = req.body;
  const errors = validateStudent(data, true);
  if (errors.length) return res.status(400).json({ error: errors });

  db.get('SELECT * FROM students WHERE id = ?', [req.params.id], (err, student) => {
    if (err) return res.status(500).json({ error: err.message });
    if (!student) return res.status(404).json({ error: 'Student not found' });

    const name = data.name ? data.name.trim() : student.name;
    const age = data.age !== undefined ? data.age : student.age;
    const email = data.email ? data.email.trim() : student.email;

    db.run(
      'UPDATE students SET name = ?, age = ?, email = ? WHERE id = ?',
      [name, age, email, req.params.id],
      function(err) {
        if (err) {
          if (err.message.includes('UNIQUE')) {
            return res.status(409).json({ error: 'Email already exists' });
          }
          return res.status(500).json({ error: err.message });
        }
        db.get('SELECT * FROM students WHERE id = ?', [req.params.id], (err, row) => {
          res.json(row);
        });
      }
    );
  });
});

app.delete('/students/:id', (req, res) => {
  db.get('SELECT * FROM students WHERE id = ?', [req.params.id], (err, student) => {
    if (err) return res.status(500).json({ error: err.message });
    if (!student) return res.status(404).json({ error: 'Student not found' });

    db.run('DELETE FROM students WHERE id = ?', [req.params.id], (err) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ message: 'Student deleted successfully' });
    });
  });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Node.js server running on http://localhost:${PORT}`);
});
