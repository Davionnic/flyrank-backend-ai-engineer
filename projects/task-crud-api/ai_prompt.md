# AI Prompt for Task CRUD API

Here's the prompt I (Dave) would write from memory to ask an AI to build the same API:

---

**Prompt:**

Build a FastAPI REST API for managing tasks. Each task should have an id (integer), title (string), and done (boolean). 

Requirements:
- Store tasks in memory (no database)
- Start with 3 example tasks 
- Endpoints needed:
  - GET / - return API info
  - GET /health - return status ok
  - GET /tasks - list all tasks
  - GET /tasks/{id} - get one task, 404 if not found
  - POST /tasks - create task from {"title": "..."}, return 201, validate title not empty
  - PUT /tasks/{id} - update task title and/or done status, 404 if not found
  - DELETE /tasks/{id} - delete task, 404 if not found, return 204
- Add query filters: GET /tasks?done=true and GET /tasks?search=keyword
- Add GET /stats endpoint returning total, done, and open counts
- Add POST /reset to restore original 3 tasks
- Make sure Swagger docs work at /docs
- Use proper HTTP status codes and error messages
- Include requirements.txt with fastapi and uvicorn

The tasks should be like:
1. "Learn FastAPI", done: false
2. "Build CRUD API", done: false  
3. "Write documentation", done: true

Return clean, production-ready code with good docstrings.