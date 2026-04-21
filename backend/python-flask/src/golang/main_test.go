package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
)

func setupTestRouter() *gin.Engine {
	gin.SetMode(gin.TestMode)
	initDB(":memory:")
	return setupRouter()
}

func post(r *gin.Engine, body string) *httptest.ResponseRecorder {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/students", bytes.NewBufferString(body))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)
	return w
}

func createAlice(r *gin.Engine) *httptest.ResponseRecorder {
	return post(r, `{"name":"Alice","age":22,"email":"alice@test.com"}`)
}

func getStudentID(r *gin.Engine, email string) int {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/students", nil)
	r.ServeHTTP(w, req)
	var students []map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &students)
	for _, s := range students {
		if s["email"] == email {
			return int(s["id"].(float64))
		}
	}
	return -1
}

// ── TC01–TC02: Health ─────────────────────────────────────────

func TestTC01_HealthReturns200(t *testing.T) {
	r := setupTestRouter()
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/health", nil)
	r.ServeHTTP(w, req)
	if w.Code != 200 {
		t.Errorf("expected 200, got %d", w.Code)
	}
}

func TestTC02_HealthBodyHasStatusHealthy(t *testing.T) {
	r := setupTestRouter()
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/health", nil)
	r.ServeHTTP(w, req)
	var body map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &body)
	if body["status"] != "healthy" {
		t.Errorf("expected status=healthy, got %v", body["status"])
	}
	if body["timestamp"] == nil {
		t.Error("expected timestamp field")
	}
}

// ── TC03–TC05: GET /students ──────────────────────────────────

func TestTC03_EmptyListOnFreshDB(t *testing.T) {
	r := setupTestRouter()
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/students", nil)
	r.ServeHTTP(w, req)
	if w.Code != 200 {
		t.Errorf("expected 200, got %d", w.Code)
	}
	var body []interface{}
	json.Unmarshal(w.Body.Bytes(), &body)
	if len(body) != 0 {
		t.Errorf("expected empty list, got %d items", len(body))
	}
}

func TestTC04_ReturnsListAfterInsert(t *testing.T) {
	r := setupTestRouter()
	createAlice(r)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/students", nil)
	r.ServeHTTP(w, req)
	var body []interface{}
	json.Unmarshal(w.Body.Bytes(), &body)
	if len(body) != 1 {
		t.Errorf("expected 1 student, got %d", len(body))
	}
}

func TestTC05_MultipleStudentsOrderedByID(t *testing.T) {
	r := setupTestRouter()
	createAlice(r)
	post(r, `{"name":"Bob","age":25,"email":"bob@test.com"}`)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/students", nil)
	r.ServeHTTP(w, req)
	var body []map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &body)
	if len(body) != 2 {
		t.Fatalf("expected 2 students, got %d", len(body))
	}
	if body[0]["name"] != "Alice" || body[1]["name"] != "Bob" {
		t.Error("students not in expected order")
	}
}

// ── TC06–TC08: GET /students/:id ─────────────────────────────

func TestTC06_GetExistingStudent(t *testing.T) {
	r := setupTestRouter()
	createAlice(r)
	id := getStudentID(r, "alice@test.com")
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", fmt.Sprintf("/students/%d", id), nil)
	r.ServeHTTP(w, req)
	if w.Code != 200 {
		t.Errorf("expected 200, got %d", w.Code)
	}
}

func TestTC07_GetNonExistentStudentReturns404(t *testing.T) {
	r := setupTestRouter()
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/students/99999", nil)
	r.ServeHTTP(w, req)
	if w.Code != 404 {
		t.Errorf("expected 404, got %d", w.Code)
	}
}

func TestTC08_404BodyHasErrorKey(t *testing.T) {
	r := setupTestRouter()
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/students/99999", nil)
	r.ServeHTTP(w, req)
	var body map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &body)
	if body["error"] == nil {
		t.Error("expected error key in body")
	}
}

// ── TC09–TC18: POST /students ─────────────────────────────────

