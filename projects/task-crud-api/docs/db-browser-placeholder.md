# DB Browser Screenshot Placeholder

## What Screenshot to Take

Take a screenshot of DB Browser for SQLite showing:

1. **Window**: Full DB Browser for SQLite application window
2. **Database**: tasks.db opened 
3. **Tab**: "Browse Data" tab selected
4. **Table**: "tasks" table selected in dropdown
5. **Content**: Table showing all columns (id, title, done) with sample data
6. **Structure**: Should show the schema with INTEGER, TEXT, BOOLEAN types

## Steps to Capture

1. Install DB Browser for SQLite (https://sqlitebrowser.org/)
2. Open the tasks.db file from the project root
3. Click "Browse Data" tab
4. Select "tasks" table from dropdown
5. Resize window to show table clearly
6. Take screenshot showing full interface with data

## Interim Evidence - Text Dump of SELECT * FROM tasks

Until screenshot is captured, here is the current table content:

```
id|title|done
1|Learn FastAPI|0
2|Build CRUD API|0
3|Manual DB change|1
4|Another manual task|0
```

## Table Schema

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL DEFAULT 0
);
```

This shows that:
- Tasks persist across server restarts
- Manual database modifications appear immediately via API
- SQLite handles INTEGER PRIMARY KEY auto-increment
- BOOLEAN values stored as 0/1 integers as per SQLite standard