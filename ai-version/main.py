from typing import Optional

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

app = FastAPI(title="Task CRUD API")


class Task(BaseModel):
    id: int
    title: str
    completed: bool = False


class TaskCreate(BaseModel):
    title: str = Field(min_length=1)
    completed: bool = False


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    completed: Optional[bool] = None


def default_tasks() -> list[dict]:
    return [
        {"id": 1, "title": "Buy groceries", "completed": False},
        {"id": 2, "title": "Clean the house", "completed": False},
        {"id": 3, "title": "Read a book", "completed": True},
    ]


tasks: list[dict] = default_tasks()
next_id: int = 4


@app.get("/")
def api_description():
    return {
        "name": "Task CRUD API",
        "description": "A simple in-memory to-do list API",
        "endpoints": {
            "GET /health": "Health check",
            "GET /tasks": "List tasks, optionally filtered by 'completed' and/or 'keyword' query params",
            "GET /tasks/{task_id}": "Get a single task by id",
            "GET /tasks/stats": "Get counts of total, completed, and pending tasks",
            "POST /tasks": "Create a new task",
            "PUT /tasks/{task_id}": "Update an existing task",
            "DELETE /tasks/{task_id}": "Delete a task",
            "POST /tasks/reset": "Reset tasks back to the original 3 tasks",
        },
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/tasks/stats")
def get_task_stats():
    total = len(tasks)
    completed = sum(1 for t in tasks if t["completed"])
    return {"total": total, "completed": completed, "pending": total - completed}


@app.get("/tasks", response_model=list[Task])
def get_tasks(
    completed: Optional[bool] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
):
    result = tasks

    if completed is not None:
        result = [t for t in result if t["completed"] == completed]

    if keyword is not None:
        if not keyword.strip():
            raise HTTPException(status_code=400, detail="keyword must not be empty")
        result = [t for t in result if keyword.lower() in t["title"].lower()]

    return result


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task_in: TaskCreate):
    global next_id

    if not task_in.title.strip():
        raise HTTPException(status_code=400, detail="title must not be empty")

    task = {"id": next_id, "title": task_in.title, "completed": task_in.completed}
    tasks.append(task)
    next_id += 1
    return task


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_in: TaskUpdate):
    if task_in.title is None and task_in.completed is None:
        raise HTTPException(status_code=400, detail="no fields provided to update")

    if task_in.title is not None and not task_in.title.strip():
        raise HTTPException(status_code=400, detail="title must not be empty")

    for task in tasks:
        if task["id"] == task_id:
            if task_in.title is not None:
                task["title"] = task_in.title
            if task_in.completed is not None:
                task["completed"] = task_in.completed
            return task

    raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            return

    raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")


@app.post("/tasks/reset", response_model=list[Task])
def reset_tasks():
    global tasks, next_id
    tasks = default_tasks()
    next_id = 4
    return tasks
