@echo off
set TEMP_FILE="%TEMP%\zero_friction_log_%RANDOM%.txt"
type nul > %TEMP_FILE%
echo Opening Notepad. Type your code, save, and close to submit...
start /wait notepad %TEMP_FILE%

python -c "import json, urllib.request; p = r'%TEMP_FILE%'; p = p.replace('\"', ''); f = open(p, 'r', encoding='utf-8'); content = f.read().strip(); f.close(); req = urllib.request.Request('http://localhost:8000/api/log?cli=true', data=json.dumps({'content': content}).encode('utf-8'), headers={'Content-Type': 'application/json'}) if content else None; res = urllib.request.urlopen(req) if req else None; print(res.read().decode('utf-8') if res else 'Empty snippet, discarded.')"

del %TEMP_FILE%
