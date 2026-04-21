/**
 * Student API — Node.js/Express Test Suite
 * 31 test cases using Jest + Supertest
 * Uses an in-memory SQLite DB — no server needed
 *
 * Run:  npm test
 */

const request = require('supertest');
const express = require('express');
const sqlite3 = require('sqlite3').verbose();

// ── Build a fresh app instance backed by in-memory SQLite ──

function buildApp() {
  const app = express();
  app.use(express.json());

  const db = new sqlite3.Database(':memory:');

  db.serialize(() => {
    db.run(`
      CREATE TABLE IF NOT EXISTS students (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT    NOT NULL,
        age        INTEGER NOT NULL,
        email      TEXT    UNIQUE NOT NULL
      )
    `);
  });

  function validateStudent(data, isUpdate = false) {
    const errors = [];
    if (!isUpdate || 'name' in data) {
      const name = (data.name || '').trim();
      if (!name) errors.push('name is required and must be non-empty');
    }
    if (!isUpdate || 'age' in data) {
      const age = data.age;
      if (age === undefined)           errors.push('age is required');
      else if (typeof age !== 'number') errors.push('age must be an integer');
      else if (age < 15 || age > 100)  errors.push('age must be between 15 and 100');
    }
    if (!isUpdate || 'email' in data) {
      const email = (data.email || '').trim();
      if (!email) errors.push('email is required');
      else if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(email))
        errors.push('email must be a valid format');
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
      if (err)  return res.status(500).json({ error: err.message });
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
      function (err) {
        if (err) {
          if (err.message.includes('UNIQUE'))
            return res.status(409).json({ error: 'Email already exists' });
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
      if (err)      return res.status(500).json({ error: err.message });
      if (!student) return res.status(404).json({ error: 'Student not found' });

      const name  = data.name  ? data.name.trim()  : student.name;
      const age   = data.age  !== undefined ? data.age   : student.age;
      const email = data.email ? data.email.trim() : student.email;

      db.run(
        'UPDATE students SET name = ?, age = ?, email = ? WHERE id = ?',
        [name, age, email, req.params.id],
        function (err) {
          if (err) {
            if (err.message.includes('UNIQUE'))
              return res.status(409).json({ error: 'Email already exists' });
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
      if (err)      return res.status(500).json({ error: err.message });
      if (!student) return res.status(404).json({ error: 'Student not found' });

      db.run('DELETE FROM students WHERE id = ?', [req.params.id], (err) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ message: 'Student deleted successfully' });
      });
    });
  });

  return { app, db };
}

// ── Helper ────────────────────────────────────────────────────

function createStudent(agent, name = 'Alice', age = 22, email = 'alice@test.com') {
  return agent.post('/students').send({ name, age, email });
}

async function createStudentId(agent, name = 'Alice', age = 22, email = 'alice@test.com') {
  await createStudent(agent, name, age, email);
  const res = await agent.get('/students');
  return res.body.find(s => s.email === email).id;
}

// ════════════════════════════════════════════════════════════
// TC01 – TC02 : Health
// ════════════════════════════════════════════════════════════

describe('Health', () => {
  let agent;
  beforeAll(() => { agent = request(buildApp().app); });

  test('TC01 GET /health returns 200', async () => {
    const res = await agent.get('/health');
    expect(res.statusCode).toBe(200);
  });

  test('TC02 GET /health body has status:healthy and timestamp', async () => {
    const res = await agent.get('/health');
    expect(res.body.status).toBe('healthy');
    expect(res.body.timestamp).toBeDefined();
  });
});

// ════════════════════════════════════════════════════════════
// TC03 – TC05 : GET /students
// ════════════════════════════════════════════════════════════

describe('GET /students', () => {
  let agent;
  beforeAll(() => { agent = request(buildApp().app); });

  test('TC03 returns 200 with empty array on fresh DB', async () => {
    const res = await agent.get('/students');
    expect(res.statusCode).toBe(200);
    expect(res.body).toEqual([]);
  });

  test('TC04 returns 200 with array after insert', async () => {
    await createStudent(agent);
    const res = await agent.get('/students');
    expect(res.statusCode).toBe(200);
    expect(res.body.length).toBe(1);
  });

  test('TC05 multiple students returned ordered by id', async () => {
    await createStudent(agent, 'Bob', 25, 'bob@test.com');
    const res = await agent.get('/students');
    expect(res.body.length).toBeGreaterThanOrEqual(2);
    expect(res.body[0].id).toBeLessThan(res.body[1].id);
  });
});

// ════════════════════════════════════════════════════════════
// TC06 – TC08 : GET /students/:id
// ════════════════════════════════════════════════════════════

describe('GET /students/:id', () => {
  let agent;
  let studentId;

  beforeAll(async () => {
    agent = request(buildApp().app);
    studentId = await createStudentId(agent);
  });

  test('TC06 returns 200 for existing student', async () => {
    const res = await agent.get(`/students/${studentId}`);
    expect(res.statusCode).toBe(200);
    expect(res.body.name).toBe('Alice');
  });

  test('TC07 returns 404 for non-existent student', async () => {
    const res = await agent.get('/students/99999');
    expect(res.statusCode).toBe(404);
  });

  test('TC08 404 response body contains error key', async () => {
    const res = await agent.get('/students/99999');
    expect(res.body).toHaveProperty('error');
  });
});

// ════════════════════════════════════════════════════════════
// TC09 – TC18 : POST /students
// ════════════════════════════════════════════════════════════

