import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import List, Dict, Any, Optional

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/tasks")

@contextmanager
def get_db_connection():
    """Get a database connection with automatic cleanup"""
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        yield conn
    finally:
        if conn:
            conn.close()

def init_database():
    """Initialize database by creating tables and seeding data if needed"""
    import time
    max_retries = 10
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Create tasks table if it doesn't exist
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS tasks (
                            id SERIAL PRIMARY KEY,
                            title VARCHAR(255) NOT NULL,
                            done BOOLEAN DEFAULT FALSE
                        );
                    """)
                    
                    # Check if table is empty and seed with initial data
                    cursor.execute("SELECT COUNT(*) FROM tasks")
                    count = cursor.fetchone()[0]
                    
                    if count == 0:
                        # Seed with 3 initial tasks
                        seed_tasks = [
                            ("Learn FastAPI", False),
                            ("Build CRUD API", False), 
                            ("Write documentation", True)
                        ]
                        
                        cursor.executemany(
                            "INSERT INTO tasks (title, done) VALUES (%s, %s)",
                            seed_tasks
                        )
                
                conn.commit()
                print("Database initialized successfully")
                return  # Success, exit retry loop
                
        except Exception as e:
            print(f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Database initialization failed.")
                raise

class TaskRepository:
    """Repository class for task operations"""
    
    @staticmethod
    def get_all_tasks(done: Optional[bool] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all tasks with optional filtering"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = "SELECT id, title, done FROM tasks"
                params = []
                conditions = []
                
                if done is not None:
                    conditions.append("done = %s")
                    params.append(done)
                
                if search:
                    conditions.append("title ILIKE %s")
                    params.append(f"%{search}%")
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY id"
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_task_by_id(task_id: int) -> Optional[Dict[str, Any]]:
        """Get a single task by ID"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT id, title, done FROM tasks WHERE id = %s", (task_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
    
    @staticmethod
    def create_task(title: str) -> Dict[str, Any]:
        """Create a new task"""
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done",
                    (title, False)
                )
                row = cursor.fetchone()
                conn.commit()
                return dict(row)
    
    @staticmethod
    def update_task(task_id: int, title: Optional[str] = None, done: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        """Update an existing task"""
        # First check if task exists
        if not TaskRepository.get_task_by_id(task_id):
            return None
            
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                updates = []
                params = []
                
                if title is not None:
                    updates.append("title = %s")
                    params.append(title)
                
                if done is not None:
                    updates.append("done = %s")
                    params.append(done)
                
                if not updates:
                    # No updates, just return current task
                    return TaskRepository.get_task_by_id(task_id)
                
                params.append(task_id)
                query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = %s RETURNING id, title, done"
                
                cursor.execute(query, params)
                row = cursor.fetchone()
                conn.commit()
                return dict(row) if row else None
    
    @staticmethod
    def delete_task(task_id: int) -> bool:
        """Delete a task by ID"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
                deleted = cursor.rowcount > 0
                conn.commit()
                return deleted
    
    @staticmethod
    def get_task_stats() -> Dict[str, int]:
        """Get task statistics"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE done = true) as done,
                        COUNT(*) FILTER (WHERE done = false) as open
                    FROM tasks
                """)
                row = cursor.fetchone()
                return {
                    "total": row[0],
                    "done": row[1], 
                    "open": row[2]
                }
    
    @staticmethod
    def reset_tasks():
        """Reset tasks to seed data"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Clear existing tasks
                cursor.execute("DELETE FROM tasks")
                
                # Reset the sequence
                cursor.execute("ALTER SEQUENCE tasks_id_seq RESTART WITH 1")
                
                # Insert seed tasks
                seed_tasks = [
                    ("Learn FastAPI", False),
                    ("Build CRUD API", False),
                    ("Write documentation", True)
                ]
                
                cursor.executemany(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s)",
                    seed_tasks
                )
                
                conn.commit()
                
        return TaskRepository.get_all_tasks()