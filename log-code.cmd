@echo off
set TEMP_FILE="%TEMP%\zero_friction_log_%RANDOM%.txt"
type nul > %TEMP_FILE%
echo Opening Notepad. Type your code, save, and close to submit...
start /wait notepad %TEMP_FILE%

"%~dp0.venv\Scripts\python.exe" -c "import json, urllib.request, os; p = r'%TEMP_FILE%'.replace('\"', ''); f = open(p, 'r', encoding='utf-8'); content = f.read().strip(); f.close(); url = os.environ.get('ZERO_FRICTION_URL', 'http://localhost:8000').rstrip('/') + '/api/log?cli=true'; req = urllib.request.Request(url, data=json.dumps({'content': content}).encode('utf-8'), headers={'Content-Type': 'application/json'}) if content else None; res = urllib.request.urlopen(req) if req else None; print(res.read().decode('utf-8') if res else 'Empty snippet, discarded.')"

del %TEMP_FILE%