func TestTC09_ValidCreateReturns201(t *testing.T) {
	r := setupTestRouter()
	w := createAlice(r)
	if w.Code != 201 {
		t.Errorf("expected 201, got %d", w.Code)
	}
}

func TestTC10_ResponseContainsMessage(t *testing.T) {
	r := setupTestRouter()
	w := createAlice(r)
	var body map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &body)
	if body["message"] == nil {
		t.Error("expected message key in response")
	}
}

func TestTC11_MissingNameReturns400(t *testing.T) {
	r := setupTestRouter()
	w := post(r, `{"age":20,"email":"x@test.com"}`)
	if w.Code != 400 {
		t.Errorf("expected 400, got %d", w.Code)
	}
}

func TestTC12_AgeBelowMinimumReturns400(t *testing.T) {
	r := setupTestRouter()
	w := post(r, `{"name":"Kid","age":10,"email":"kid@test.com"}`)
	if w.Code != 400 {
		t.Errorf("expected 400, got %d", w.Code)
	}
}

func TestTC13_AgeAboveMaximumReturns400(t *testing.T) {
	r := setupTestRouter()
	w := post(r, `{"name":"Elder","age":150,"email":"elder@test.com"}`)
	if w.Code != 400 {
		t.Errorf("expected 400, got %d", w.Code)
	}
}

func TestTC14_InvalidEmailFormatReturns400(t *testing.T) {
	r := setupTestRouter()
	w := post(r, `{"name":"Dave","age":25,"email":"not-an-email"}`)
	if w.Code != 400 {
		t.Errorf("expected 400, got %d", w.Code)
	}
}

func TestTC15_EmptyBodyReturns400(t *testing.T) {
	r := setupTestRouter()
	w := post(r, `{}`)
	if w.Code != 400 {
		t.Errorf("expected 400, got %d", w.Code)
	}
}

func TestTC16_MissingAgeReturns400(t *testing.T) {
	r := setupTestRouter()
	w := post(r, `{"name":"Eve","email":"eve@test.com"}`)
	if w.Code != 400 {
		t.Errorf("expected 400, got %d", w.Code)
	}
}

func TestTC17_DuplicateEmailReturns409(t *testing.T) {
	r := setupTestRouter()
	createAlice(r)
	w := post(r, `{"name":"Alice2","age":23,"email":"alice@test.com"}`)
	if w.Code != 409 {
		t.Errorf("expected 409, got %d", w.Code)
	}
}

func TestTC18_MultipleValidationErrorsReturnedAsList(t *testing.T) {
	r := setupTestRouter()
	w := post(r, `{"age":5}`)
	if w.Code != 400 {
		t.Errorf("expected 400, got %d", w.Code)
	}
	var body map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &body)
	errs, ok := body["error"].([]interface{})
	if !ok || len(errs) < 2 {
		t.Errorf("expected list of >= 2 errors, got %v", body["error"])
	}
}

// ── TC19–TC23: PUT /students/:id ─────────────────────────────

func TestTC19_ValidUpdateReturns200(t *testing.T) {
	r := setupTestRouter()
	createAlice(r)
	id := getStudentID(r, "alice@test.com")
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("PUT", fmt.Sprintf("/students/%d", id),
		bytes.NewBufferString(`{"name":"Alice Updated","age":24}`))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)
	if w.Code != 200 {
		t.Errorf("expected 200, got %d", w.Code)
	}
}

func TestTC20_ResponseReflectsUpdatedValues(t *testing.T) {
	r := setupTestRouter()
	createAlice(r)
	id := getStudentID(r, "alice@test.com")
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("PUT", fmt.Sprintf("/students/%d", id),
		bytes.NewBufferString(`{"name":"NewName"}`))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)
	var body map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &body)
	if body["name"] != "NewName" {
		t.Errorf("expected name=NewName, got %v", body["name"])
	}
}

func TestTC21_UpdateNonExistentReturns404(t *testing.T) {
	r := setupTestRouter()
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("PUT", "/students/99999",
		bytes.NewBufferString(`{"name":"Ghost"}`))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)
	if w.Code != 404 {
		t.Errorf("expected 404, got %d", w.Code)
	}
}

