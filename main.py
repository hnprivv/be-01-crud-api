from fastapi import FastAPI, HTTPException

app = FastAPI()

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