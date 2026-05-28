@echo off
if "%~1"=="" (
    echo Usage: log "your message #tag"
    exit /b 1
)
curl -s -X POST "http://localhost:8000/api/log?cli=true" -H "Content-Type: application/json" -d "{\"content\": \"%~1\"}"
echo.
