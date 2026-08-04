from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from pydantic import BaseModel, Field
import sqlite3

# Stage 0 - Fetching the database
def get_db():
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    """)
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count == 0:
        conn.executemany("INSERT INTO tasks (title, done) VALUES (?, ?)", [
            ("Task #1", False),
            ("Task #2", False),
            ("Task #3", True)
        ])
        conn.commit()
    conn.close()

class Task(BaseModel):
    title: str = Field(min_length=1)
    done: bool = False

app = FastAPI()

init_db()

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()})

INITIAL_TASKS = [
    {"id": 1, "title": "Task #1", "done": False},
    {"id": 2, "title": "Task #2", "done": False},
    {"id": 3, "title": "Task #3", "done": True},
]
db = [task.copy() for task in INITIAL_TASKS]

# Stage 1 - H (Health Check)
@app.get("/")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health():
    return {"status": "ok"}

# Optionals
@app.get("/tasks/stats")
def get_task_stats():
    total_tasks = len(db)
    completed_tasks = sum(1 for task in db if task["done"])
    pending_tasks = total_tasks - completed_tasks
    return {
        "total": total_tasks,
        "done": completed_tasks,
        "open": pending_tasks
    }

@app.post("/tasks/reset", status_code=204)
def reset_tasks():
    global db
    db = [task.copy() for task in INITIAL_TASKS]

# Stage 2 - R (Read)
@app.get("/tasks/{id}")
def get_task(id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (id,)).fetchone()
    conn.close()

    if row is None:
        return JSONResponse(status_code=404, content={"error": "Task not found"})    
    return {"task": dict(row)}

@app.get("/tasks")
def get_tasks(done: bool = None, q: str = None, limit: int = 2, offset: int = 2):
    conn = get_db()
    rows = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()

    filtered_tasks = [dict(row) for row in rows]

    if done is not None:
        filtered_tasks = [task for task in filtered_tasks if task["done"] == done]
    if q is not None:
        filtered_tasks = [task for task in filtered_tasks if q.lower() in task["title"].lower()]
    if not filtered_tasks:
        return JSONResponse(status_code=404, content={"error": "No tasks found"})

    total_tasks = len(filtered_tasks)
    paginated_tasks = filtered_tasks[offset:offset + limit]

    return {"tasks": paginated_tasks, "total": total_tasks, "limit": limit, "offset": offset}

# Stage 3 - C (Create)
@app.post("/tasks", status_code=201)
def create_task(task: Task):
    conn = get_db()
    cursor = conn.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (task.title, task.done))
    conn.commit()
    new_task_id = cursor.lastrowid
    conn.close()
    new_task = {"id": new_task_id, "title": task.title, "done": task.done}
    return {"task": new_task}

# Stage 4 - U/D (Update/Delete)
@app.put("/tasks/{id}")
def update_task(id: int, task: Task):
    for existing_task in db:
        if existing_task["id"] == id:
            existing_task["title"] = task.title
            existing_task["done"] = task.done
            return {"task": existing_task}
    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})

@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    for i, task in enumerate(db):
        if task["id"] == id:
            del db[i]
            return
    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})