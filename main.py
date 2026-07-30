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

@app.get("/")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tasks")
def get_tasks():
    return {"tasks": db}

@app.get("/tasks/{id}")
def get_task(id: int):
    for task in db:
        if task["id"] == id:
            return {"task": task}
    raise HTTPException(status_code=404, detail=f"Task {id} not found")

@app.post("/tasks", status_code=201)
def create_task(task: Task):
    new_id = max((task["id"] for task in db), default=0) + 1
    new_task = {"id": new_id, "title": task.title, "done": task.done}
    db.append(new_task)
    return {"task": new_task}