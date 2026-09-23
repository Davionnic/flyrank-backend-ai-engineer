from fastapi import FastAPI, HTTPException
import uvicorn
import os
from typing import Optional
from pydantic import BaseModel

# Detect if running with PostgreSQL (Docker) or SQLite (local dev)
USE_POSTGRES = os.getenv("DATABASE_URL", "").startswith("postgresql://")

if USE_POSTGRES:
    from database import init_database, TaskRepository
else:
    import sqlite3
    DATABASE_PATH = "tasks.db"

app = FastAPI(
    title="Task API", 
    description="A simple CRUD API for managing tasks with PostgreSQL (Docker) or SQLite (local)",
    version="1.0"
)

# Track if database has been initialized
_db_initialized = False

def ensure_db_initialized():
    """Ensure database is initialized, call on first API request"""
    global _db_initialized
    if not _db_initialized:
        if USE_POSTGRES:
            init_database()
        else:
            init_sqlite_database()
        _db_initialized = True

def init_sqlite_database():
    """Create SQLite database and tasks table if they don't exist, seed with 3 tasks if table is empty"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create tasks table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    """)
    
    # Check if table is empty and seed with 3 tasks if so
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    
    if count == 0:
        seed_tasks = [
            ("Learn FastAPI", 0),
            ("Build CRUD API", 0),
            ("Write documentation", 1)
        ]
        cursor.executemany("INSERT INTO tasks (title, done) VALUES (?, ?)", seed_tasks)
        conn.commit()
    
    conn.close()

# Pydantic models
class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

@app.get("/")
def root():
    """Root endpoint returning API information"""
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def health():
    """Health check endpoint"""
    try:
        ensure_db_initialized()
        db_type = "PostgreSQL" if USE_POSTGRES else "SQLite"
        return {"status": "ok", "database": f"connected ({db_type})"}
    except Exception as e:
        return {"status": "error", "database": f"failed: {str(e)}"}

@app.get("/tasks")
def get_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    """Get all tasks with optional filtering by done status and title search"""
    ensure_db_initialized()
    
    if USE_POSTGRES:
        return TaskRepository.get_all_tasks(done=done, search=search)
    else:
        # SQLite implementation
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Build query with optional WHERE clauses
        query = "SELECT * FROM tasks"
        params = []
        where_clauses = []
        
        if done is not None:
            where_clauses.append("done = ?")
            params.append(int(done))
        
        if search:
            where_clauses.append("title LIKE ?")
            params.append(f"%{search}%")
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        tasks = []
        for row in rows:
            tasks.append({
                "id": row[0],
                "title": row[1],
                "done": bool(row[2])
            })
        
        conn.close()
        return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Get a single task by ID"""
    ensure_db_initialized()
    
    if USE_POSTGRES:
        task = TaskRepository.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        return task
    else:
        # SQLite implementation
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return {
            "id": row[0],
            "title": row[1],
            "done": bool(row[2])
        }

@app.post("/tasks", status_code=201)
def create_task(task_data: TaskCreate):
    """Create a new task"""
    if not task_data.title or not task_data.title.strip():
        raise HTTPException(status_code=400, detail="Title is required and cannot be empty")
    
    ensure_db_initialized()
    
    if USE_POSTGRES:
        return TaskRepository.create_task(task_data.title.strip())
    else:
        # SQLite implementation
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Insert new task with parameterized query, let DB assign id, set done=false
        cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (task_data.title.strip(), 0))
        task_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return {
            "id": task_id,
            "title": task_data.title.strip(),
            "done": False
        }

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_update: TaskUpdate):
    """Update an existing task"""
    # Validate title if provided
    if task_update.title is not None and not task_update.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    ensure_db_initialized()
    
    if USE_POSTGRES:
        title = task_update.title.strip() if task_update.title is not None else None
        task = TaskRepository.update_task(task_id, title=title, done=task_update.done)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        return task
    else:
        # SQLite implementation
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if task exists first
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        existing_task = cursor.fetchone()
        
        if not existing_task:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        # Build update query based on provided fields
        update_fields = []
        params = []
        
        if task_update.title is not None:
            update_fields.append("title = ?")
            params.append(task_update.title.strip())
        
        if task_update.done is not None:
            update_fields.append("done = ?")
            params.append(int(task_update.done))
        
        if update_fields:
            params.append(task_id)
            query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        # Get updated task
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        updated_row = cursor.fetchone()
        
        conn.close()
        
        return {
            "id": updated_row[0],
            "title": updated_row[1], 
            "done": bool(updated_row[2])
        }

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    """Delete a task"""
    ensure_db_initialized()
    
    if USE_POSTGRES:
        if not TaskRepository.delete_task(task_id):
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    else:
        # SQLite implementation
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if task exists first
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        existing_task = cursor.fetchone()
        
        if not existing_task:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        # Delete the task
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()

@app.get("/stats")
def get_stats():
    """Get task statistics"""
    ensure_db_initialized()
    
    if USE_POSTGRES:
        return TaskRepository.get_task_stats()
    else:
        # SQLite implementation
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM tasks")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE done=1")
        done = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total": total,
            "done": done,
            "open": total - done
        }

@app.post("/reset")
def reset_tasks():
    """Reset tasks to the original 3 seed tasks"""
    ensure_db_initialized()
    
    if USE_POSTGRES:
        tasks = TaskRepository.reset_tasks()
        return {"message": "Tasks reset to seed data", "tasks": tasks}
    else:
        # SQLite implementation
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Clear all tasks
        cursor.execute("DELETE FROM tasks")
        
        # Re-add seed tasks
        seed_tasks = [
            ("Learn FastAPI", 0),
            ("Build CRUD API", 0),
            ("Write documentation", 1)
        ]
        cursor.executemany("INSERT INTO tasks (title, done) VALUES (?, ?)", seed_tasks)
        
        conn.commit()
        
        # Get the reset tasks
        cursor.execute("SELECT * FROM tasks")
        rows = cursor.fetchall()
        tasks = []
        for row in rows:
            tasks.append({
                "id": row[0],
                "title": row[1],
                "done": bool(row[2])
            })
        
        conn.close()
        
        return {"message": "Tasks reset to seed data", "tasks": tasks}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)