---
name: microsoft-todo
description: >
  Quản lý task, schedule, reminder sử dụng Microsoft Todo.
  Thêm task, xem danh sách, đánh dấu hoàn thành, set reminder.
  Gửi thông báo qua Telegram.
metadata:
  openclaw:
    requires:
      bins: ["python3"]
---

# Microsoft Todo Task Manager

## Khi nào sử dụng skill này
- Khi người dùng nói "thêm task", "ghi task", "add todo"
- Khi muốn xem danh sách task, deadline, reminder
- Khi cần đánh dấu task hoàn thành
- Khi setup reminder cho task quan trọng

## Cách thực hiện

### Bước 1: Authenticate (Lần đầu)
Script tự động login với personal account (haphuong.phan@live.com).
Lấy access token từ Microsoft Graph API.

### Bước 2: Task Management
Các thao tác chính:

**Thêm task mới:**
```bash
python3 scripts/task_manager.py add "Tiêu đề task" --due-date 2026-03-05 --reminder 1h
```

**Xem danh sách task:**
```bash
python3 scripts/task_manager.py list --list "Inbox"
```

**Đánh dấu hoàn thành:**
```bash
python3 scripts/task_manager.py complete <task-id>
```

**Xóa task:**
```bash
python3 scripts/task_manager.py delete <task-id>
```

### Bước 3: Notification
- Task với reminder sẽ gửi thông báo qua Telegram
- Format: "⏰ Task: [tiêu đề] - due [ngày]"

## Credentials
- Email: haphuong.phan@live.com
- Password: Stored in environment (không hardcode)
- Token: Auto-refresh khi expire

## API Reference
Microsoft Graph API: `/v1.0/me/todo/lists`

Docs: https://learn.microsoft.com/en-us/graph/api/resources/todo-overview
