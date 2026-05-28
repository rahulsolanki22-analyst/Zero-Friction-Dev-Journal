import os
import re
import sqlite3
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI(title="Zero-Friction Dev Journal")

# Ensure the database is created
DB_FILE = "database.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            tags TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Set up templates
templates = Jinja2Templates(directory="templates")

# Mount static files directly from templates folder to serve styles.css
app.mount("/static", StaticFiles(directory="templates"), name="static")

class LogEntry(BaseModel):
    content: str

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM logs ORDER BY timestamp DESC").fetchall()
    conn.close()
    
    # Calculate some stats for the header
    total_entries = len(logs)
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "logs": logs,
        "total_entries": total_entries
    })

@app.post("/api/log")
async def create_log(entry: LogEntry, cli: bool = False):
    content = entry.content
    # Extract tags
    tags = re.findall(r'#\w+', content)
    tags_str = ",".join(tags)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO logs (content, tags, timestamp) VALUES (?, ?, ?)",
        (content, tags_str, timestamp)
    )
    conn.commit()
    conn.close()
    
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM logs WHERE id = ?", (log_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Log deleted"}

@app.get("/api/tags")
async def get_tags():
    conn = get_db_connection()
    logs = conn.execute("SELECT tags FROM logs").fetchall()
    conn.close()
    
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
    conn = get_db_connection()
    query = f"%{q}%"
    logs = conn.execute(
        "SELECT * FROM logs WHERE content LIKE ? OR tags LIKE ? ORDER BY timestamp DESC",
        (query, query)
    ).fetchall()
    conn.close()
    
    return [dict(log) for log in logs]
