"""Todo 数据模型与 JSON 持久化（原子写入）。"""
import json
import os
import time
import uuid
from pathlib import Path

DEFAULT_PATH = Path.home() / ".todosimple" / "todos.json"


class TodoStore:
    def __init__(self, path=DEFAULT_PATH):
        self.path = Path(path)
        self.todos = []  # list[dict]，每项 {id, text, done, created_at}
        self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self.todos = [
                    t for t in data if isinstance(t, dict) and "text" in t
                ]
        except FileNotFoundError:
            self.todos = []
        except (json.JSONDecodeError, OSError):
            self.todos = []
        return self.todos

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".json.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.todos, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        except OSError:
            pass  # 保存失败不致命，下次成功时再写

    def add(self, text):
        text = (text or "").strip()
        if not text:
            return None
        todo = {
            "id": uuid.uuid4().hex,
            "text": text,
            "done": False,
            "created_at": time.time(),
        }
        self.todos.append(todo)
        self.save()
        return todo

    def set_done(self, todo_id, done):
        for t in self.todos:
            if t["id"] == todo_id:
                t["done"] = bool(done)
                self.save()
                return

    def remove(self, todo_id):
        self.todos = [t for t in self.todos if t["id"] != todo_id]
        self.save()

    def pending_count(self):
        return sum(1 for t in self.todos if not t["done"])