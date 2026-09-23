# Task API - Containerized with PostgreSQL

A FastAPI-based CRUD API for managing tasks with **PostgreSQL in Docker** as the primary deployment method and SQLite fallback for local development. This implements the FlyRank BE-04 containerization requirements.

## 🚀 Quick Setup (Docker - Recommended)

**One-command setup:**

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Start the entire stack:
```bash
docker compose up
```

That's it! The API will be available at `http://localhost:8000` and interactive docs at `http://localhost:8000/docs`.

## 📦 Deployment Options

### Option 1: Docker Compose (Primary/Production)
- **Database**: PostgreSQL 15 in container
- **Persistence**: Docker named volume
- **Setup**: `docker compose up`
- **Use case**: Production, team development

### Option 2: Local Development (Fallback)
- **Database**: SQLite (`tasks.db`)  
- **Persistence**: Local file
- **Setup**: `pip install -r requirements.txt && python main.py`
- **Use case**: Local development without Docker

The application **automatically detects** which mode to use based on the `DATABASE_URL` environment variable.

## 📋 Environment Variables

| Variable | Description | Docker Default | Local Fallback |
|----------|-------------|----------------|-----------------|
| `DATABASE_URL` | Database connection string | `postgresql://postgres:postgres@172.17.0.1:5432/tasks` | None (uses SQLite) |

## 🔌 API Endpoints

| Method | Endpoint | Description | Status Codes |
|--------|----------|-------------|--------------|
| GET | `/` | API information | 200 |
| GET | `/health` | Health check with database type | 200 |
| GET | `/tasks` | Get all tasks (supports `?done=true/false` and `?search=text`) | 200 |
| GET | `/tasks/{id}` | Get single task by ID | 200, 404 |
| POST | `/tasks` | Create new task | 201, 400 |
| PUT | `/tasks/{id}` | Update existing task | 200, 400, 404 |
| DELETE | `/tasks/{id}` | Delete task by ID | 204, 404 |
| GET | `/stats` | Get task statistics | 200 |
| POST | `/reset` | Reset to seed data | 200 |

## 🧪 API Examples

### Health Check (shows database type)
```bash
curl -i http://localhost:8000/health
```
```
HTTP/1.1 200 OK
date: Wed, 23 Sep 2026 10:14:22 GMT
server: uvicorn
content-length: 55
content-type: application/json

{"status":"ok","database":"connected (PostgreSQL)"}
```

### Get All Tasks
```bash
curl http://localhost:8000/tasks
```

### Create a New Task
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn Docker"}'
```

### Update a Task
```bash
curl -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Master Docker", "done": true}'
```

### Delete a Task
```bash
curl -X DELETE http://localhost:8000/tasks/1 -i
```

### Filter Tasks
```bash
# Get completed tasks
curl "http://localhost:8000/tasks?done=true"

# Search tasks
curl "http://localhost:8000/tasks?search=Docker"
```

## 🐳 Docker Architecture

### Services
- **api**: FastAPI application container (Python 3.12-slim)
- **db**: PostgreSQL 15 database container

### Networking
- Containers communicate via Docker network
- API connects to database using host gateway IP (`172.17.0.1:5432`)
- API exposed on host port 8000
- Database exposed on host port 5432 for development access

### Storage
- PostgreSQL data persisted in named volume `postgres_data`
- Data survives container restarts and updates

## 🔄 Data Persistence Verification

To verify data persists across container restarts:

1. Create some tasks:
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Persistence test"}'
```

2. Stop the stack:
```bash
docker compose down
```

3. Restart the stack:
```bash
docker compose up -d
```

4. Verify data is still there:
```bash
curl http://localhost:8000/tasks
```

The tasks should still be present, confirming persistence works.

## 🗄️ Database Schema

Both PostgreSQL and SQLite use the same schema:

```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,          -- INTEGER PRIMARY KEY for SQLite
    title VARCHAR(255) NOT NULL,    -- TEXT NOT NULL for SQLite  
    done BOOLEAN DEFAULT FALSE      -- BOOLEAN DEFAULT 0 for SQLite
);
```

### Sample Data
The application automatically seeds both databases with 3 initial tasks:
1. "Learn FastAPI" (not done)
2. "Build CRUD API" (not done)  
3. "Write documentation" (done)

## 🛠️ Local Development

### With Docker (Recommended)
```bash
cp .env.example .env
docker compose up
```

### Without Docker (SQLite fallback)
```bash
# Install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt

# Run directly (will use SQLite)
python main.py
```

### Database Management

#### PostgreSQL (Docker)
```bash
# Connect to database
docker compose exec db psql -U postgres -d tasks

# View logs
docker compose logs db
```

#### SQLite (Local)
```bash
# Database file is created as tasks.db
sqlite3 tasks.db ".schema"
```

#### Reset to seed data (both)
```bash
curl -X POST http://localhost:8000/reset
```

## 🎯 Production Notes

- **Recommended**: Use Docker Compose deployment
- Default PostgreSQL credentials are for development only
- For production: use strong passwords, secrets management
- Consider non-root container user for production
- SQLite fallback is suitable for development/testing only

## 🔍 Implementation Details

### Database Detection
The app detects PostgreSQL vs SQLite based on `DATABASE_URL`:
- If `DATABASE_URL` starts with `postgresql://` → PostgreSQL mode
- Otherwise → SQLite mode  

### Error Handling
- Consistent 404 responses for missing tasks
- Validation for empty/missing titles
- Database connection retry logic (PostgreSQL)
- Graceful fallback between database types

### API Compatibility
Both database backends provide identical API responses and behavior.

---

**Built with FastAPI, PostgreSQL, SQLite, Docker, and Docker Compose**  
*FlyRank BE-04 Implementation - Containerized Stack*