describe('POST /students', () => {
  let agent;
  beforeEach(() => { agent = request(buildApp().app); });

  test('TC09 valid student returns 201', async () => {
    const res = await createStudent(agent);
    expect(res.statusCode).toBe(201);
  });

  test('TC10 response contains message', async () => {
    const res = await createStudent(agent);
    expect(res.body).toHaveProperty('message');
  });

  test('TC11 missing name returns 400', async () => {
    const res = await agent.post('/students').send({ age: 20, email: 'x@test.com' });
    expect(res.statusCode).toBe(400);
  });

  test('TC12 age below 15 returns 400', async () => {
    const res = await agent.post('/students')
      .send({ name: 'Kid', age: 10, email: 'kid@test.com' });
    expect(res.statusCode).toBe(400);
  });

  test('TC13 age above 100 returns 400', async () => {
    const res = await agent.post('/students')
      .send({ name: 'Elder', age: 150, email: 'elder@test.com' });
    expect(res.statusCode).toBe(400);
  });

  test('TC14 invalid email format returns 400', async () => {
    const res = await agent.post('/students')
      .send({ name: 'Dave', age: 25, email: 'not-an-email' });
    expect(res.statusCode).toBe(400);
  });

  test('TC15 empty body returns 400', async () => {
    const res = await agent.post('/students').send({});
    expect(res.statusCode).toBe(400);
  });

  test('TC16 missing age returns 400', async () => {
    const res = await agent.post('/students')
      .send({ name: 'Eve', email: 'eve@test.com' });
    expect(res.statusCode).toBe(400);
  });

  test('TC17 duplicate email returns 409', async () => {
    await createStudent(agent);
    const res = await agent.post('/students')
      .send({ name: 'Alice2', age: 23, email: 'alice@test.com' });
    expect(res.statusCode).toBe(409);
  });

  test('TC18 multiple validation errors returned as array', async () => {
    const res = await agent.post('/students').send({ age: 5 });
    expect(res.statusCode).toBe(400);
    expect(Array.isArray(res.body.error)).toBe(true);
    expect(res.body.error.length).toBeGreaterThanOrEqual(2);
  });
});

// ════════════════════════════════════════════════════════════
// TC19 – TC23 : PUT /students/:id
// ════════════════════════════════════════════════════════════

describe('PUT /students/:id', () => {
  let agent;
  let aliceId;
  let bobId;

  beforeEach(async () => {
    agent = request(buildApp().app);
    aliceId = await createStudentId(agent, 'Alice', 22, 'alice@test.com');
    bobId   = await createStudentId(agent, 'Bob',   28, 'bob@test.com');
  });

  test('TC19 valid update returns 200', async () => {
    const res = await agent.put(`/students/${aliceId}`)
      .send({ name: 'Alice Updated', age: 24 });
    expect(res.statusCode).toBe(200);
  });

  test('TC20 response reflects updated values', async () => {
    const res = await agent.put(`/students/${aliceId}`)
      .send({ name: 'New Name' });
    expect(res.body.name).toBe('New Name');
  });

  test('TC21 update non-existent student returns 404', async () => {
    const res = await agent.put('/students/99999').send({ name: 'Ghost' });
    expect(res.statusCode).toBe(404);
  });

  test('TC22 update with duplicate email returns 409', async () => {
    const res = await agent.put(`/students/${aliceId}`)
      .send({ email: 'bob@test.com' });
    expect(res.statusCode).toBe(409);
  });

  test('TC23 partial update preserves other fields', async () => {
    await agent.put(`/students/${aliceId}`).send({ name: 'Changed' });
    const res = await agent.get(`/students/${aliceId}`);
    expect(res.body.age).toBe(22);
    expect(res.body.email).toBe('alice@test.com');
  });
});

// ════════════════════════════════════════════════════════════
// TC24 – TC27 : DELETE /students/:id
// ════════════════════════════════════════════════════════════

describe('DELETE /students/:id', () => {
  let agent;
  let studentId;

  beforeEach(async () => {
    agent = request(buildApp().app);
    studentId = await createStudentId(agent);
  });

  test('TC24 delete existing student returns 200', async () => {
    const res = await agent.delete(`/students/${studentId}`);
    expect(res.statusCode).toBe(200);
  });

  test('TC25 deleted student is no longer found', async () => {
    await agent.delete(`/students/${studentId}`);
    const res = await agent.get(`/students/${studentId}`);
    expect(res.statusCode).toBe(404);
  });

  test('TC26 delete non-existent student returns 404', async () => {
    const res = await agent.delete('/students/99999');
    expect(res.statusCode).toBe(404);
  });

  test('TC27 delete response contains message', async () => {
    const res = await agent.delete(`/students/${studentId}`);
    expect(res.body).toHaveProperty('message');
  });
});

// ════════════════════════════════════════════════════════════
// TC28 – TC31 : Age boundary & validation format
// ════════════════════════════════════════════════════════════

describe('Validation — boundaries & error format', () => {
  let agent;
  beforeEach(() => { agent = request(buildApp().app); });

  test('TC28 age exactly 15 is valid (boundary)', async () => {
    const res = await agent.post('/students')
      .send({ name: 'Young', age: 15, email: 'young@test.com' });
    expect(res.statusCode).toBe(201);
  });

  test('TC29 age exactly 100 is valid (boundary)', async () => {
    const res = await agent.post('/students')
      .send({ name: 'Senior', age: 100, email: 'senior@test.com' });
    expect(res.statusCode).toBe(201);
  });

  test('TC30 age 14 is invalid', async () => {
    const res = await agent.post('/students')
      .send({ name: 'X', age: 14, email: 'x@test.com' });
    expect(res.statusCode).toBe(400);
  });

  test('TC31 age 101 is invalid', async () => {
    const res = await agent.post('/students')
      .send({ name: 'X', age: 101, email: 'x@test.com' });
    expect(res.statusCode).toBe(400);
  });
});
