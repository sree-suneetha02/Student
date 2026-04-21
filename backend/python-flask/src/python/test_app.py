import pytest
import json
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from app import app, init_db


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    app.config['TESTING'] = True
    app.config['DATABASE'] = db_path
    with app.app_context():
        init_db()
    with app.test_client() as c:
        yield c
    os.close(db_fd)
    os.unlink(db_path)


def create_student(client, name='Alice', age=22, email='alice@test.com'):
    return client.post('/students',
                       data=json.dumps({'name': name, 'age': age, 'email': email}),
                       content_type='application/json')

def create_student_id(client, name='Alice', age=22, email='alice@test.com'):
    create_student(client, name, age, email)
    students = client.get('/students').get_json()
    return next(s['id'] for s in students if s['email'] == email)


# ════════════════════════════════════════════════════════════
# TC01 – TC02 : Health & index
# ════════════════════════════════════════════════════════════

class TestHealth:
    def test_tc01_health_returns_200(self, client):
        res = client.get('/health')
        assert res.status_code == 200

    def test_tc02_health_body_has_status_healthy(self, client):
        res = client.get('/health')
        body = res.get_json()
        assert body['status'] == 'healthy'
        assert 'timestamp' in body


# ════════════════════════════════════════════════════════════
# TC03 – TC05 : GET /students
# ════════════════════════════════════════════════════════════

class TestGetAllStudents:
    def test_tc03_empty_list_on_fresh_db(self, client):
        res = client.get('/students')
        assert res.status_code == 200
        assert res.get_json() == []

    def test_tc04_returns_list_after_insert(self, client):
        create_student(client)
        res = client.get('/students')
        assert res.status_code == 200
        assert len(res.get_json()) == 1

    def test_tc05_multiple_students_ordered_by_id(self, client):
        create_student(client, name='Alice', email='alice@test.com')
        create_student(client, name='Bob',   email='bob@test.com')
        data = client.get('/students').get_json()
        assert len(data) == 2
        assert data[0]['name'] == 'Alice'
        assert data[1]['name'] == 'Bob'


# ════════════════════════════════════════════════════════════
# TC06 – TC08 : GET /students/:id
# ════════════════════════════════════════════════════════════

class TestGetStudentById:
    def test_tc06_get_existing_student(self, client):
        sid = create_student_id(client)
        res = client.get(f'/students/{sid}')
        assert res.status_code == 200
        assert res.get_json()['name'] == 'Alice'

    def test_tc07_get_nonexistent_student_returns_404(self, client):
        res = client.get('/students/99999')
        assert res.status_code == 404

    def test_tc08_404_body_has_error_key(self, client):
        res = client.get('/students/99999')
        assert 'error' in res.get_json()


# ════════════════════════════════════════════════════════════
# TC09 – TC16 : POST /students (create)
# ════════════════════════════════════════════════════════════

class TestCreateStudent:
    def test_tc09_valid_create_returns_201(self, client):
        res = create_student(client)
        assert res.status_code == 201

    def test_tc10_response_contains_message(self, client):
        body = create_student(client).get_json()
        assert 'message' in body

    def test_tc11_missing_name_returns_400(self, client):
        res = client.post('/students',
                          data=json.dumps({'age': 20, 'email': 'x@test.com'}),
                          content_type='application/json')
        assert res.status_code == 400

    def test_tc12_age_below_minimum_returns_400(self, client):
        res = client.post('/students',
                          data=json.dumps({'name': 'Kid', 'age': 10, 'email': 'kid@test.com'}),
                          content_type='application/json')
        assert res.status_code == 400

    def test_tc13_age_above_maximum_returns_400(self, client):
        res = client.post('/students',
                          data=json.dumps({'name': 'Elder', 'age': 150, 'email': 'old@test.com'}),
                          content_type='application/json')
        assert res.status_code == 400

    def test_tc14_invalid_email_format_returns_400(self, client):
        res = client.post('/students',
                          data=json.dumps({'name': 'Dave', 'age': 25, 'email': 'not-an-email'}),
                          content_type='application/json')
        assert res.status_code == 400

    def test_tc15_empty_body_returns_400(self, client):
        res = client.post('/students',
                          data=json.dumps({}),
                          content_type='application/json')
        assert res.status_code == 400

    def test_tc16_missing_age_returns_400(self, client):
        res = client.post('/students',
                          data=json.dumps({'name': 'Eve', 'email': 'eve@test.com'}),
                          content_type='application/json')
        assert res.status_code == 400

    def test_tc17_duplicate_email_returns_409(self, client):
        create_student(client)
        res = client.post('/students',
                          data=json.dumps({'name': 'Alice2', 'age': 23, 'email': 'alice@test.com'}),
                          content_type='application/json')
        assert res.status_code == 409

    def test_tc18_no_content_type_returns_400(self, client):
        res = client.post('/students', data='{"name":"X","age":20,"email":"x@test.com"}')
        assert res.status_code in (400, 415)


