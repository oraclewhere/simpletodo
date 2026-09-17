"""配置加载与保存。

配置存放于 ~/.todosimple/config.json，默认全局快捷键为 F2。
"""
import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "autostart": False,
    "hotkey": "f2",        # pynput 规范字符串，如 "f2"、"ctrl+alt+space"
    "hotkey_label": "F2",  # 展示用文本
}


def _config_path() -> Path:
    return Path.home() / ".todosimple" / "config.json"


class Config:
    def __init__(self):
        self.path = _config_path()
        self.data = dict(DEFAULT_CONFIG)
        self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                self.data.update(loaded)
        except FileNotFoundError:
            pass  # 首次运行，使用默认值
        except (json.JSONDecodeError, OSError):
            pass  # 配置损坏时回退默认值

    @property
    def hotkey(self) -> str:
        return self.data.get("hotkey", DEFAULT_CONFIG["hotkey"])

    @property
    def hotkey_label(self) -> str:
        return self.data.get("hotkey_label", DEFAULT_CONFIG["hotkey_label"])

    @property
    def autostart(self) -> bool:
        return bool(self.data.get("autostart", DEFAULT_CONFIG["autostart"]))

    def set_hotkey(self, hotkey: str, label: str):
        self.data["hotkey"] = hotkey
        self.data["hotkey_label"] = label
        self.save()

    def set_autostart(self, enabled: bool):
        self.data["autostart"] = bool(enabled)
        self.save()

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".json.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        except OSError:
            pass  # 保存失败不致命
