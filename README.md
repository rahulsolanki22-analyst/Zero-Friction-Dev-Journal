# ⚡ Zero-Friction Dev Journal

<div align="center">
  <p>A lightning-fast, keyboard-first developer journal and API logger with a premium Tailwind CSS dashboard.</p>
</div>

## ✨ Features

- **Keyboard-First Workflow:** Instantly log thoughts, bugs, and learning milestones directly from your terminal/CMD without switching contexts.
- **Multi-Line Snippets:** Native support for logging multi-line code blocks and error traces using your system's default text editor.
- **Cloud Tags Sidebar:** Automatically extracts `#tags` from your logs and builds a dynamic, clickable sidebar to instantly filter your timeline.
- **Premium Aesthetics:** Beautiful UI built with Tailwind CSS, featuring an engineering-blueprint grid background, dynamic glowing tag colors, and smooth transitions.
- **Light & Dark Mode:** Built-in theme toggle that respects your eyes and seamlessly remembers your preference.
- **100% Local & Private:** Powered by a local SQLite database and FastAPI. No external dependencies, no cloud subscriptions, your data stays entirely yours.

## 🛠️ Architecture

* `main.py`: FastAPI backend handling routes, SQLite connections, and hashtag extraction logic.
* `database.db`: SQLite database (auto-generates safely on your first run, excluded from Git).
* `templates/index.html`: The interactive dashboard UI (Jinja2 + Tailwind CSS + Vanilla JS).
* `templates/styles.css`: Custom scrollbars and grid background patterns.
* `log.cmd` / `log-code.cmd`: Windows CMD integration scripts.

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have Python installed, then install the required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Launch the Server
Start the local server. The database will automatically initialize itself.
```bash
uvicorn main:app --reload
```
The dashboard will be available at: [http://localhost:8000](http://localhost:8000)

## 💻 Terminal Integration Setup

To achieve the "zero-friction" workflow, configure your terminal so you can type `log "message #tag"` directly.

### For Windows (PowerShell)
Add these custom functions to your PowerShell profile. 
1. Open PowerShell and run `notepad $PROFILE`. (If it errors, run `New-Item -Path $PROFILE -Type File -Force` first).
2. Paste the following at the bottom:
```powershell
function log {
    param([string]$message)
    $payload = @{ content = $message } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/log?cli=true" -Method Post -Body $payload -ContentType "application/json"
    Write-Host $response
}

function log-code {
    $tempFile = New-TemporaryFile
    Write-Host "Opening Notepad..."
    Start-Process notepad -ArgumentList $tempFile -Wait
    $content = Get-Content $tempFile -Raw
    if (![string]::IsNullOrWhiteSpace($content)) {
        $payload = @{ content = $content.Trim() } | ConvertTo-Json -Depth 10
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/log?cli=true" -Method Post -Body $payload -ContentType "application/json"
        Write-Host $response
    } else {
        Write-Host "Empty snippet, discarded."
    }
    Remove-Item $tempFile
}
```
3. Save, close Notepad, and restart PowerShell.

### For Windows (Standard CMD)
Batch scripts `log.cmd` and `log-code.cmd` are included in this project.
1. Press the **Windows Key**, type **Environment Variables**, and hit Enter.
2. Click the **Environment Variables...** button.
3. Under "User variables", double-click **Path**, click **New**, and add the absolute path to this project folder.
4. Restart your CMD window.

### For Mac/Linux (Bash/Zsh)
Add this to your `~/.bashrc` or `~/.zshrc`:
```bash
function log() {
    response=$(curl -s -X POST "http://localhost:8000/api/log?cli=true" \
         -H "Content-Type: application/json" \
         -d "{\"content\": \"$1\"}")
    echo $response
}

function log-code() {
    temp_file=$(mktemp)
    ${EDITOR:-nano} "$temp_file"
    content=$(cat "$temp_file")
    if [ -n "$content" ]; then
        payload=$(jq -n --arg content "$content" '{content: $content}')
        response=$(curl -s -X POST "http://localhost:8000/api/log?cli=true" \
             -H "Content-Type: application/json" \
             -d "$payload")
        echo "$response"
    else
        echo "Empty snippet, discarded."
    fi
    rm "$temp_file"
}
```

## 📝 Usage Example
Once configured, log entries from anywhere on your machine:
```bash
# Standard single-line log
log "Fixed the caching issue on the backend #bug #backend"

# Multi-line code block log (Opens your text editor)
log-code
```
Refresh your browser at `localhost:8000` to see your new entries appear instantly!

## 📄 License
This project is open-source and available under the MIT License.