# ════════════════════════════════════════════════════════════
# TC19 – TC23 : PUT /students/:id (update)
# ════════════════════════════════════════════════════════════

class TestUpdateStudent:
    def test_tc19_valid_update_returns_200(self, client):
        sid = create_student_id(client)
        res = client.put(f'/students/{sid}',
                         data=json.dumps({'name': 'Alice Updated', 'age': 24}),
                         content_type='application/json')
        assert res.status_code == 200

    def test_tc20_response_reflects_updated_values(self, client):
        sid = create_student_id(client)
        res = client.put(f'/students/{sid}',
                         data=json.dumps({'name': 'NewName'}),
                         content_type='application/json')
        assert res.get_json()['name'] == 'NewName'

    def test_tc21_update_nonexistent_returns_404(self, client):
        res = client.put('/students/99999',
                         data=json.dumps({'name': 'Ghost'}),
                         content_type='application/json')
        assert res.status_code == 404

    def test_tc22_update_duplicate_email_returns_409(self, client):
        create_student(client, name='Alice', email='alice@test.com')
        sid2 = create_student_id(client, name='Bob', email='bob@test.com')
        res = client.put(f'/students/{sid2}',
                         data=json.dumps({'email': 'alice@test.com'}),
                         content_type='application/json')
        assert res.status_code == 409

    def test_tc23_partial_update_preserves_other_fields(self, client):
        sid = create_student_id(client)
        client.put(f'/students/{sid}',
                   data=json.dumps({'name': 'Changed'}),
                   content_type='application/json')
        body = client.get(f'/students/{sid}').get_json()
        assert body['age'] == 22
        assert body['email'] == 'alice@test.com'


# ════════════════════════════════════════════════════════════
# TC24 – TC27 : DELETE /students/:id
# ════════════════════════════════════════════════════════════

class TestDeleteStudent:
    def test_tc24_delete_existing_returns_200(self, client):
        sid = create_student_id(client)
        res = client.delete(f'/students/{sid}')
        assert res.status_code == 200

    def test_tc25_deleted_student_no_longer_found(self, client):
        sid = create_student_id(client)
        client.delete(f'/students/{sid}')
        assert client.get(f'/students/{sid}').status_code == 404

    def test_tc26_delete_nonexistent_returns_404(self, client):
        res = client.delete('/students/99999')
        assert res.status_code == 404

    def test_tc27_delete_response_has_message(self, client):
        sid = create_student_id(client)
        body = client.delete(f'/students/{sid}').get_json()
        assert 'message' in body


# ════════════════════════════════════════════════════════════
# TC28 – TC30 : Validation error format
# ════════════════════════════════════════════════════════════

class TestValidationErrorFormat:
    def test_tc28_error_key_present_on_400(self, client):
        res = client.post('/students',
                          data=json.dumps({}),
                          content_type='application/json')
        assert 'error' in res.get_json()

    def test_tc29_multiple_errors_returned_as_list(self, client):
        res = client.post('/students',
                          data=json.dumps({'age': 5}),
                          content_type='application/json')
        body = res.get_json()
        assert isinstance(body['error'], list)
        assert len(body['error']) >= 2

    def test_tc30_age_boundary_exactly_15_is_valid(self, client):
        res = client.post('/students',
                          data=json.dumps({'name': 'Young', 'age': 15, 'email': 'y@test.com'}),
                          content_type='application/json')
        assert res.status_code == 201

    def test_tc31_age_boundary_exactly_100_is_valid(self, client):
        res = client.post('/students',
                          data=json.dumps({'name': 'Old', 'age': 100, 'email': 'old@test.com'}),
                          content_type='application/json')
        assert res.status_code == 201
