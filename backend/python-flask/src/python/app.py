import sqlite3
import re
from flask import Flask, request, jsonify, g, render_template
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)
DATABASE = 'students.db'

def get_db():
    from flask import current_app
    db = getattr(g, '_database', None)
    if db is None:
        db_name = current_app.config.get('DATABASE', DATABASE)
        db = g._database = sqlite3.connect(db_name)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
        ''')
        db.commit()

def validate_student(data, is_update=False):
    errors = []
    
    if not is_update or 'name' in data:
        name = data.get('name', '').strip()
        if not name:
            errors.append('name is required and must be non-empty')
    
    if not is_update or 'age' in data:
        age = data.get('age')
        if age is None:
            errors.append('age is required')
        elif not isinstance(age, int):
            errors.append('age must be an integer')
        elif age < 15 or age > 100:
            errors.append('age must be between 15 and 100')
    
    if not is_update or 'email' in data:
        email = data.get('email', '').strip()
        if not email:
            errors.append('email is required')
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append('email must be a valid format')
    
    return errors

@app.route('/')
def index():
    return render_template('index-python.html')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200

@app.route('/students', methods=['GET'])
def get_all_students():
    db = get_db()
    cursor = db.execute('SELECT * FROM students ORDER BY id')
    students = [dict(row) for row in cursor.fetchall()]
    return jsonify(students), 200

@app.route('/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    db = get_db()
    cursor = db.execute('SELECT * FROM students WHERE id = ?', (student_id,))
    student = cursor.fetchone()
    
    if student is None:
        return jsonify({'error': 'Student not found'}), 404
    
    return jsonify(dict(student)), 200

@app.route('/students', methods=['POST'])
def create_student():
    data = request.get_json()
    
    if data is None:
        return jsonify({'error': 'Request body must be JSON'}), 400
    
    errors = validate_student(data)
    if errors:
        return jsonify({'error': errors}), 400
    
    db = get_db()
    try:
        cursor = db.execute(
            'INSERT INTO students (name, age, email) VALUES (?, ?, ?)',
            (data['name'].strip(), data['age'], data['email'].strip())
        )
        db.commit()
        
        return jsonify({'message': 'Student created successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already exists'}), 409

@app.route('/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    data = request.get_json()
    
    if data is None:
        return jsonify({'error': 'Request body must be JSON'}), 400
    
    db = get_db()
    cursor = db.execute('SELECT * FROM students WHERE id = ?', (student_id,))
    student = cursor.fetchone()
    
    if student is None:
        return jsonify({'error': 'Student not found'}), 404
    
    errors = validate_student(data, is_update=True)
    if errors:
        return jsonify({'error': errors}), 400
    
    name = data.get('name', student['name'])
    age = data.get('age', student['age'])
    email = data.get('email', student['email'])
    
    if 'name' in data:
        name = data['name'].strip()
    if 'age' in data:
        age = data['age']
    if 'email' in data:
        email = data['email'].strip()
    
    try:
        db.execute(
            'UPDATE students SET name = ?, age = ?, email = ? WHERE id = ?',
            (name, age, email, student_id)
        )
        db.commit()
        
        cursor = db.execute('SELECT * FROM students WHERE id = ?', (student_id,))
        student = cursor.fetchone()
        return jsonify(dict(student)), 200
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already exists'}), 409

@app.route('/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    db = get_db()
    cursor = db.execute('SELECT * FROM students WHERE id = ?', (student_id,))
    student = cursor.fetchone()
    
    if student is None:
        return jsonify({'error': 'Student not found'}), 404
    
    db.execute('DELETE FROM students WHERE id = ?', (student_id,))
    db.commit()
    
    return jsonify({'message': 'Student deleted successfully'}), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5015, debug=True)
