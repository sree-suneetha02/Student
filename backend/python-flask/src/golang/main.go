package main

import (
	"database/sql"
	"net/http"
	"regexp"
	"time"

	"github.com/gin-gonic/gin"
	_ "github.com/mattn/go-sqlite3"
)

type Student struct {
	ID    int    `json:"id"`
	Name  string `json:"name"`
	Age   int    `json:"age"`
	Email string `json:"email"`
}

var db *sql.DB

func initDB(path string) {
	var err error
	db, err = sql.Open("sqlite3", path)
	if err != nil {
		panic(err)
	}
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS students (
			id    INTEGER PRIMARY KEY AUTOINCREMENT,
			name  TEXT    NOT NULL,
			age   INTEGER NOT NULL,
			email TEXT    UNIQUE NOT NULL
		)
	`)
	if err != nil {
		panic(err)
	}
}

func validateStudent(data map[string]interface{}, isUpdate bool) []string {
	errors := []string{}

	if !isUpdate || data["name"] != nil {
		name, ok := data["name"].(string)
		if !ok || len(name) == 0 {
			errors = append(errors, "name is required and must be non-empty")
		}
	}

	if !isUpdate || data["age"] != nil {
		age, ok := data["age"]
		if !ok {
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
		if !ok || len(email) == 0 {
			errors = append(errors, "email is required")
		} else {
			matched, _ := regexp.MatchString(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`, email)
			if !matched {
				errors = append(errors, "email must be a valid format")
			}
		}
	}

	return errors
}

func setupRouter() *gin.Engine {
	r := gin.Default()

	r.Use(func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Header("Access-Control-Allow-Headers", "Content-Type")
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(http.StatusOK)
			return
		}
		c.Next()
	})

	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":    "healthy",
			"timestamp": time.Now().UTC().Format(time.RFC3339),
		})
	})

	r.GET("/students", func(c *gin.Context) {
		rows, err := db.Query("SELECT * FROM students ORDER BY id")
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		defer rows.Close()

		students := []Student{}
		for rows.Next() {
			var s Student
			if err := rows.Scan(&s.ID, &s.Name, &s.Age, &s.Email); err == nil {
				students = append(students, s)
			}
		}
		c.JSON(http.StatusOK, students)
	})

	r.GET("/students/:id", func(c *gin.Context) {
		var s Student
		err := db.QueryRow("SELECT * FROM students WHERE id = ?", c.Param("id")).Scan(
			&s.ID, &s.Name, &s.Age, &s.Email,
		)
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "Student not found"})
			return
		}
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		c.JSON(http.StatusOK, s)
	})

	r.POST("/students", func(c *gin.Context) {
		var data map[string]interface{}
		if err := c.ShouldBindJSON(&data); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Request body must be JSON"})
			return
		}

		errors := validateStudent(data, false)
		if len(errors) > 0 {
			c.JSON(http.StatusBadRequest, gin.H{"error": errors})
			return
		}

		name := data["name"].(string)
		age := int(data["age"].(float64))
		email := data["email"].(string)

		_, err := db.Exec(
			"INSERT INTO students (name, age, email) VALUES (?, ?, ?)",
			name, age, email,
		)
		if err != nil {
			c.JSON(http.StatusConflict, gin.H{"error": "Email already exists"})
			return
		}
		c.JSON(http.StatusCreated, gin.H{"message": "Student created successfully"})
	})

	r.PUT("/students/:id", func(c *gin.Context) {
		var data map[string]interface{}
		if err := c.ShouldBindJSON(&data); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Request body must be JSON"})
			return
		}

		var current Student
		err := db.QueryRow("SELECT * FROM students WHERE id = ?", c.Param("id")).Scan(
			&current.ID, &current.Name, &current.Age, &current.Email,
		)
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "Student not found"})
			return
		}

		errors := validateStudent(data, true)
		if len(errors) > 0 {
			c.JSON(http.StatusBadRequest, gin.H{"error": errors})
			return
		}

		name := current.Name
		age := current.Age
		email := current.Email

		if n, ok := data["name"].(string); ok {
			name = n
		}
		if a, ok := data["age"].(float64); ok {
			age = int(a)
		}
		if e, ok := data["email"].(string); ok {
			email = e
		}

		_, err = db.Exec(
			"UPDATE students SET name = ?, age = ?, email = ? WHERE id = ?",
			name, age, email, c.Param("id"),
		)
		if err != nil {
			c.JSON(http.StatusConflict, gin.H{"error": "Email already exists"})
			return
		}

		var s Student
		db.QueryRow("SELECT * FROM students WHERE id = ?", c.Param("id")).Scan(
			&s.ID, &s.Name, &s.Age, &s.Email,
		)
		c.JSON(http.StatusOK, s)
	})

	r.DELETE("/students/:id", func(c *gin.Context) {
		var current Student
		err := db.QueryRow("SELECT * FROM students WHERE id = ?", c.Param("id")).Scan(
			&current.ID, &current.Name, &current.Age, &current.Email,
		)
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "Student not found"})
			return
		}
		db.Exec("DELETE FROM students WHERE id = ?", c.Param("id"))
		c.JSON(http.StatusOK, gin.H{"message": "Student deleted successfully"})
	})

	return r
}

func main() {
	initDB("./students.db")
	defer db.Close()
	r := setupRouter()
	r.LoadHTMLGlob("../templates/*")
	r.GET("/", func(c *gin.Context) {
		c.HTML(http.StatusOK, "index-golang.html", nil)
	})
	r.Run(":5017")
}
