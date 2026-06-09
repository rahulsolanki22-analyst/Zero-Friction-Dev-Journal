@echo off
if "%~1"=="" (
    echo Usage: log "your message #tag"
    exit /b 1
)
set "BASE_URL=%ZERO_FRICTION_URL%"
if "%BASE_URL%"=="" set "BASE_URL=http://localhost:8000"
curl -s -X POST "%BASE_URL%/api/log?cli=true" -H "Content-Type: application/json" -d "{\"content\": \"%~1\"}"
echo.

