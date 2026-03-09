#!/usr/bin/env python3
"""
Microsoft Todo Manager with MSAL Authentication
- Authenticate with personal account
- Add, list, complete, delete tasks
"""

import sys
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import os
from urllib.parse import urlencode
import webbrowser

# Config
EMAIL = "haphuong.phan@live.com"
PASSWORD = os.environ.get("MICROSOFT_TODO_PASSWORD", "")
TOKEN_FILE = Path.home() / ".openclaw" / "credentials" / "microsoft_todo_token.json"
CONFIG_FILE = Path.home() / ".openclaw" / "credentials" / "microsoft_todo_config.json"

# Microsoft Graph API endpoints
GRAPH_API = "https://graph.microsoft.com/v1.0"
TENANT_ID = "common"
AUTH_ENDPOINT = f"https://login.microsoft.com/{TENANT_ID}/oauth2/v2.0/authorize"
TOKEN_ENDPOINT = f"https://login.microsoft.com/{TENANT_ID}/oauth2/v2.0/token"

# Azure App (Public client) - Using Microsoft's built-in clientId for CLI auth
CLIENT_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"  # Azure CLI public client
REDIRECT_URI = "http://localhost:8080"
SCOPE = ["https://graph.microsoft.com/.default", "offline_access"]


class TodoManager:
    def __init__(self):
        self.access_token = None
        self.headers = {}
        self.ensure_authenticated()
    
    def ensure_authenticated(self):
        """Load token or authenticate"""
        if TOKEN_FILE.exists():
            try:
                with open(TOKEN_FILE) as f:
                    data = json.load(f)
                    self.access_token = data.get("access_token")
                    if self.access_token:
                        self.headers = {"Authorization": f"Bearer {self.access_token}"}
                        print("✓ Token loaded from cache")
                        return
            except:
                pass
        
        # Authenticate with device flow (no browser needed)
        self.authenticate_device_flow()
    
    def authenticate_device_flow(self):
        """Device flow authentication"""
        print("\n🔐 Authenticating with Microsoft...")
        
        try:
            # Step 1: Get device code
            device_code_url = f"{TOKEN_ENDPOINT.replace('token', 'devicecode')}"
            device_payload = {
                "client_id": CLIENT_ID,
                "scope": " ".join(SCOPE)
            }
            
            response = requests.post(device_code_url, data=device_payload)
            
            if response.status_code != 200:
                print(f"❌ Error getting device code: {response.text}")
                raise Exception("Authentication failed")
            
            device_data = response.json()
            device_code = device_data.get("device_code")
            user_code = device_data.get("user_code")
            
            print(f"\n📱 Go to: {device_data.get('verification_uri')}")
            print(f"📝 Enter code: {user_code}")
            print("⏳ Waiting for authentication...\n")
            
            # Step 2: Poll for token
            for attempt in range(120):  # 2 minute timeout
                token_payload = {
                    "client_id": CLIENT_ID,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                }
                
                response = requests.post(TOKEN_ENDPOINT, data=token_payload)
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.access_token = token_data.get("access_token")
                    self.headers = {"Authorization": f"Bearer {self.access_token}"}
                    
                    # Save token
                    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
                    with open(TOKEN_FILE, 'w') as f:
                        json.dump(token_data, f)
                    
                    print("✅ Authentication successful!\n")
                    return
                
                elif response.status_code == 400:
                    error = response.json().get("error")
                    if error == "authorization_pending":
                        pass  # Still waiting
                    else:
                        print(f"❌ Error: {error}")
                        raise Exception(f"Auth error: {error}")
                
                # Wait before retry
                import time
                time.sleep(1)
            
            print("❌ Authentication timeout")
            raise Exception("Timeout waiting for authentication")
            
        except Exception as e:
            print(f"❌ Authentication failed: {str(e)}")
            raise
    
    def get_tasks(self, list_name="Inbox"):
        """Fetch tasks from a list"""
        try:
            # Get all lists
            response = requests.get(
                f"{GRAPH_API}/me/todo/lists",
                headers=self.headers
            )
            
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return None
            
            lists = response.json().get("value", [])
            target_list = next((l for l in lists if l["displayName"] == list_name), None)
            
            if not target_list:
                print(f"❌ List '{list_name}' not found")
                return None
            
            # Get tasks in this list
            list_id = target_list["id"]
            response = requests.get(
                f"{GRAPH_API}/me/todo/lists/{list_id}/tasks",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json().get("value", [])
            else:
                print(f"❌ Error fetching tasks: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return None
    
    def add_task(self, title, due_date=None, list_name="Inbox"):
        """Add new task"""
        try:
            # Get list ID
            response = requests.get(
                f"{GRAPH_API}/me/todo/lists",
                headers=self.headers
            )
            
            lists = response.json().get("value", [])
            target_list = next((l for l in lists if l["displayName"] == list_name), None)
            
            if not target_list:
                print(f"❌ List '{list_name}' not found")
                return False
            
            list_id = target_list["id"]
            
            # Create task
            task_data = {"title": title}
            
            if due_date:
                task_data["dueDateTime"] = {
                    "dateTime": due_date,
                    "timeZone": "Asia/Saigon"
                }
            
            response = requests.post(
                f"{GRAPH_API}/me/todo/lists/{list_id}/tasks",
                headers=self.headers,
                json=task_data
            )
            
            if response.status_code == 201:
                task = response.json()
                print(f"✓ Task created: {task['id']}")
                return task
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return False
    
    def complete_task(self, task_id, list_name="Inbox"):
        """Mark task as completed"""
        try:
            # Get list ID
            response = requests.get(
                f"{GRAPH_API}/me/todo/lists",
                headers=self.headers
            )
            
            lists = response.json().get("value", [])
            target_list = next((l for l in lists if l["displayName"] == list_name), None)
            
            if not target_list:
                return False
            
            list_id = target_list["id"]
            
            # Update task status
            response = requests.patch(
                f"{GRAPH_API}/me/todo/lists/{list_id}/tasks/{task_id}",
                headers=self.headers,
                json={"status": "completed"}
            )
            
            if response.status_code == 200:
                print(f"✓ Task marked as completed")
                return True
            else:
                print(f"❌ Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return False
    
    def delete_task(self, task_id, list_name="Inbox"):
        """Delete a task"""
        try:
            response = requests.get(
                f"{GRAPH_API}/me/todo/lists",
                headers=self.headers
            )
            
            lists = response.json().get("value", [])
            target_list = next((l for l in lists if l["displayName"] == list_name), None)
            
            if not target_list:
                return False
            
            list_id = target_list["id"]
            
            response = requests.delete(
                f"{GRAPH_API}/me/todo/lists/{list_id}/tasks/{task_id}",
                headers=self.headers
            )
            
            if response.status_code == 204:
                print(f"✓ Task deleted")
                return True
            else:
                print(f"❌ Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Microsoft Todo Manager")
    subparsers = parser.add_subparsers(dest="command")
    
    # Add task
    add_parser = subparsers.add_parser("add", help="Add new task")
    add_parser.add_argument("title", help="Task title")
    add_parser.add_argument("--due-date", help="Due date (YYYY-MM-DD)")
    add_parser.add_argument("--list", default="Inbox", help="List name")
    
    # List tasks
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("--list", default="Inbox", help="List name")
    
    # Complete task
    complete_parser = subparsers.add_parser("complete", help="Mark task as completed")
    complete_parser.add_argument("task_id", help="Task ID")
    complete_parser.add_argument("--list", default="Inbox", help="List name")
    
    # Delete task
    delete_parser = subparsers.add_parser("delete", help="Delete task")
    delete_parser.add_argument("task_id", help="Task ID")
    delete_parser.add_argument("--list", default="Inbox", help="List name")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = TodoManager()
    
    if args.command == "add":
        manager.add_task(
            args.title,
            due_date=args.due_date,
            list_name=args.list
        )
    
    elif args.command == "list":
        tasks = manager.get_tasks(args.list)
        if tasks:
            print(f"\n📋 Tasks in '{args.list}':")
            for task in tasks:
                status = "✓" if task.get("status") == "completed" else "○"
                due = ""
                if task.get("dueDateTime"):
                    due = f" - Due: {task['dueDateTime']['dateTime'][:10]}"
                print(f"  {status} {task['title']}{due}")
            
            # Summary
            total = len(tasks)
            completed = len([t for t in tasks if t.get("status") == "completed"])
            pending = total - completed
            print(f"\n📊 Summary: {pending} pending, {completed} completed (Total: {total})")
        else:
            print("❌ No tasks found")
    
    elif args.command == "complete":
        manager.complete_task(args.task_id, args.list)
    
    elif args.command == "delete":
        manager.delete_task(args.task_id, args.list)


if __name__ == "__main__":
    main()