func TestTC22_UpdateDuplicateEmailReturns409(t *testing.T) {
	r := setupTestRouter()
	createAlice(r)
	post(r, `{"name":"Bob","age":28,"email":"bob@test.com"}`)
	aliceID := getStudentID(r, "alice@test.com")
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("PUT", fmt.Sprintf("/students/%d", aliceID),
		bytes.NewBufferString(`{"email":"bob@test.com"}`))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)
	if w.Code != 409 {
		t.Errorf("expected 409, got %d", w.Code)
	}
}

func TestTC23_PartialUpdatePreservesOtherFields(t *testing.T) {
	r := setupTestRouter()
	createAlice(r)
	id := getStudentID(r, "alice@test.com")
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("PUT", fmt.Sprintf("/students/%d", id),
		bytes.NewBufferString(`{"name":"Changed"}`))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)
	var body map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &body)
	if body["age"].(float64) != 22 {
		t.Errorf("expected age=22, got %v", body["age"])
	}
	if body["email"] != "alice@test.com" {
		t.Errorf("expected original email, got %v", body["email"])
	}
}

// ── TC24–TC27: DELETE /students/:id ──────────────────────────

func TestTC24_DeleteExistingReturns200(t *testing.T) {
	r := setupTestRouter()
	createAlice(r)
	id := getStudentID(r, "alice@test.com")
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("DELETE", fmt.Sprintf("/students/%d", id), nil)
	r.ServeHTTP(w, req)
	if w.Code != 200 {
		t.Errorf("expected 200, got %d", w.Code)
	}
}

func TestTC25_DeletedStudentNoLongerFound(t *testing.T) {
	r := setupTestRouter()
	createAlice(r)
	id := getStudentID(r, "alice@test.com")
	req, _ := http.NewRequest("DELETE", fmt.Sprintf("/students/%d", id), nil)
	r.ServeHTTP(httptest.NewRecorder(), req)
	w := httptest.NewRecorder()
	req2, _ := http.NewRequest("GET", fmt.Sprintf("/students/%d", id), nil)
	r.ServeHTTP(w, req2)
	if w.Code != 404 {
		t.Errorf("expected 404 after delete, got %d", w.Code)
	}
}

func TestTC26_DeleteNonExistentReturns404(t *testing.T) {
	r := setupTestRouter()
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("DELETE", "/students/99999", nil)
	r.ServeHTTP(w, req)
	if w.Code != 404 {
		t.Errorf("expected 404, got %d", w.Code)
	}
}

func TestTC27_DeleteResponseHasMessage(t *testing.T) {
	r := setupTestRouter()
	createAlice(r)
	id := getStudentID(r, "alice@test.com")
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("DELETE", fmt.Sprintf("/students/%d", id), nil)
	r.ServeHTTP(w, req)
	var body map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &body)
	if body["message"] == nil {
		t.Error("expected message key in delete response")
	}
}

// ── TC28–TC31: Age boundary & validation ─────────────────────

func TestTC28_AgeExactly15IsValid(t *testing.T) {
	r := setupTestRouter()
	w := post(r, `{"name":"Young","age":15,"email":"young@test.com"}`)
	if w.Code != 201 {
		t.Errorf("expected 201, got %d", w.Code)
	}
}

func TestTC29_AgeExactly100IsValid(t *testing.T) {
	r := setupTestRouter()
	w := post(r, `{"name":"Senior","age":100,"email":"senior@test.com"}`)
	if w.Code != 201 {
		t.Errorf("expected 201, got %d", w.Code)
	}
}

func TestTC30_Age14IsInvalid(t *testing.T) {
	r := setupTestRouter()
	w := post(r, `{"name":"X","age":14,"email":"x@test.com"}`)
	if w.Code != 400 {
		t.Errorf("expected 400, got %d", w.Code)
	}
}

func TestTC31_Age101IsInvalid(t *testing.T) {
	r := setupTestRouter()
	w := post(r, `{"name":"X","age":101,"email":"x@test.com"}`)
	if w.Code != 400 {
		t.Errorf("expected 400, got %d", w.Code)
	}
}
