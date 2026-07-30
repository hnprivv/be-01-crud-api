from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from pydantic import BaseModel

class Task(BaseModel):
    title: str
    done: bool = False

app = FastAPI()

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()})

db = [
    {"id": 1, "title": "Task #1", "done": False},
    {"id": 2, "title": "Task #2", "done": False},
    {"id": 3, "title": "Task #3", "done": True},
]

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

# Stage 2 - R (Read)
@app.get("/tasks/{id}")
def get_task(id: int):
    for task in db:
        if task["id"] == id:
            return {"task": task}
    raise HTTPException(status_code=404, detail=f"Task {id} not found")

@app.get("/tasks")
def get_tasks(done: bool = None, q: str = None):
    filtered_tasks = db
    if done is not None:
        filtered_tasks = [task for task in filtered_tasks if task["done"] == done]
    if q is not None:
        filtered_tasks = [task for task in filtered_tasks if q.lower() in task["title"].lower()]
    if not filtered_tasks:
        raise HTTPException(status_code=404, detail="No tasks found")
    return {"tasks": filtered_tasks}

# Stage 3 - C (Create)
@app.post("/tasks", status_code=201)
def create_task(task: Task):
    new_id = max((task["id"] for task in db), default=0) + 1
    new_task = {"id": new_id, "title": task.title, "done": task.done}
    db.append(new_task)
    return {"task": new_task}

# Stage 4 - U/D (Update/Delete)
@app.put("/tasks/{id}")
def update_task(id: int, task: Task):
    for existing_task in db:
        if existing_task["id"] == id:
            existing_task["title"] = task.title
            existing_task["done"] = task.done
            return {"task": existing_task}
    raise HTTPException(status_code=404, detail=f"Task {id} not found")

@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    for i, task in enumerate(db):
        if task["id"] == id:
            del db[i]
            return
    raise HTTPException(status_code=404, detail=f"Task {id} not found")