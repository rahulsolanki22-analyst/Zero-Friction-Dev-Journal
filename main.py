import os
import re
import sqlite3
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import libsql_client

app = FastAPI(title="Zero-Friction Dev Journal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration: supports both local SQLite and remote Turso (libsql)
DATABASE_URL = os.environ.get("DATABASE_URL", os.environ.get("DATABASE_PATH", "database.db"))
AUTH_TOKEN = os.environ.get("DATABASE_AUTH_TOKEN", "")

# Determine if we should use Turso (libsql) or local sqlite3
USE_TURSO = any(DATABASE_URL.startswith(prefix) for prefix in ["libsql://", "http://", "https://", "wss://"])

class TursoRowAdapter:
    def __init__(self, row, columns):
        self._row = row
        self._columns = columns
        self._dict = dict(zip(columns, row))

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._row[key]
        return self._dict[key]

    def __getattr__(self, name):
        if name in self._dict:
            return self._dict[name]
        raise AttributeError(f"'TursoRowAdapter' object has no attribute '{name}'")

    def keys(self):
        return self._columns

    def __iter__(self):
        return iter(self._dict.items())

def execute_query(query: str, params: tuple = ()):
    if USE_TURSO:
        with libsql_client.create_client_sync(DATABASE_URL, auth_token=AUTH_TOKEN) as client:
            res = client.execute(query, params)
            columns = res.columns
            return [TursoRowAdapter(row, columns) for row in res.rows]
    else:
        conn = sqlite3.connect(DATABASE_URL)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.commit()
            return rows
        finally:
            conn.close()

def init_db():
    if not USE_TURSO:
        db_dir = os.path.dirname(DATABASE_URL)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
    execute_query("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            tags TEXT,
            timestamp TEXT
        )
    """)

init_db()

# Set up templates
templates = Jinja2Templates(directory="templates")

# Mount static files directly from templates folder to serve styles.css
app.mount("/static", StaticFiles(directory="templates"), name="static")

class LogEntry(BaseModel):
    content: str

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    logs = execute_query("SELECT * FROM logs ORDER BY timestamp DESC")
    total_entries = len(logs)
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "logs": logs,
            "total_entries": total_entries
        }
    )

@app.post("/api/log")
async def create_log(entry: LogEntry, cli: bool = False):
    content = entry.content
    # Extract tags
    tags = re.findall(r'#\w+', content)
    tags_str = ",".join(tags)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    execute_query(
        "INSERT INTO logs (content, tags, timestamp) VALUES (?, ?, ?)",
        (content, tags_str, timestamp)
    )
    
    # Format response message
    tag_list = [t.replace("#", "") for t in tags]
    if tag_list:
        msg = f"✔ Log saved. Extracted tags: [{', '.join(tag_list)}]"
    else:
        msg = "✔ Log saved."
        
    if cli:
        return PlainTextResponse(msg)
        
    return {"status": "success", "message": msg}

@app.delete("/api/log/{log_id}")
async def delete_log(log_id: int):
    execute_query("DELETE FROM logs WHERE id = ?", (log_id,))
    return {"status": "success", "message": "Log deleted"}

@app.get("/api/tags")
async def get_tags():
    logs = execute_query("SELECT tags FROM logs")
    
    tag_counts = {}
    for log in logs:
        if log["tags"]:
            tags = log["tags"].split(",")
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    return [{"tag": tag, "count": count} for tag, count in sorted_tags]

@app.get("/api/search")
async def search_logs(q: str):
    query = f"%{q}%"
    logs = execute_query(
        "SELECT * FROM logs WHERE content LIKE ? OR tags LIKE ? ORDER BY timestamp DESC",
        (query, query)
    )
    
    return [dict(log) for log in logs]
