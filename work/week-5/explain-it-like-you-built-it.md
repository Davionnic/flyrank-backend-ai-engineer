# Explain It Like You Built It

**Dave Andrei Almia Gallo · Backend AI Engineer @ FlyRank · Week 5**

**Build piece:** In-memory task storage + auto-increment IDs in my W2 Task CRUD API  
**Repo:** https://github.com/Davionnic/w2-task-crud-api (`main.py`)

---

## What this part does (plain words)

When someone creates a task (`POST /tasks`), the API has to remember it somewhere and give it a unique number (`id`). I did **not** use a database for this homework. I used two Python variables that live only while the server process is running:

1. `tasks` — a **list** of dictionaries. Each dict is one task: `id`, `title`, `done`.
2. `next_id` — an integer that says “the next new task gets this number.”

On startup I call `init_seed_tasks()`, which fills the list with three starter tasks and sets `next_id` to `4`. Creating a task appends a new dict and then bumps `next_id` by one. Deleting rebuilds the list without that id. Updating finds the dict by id and changes fields in place.

That is the whole “database” for this assignment: RAM + a counter.

---

## Why it works that way

- **List of dicts** is easy to filter (`done=true`, title search) with normal Python loops. No SQL to learn for Stage 0–6.
- **`next_id`** avoids reusing ids after deletes. If I used `len(tasks) + 1`, deleting task `2` then creating a new one could collide or confuse clients.
- **No disk write** means a restart (or calling `POST /reset`) brings back only the seed data. That is a feature for demos and a limitation for real apps.

---

## What confused me at first

I kept thinking “where does the data go?” The honest answer: **nowhere permanent**. The list is just a variable in the FastAPI process. Close the terminal running `uvicorn`, and the memory is gone. That is why `/health` can still say `ok` after a restart while your newly created tasks disappeared — the process is healthy; the old list is not there anymore.

Also: `PUT /tasks/{id}` uses a Pydantic model where `title` and `done` are **optional**. That lets you flip only `done` without resending the title. If both were required, every update would force a full rewrite.

---

## How I’d teach a beginner

Imagine a whiteboard (the list) and a sticky note that says “next number” (`next_id`). Every new task: write a new box on the whiteboard, peel the sticky note, write that number on the box, then put a sticky note with number+1. Erase a box to delete. Restart the class = wipe the whiteboard and redraw the three starter boxes.

When you outgrow the whiteboard, you swap it for a real database — same API routes, different storage behind them.

---

## What I own vs what AI helped with

I can point to the list, the counter, seed init, create/update/delete paths, and explain why restart clears data. AI helped scaffold FastAPI/Pydantic patterns; the mental model above is mine after walking the file line by line.
