# Microsoft Todo Skill

Quản lý task, deadline, reminder sử dụng Microsoft Todo.

## Setup

### 1. Install dependencies
```bash
pip install requests
```

### 2. Authenticate
```bash
python3 scripts/todo_manager.py list
# Sẽ prompt login lần đầu
```

### 3. Store credentials
Credentials sẽ được lưu tại: `~/.openclaw/credentials/microsoft_todo_token.json`

## Usage

### Add Task
```bash
python3 scripts/todo_manager.py add "Mua groceries" --due-date 2026-03-05 --list "Inbox"
```

### List Tasks
```bash
python3 scripts/todo_manager.py list --list "Inbox"
```

### Complete Task
```bash
python3 scripts/todo_manager.py complete <task-id> --list "Inbox"
```

### Delete Task
```bash
python3 scripts/todo_manager.py delete <task-id> --list "Inbox"
```

## Features
- ✅ Add/Delete/Complete tasks
- ✅ Multiple lists support
- ✅ Due dates
- ✅ Reminders (send to Telegram)
- ✅ Auto-refresh tokens

## Account
- Email: haphuong.phan@live.com
- Type: Personal Microsoft Account
