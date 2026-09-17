"""全局热键监听。

在后台线程用 pynput 监听当前配置的组合键，命中后通过 Qt 信号
（跨线程队列连接）通知主线程。
"""
import sys

from PySide6.QtCore import QObject, Signal

try:
    from pynput import keyboard
    _HAS_PYNPUT = True
except Exception:  # pragma: no cover - 环境缺少 pynput 时优雅降级
    keyboard = None
    _HAS_PYNPUT = False


class HotkeyNotifier(QObject):
    """跨线程信号载体，主线程连接到 triggered 以切换遮罩。"""
    triggered = Signal()


# 不同平台上 pynput 给出的修饰键名可能带 l/r 后缀，统一归一化。
_MODIFIER_ALIASES = {
    "ctrl_l": "ctrl", "ctrl_r": "ctrl",
    "alt_l": "alt", "alt_r": "alt", "alt_gr": "alt",
    "shift_l": "shift", "shift_r": "shift",
    "cmd_l": "cmd", "cmd_r": "cmd",
    "win_l": "cmd", "win_r": "cmd",
    "super_l": "cmd", "super_r": "cmd",
}


def _normalize(name):
    return _MODIFIER_ALIASES.get(name, name)


def _pynput_key_name(key):
    """把 pynput 的 Key/KeyCode 转为规范字符串（如 'f2'、'ctrl'、'space'）。"""
    if keyboard is None:
        return None
    if isinstance(key, keyboard.Key):
        return _normalize(key.name)
    # KeyCode（普通字符键）
    if getattr(key, "char", None):
        return str(key.char).lower()
    return None


class HotkeyListener:
    def __init__(self, notifier=None):
        self.notifier = notifier or HotkeyNotifier()
        self._listener = None
        self._allowed = set()  # 期望同时按下的键名集合
        self._pressed = set()

    def set_hotkey(self, hotkey: str):
        """hotkey 形如 'f2' 或 'ctrl+alt+space'，小写、+ 分隔。"""
        parts = [_normalize(p.strip().lower()) for p in hotkey.split("+") if p.strip()]
        self._allowed = set(parts)
        self._pressed = set()
        self.restart()

    def _on_press(self, key):
        name = _pynput_key_name(key)
        if not name:
            return
        self._pressed.add(name)
        if self._allowed and self._allowed <= self._pressed:
            self.notifier.triggered.emit()
            self._pressed = set()  # 触发后清空，避免长按连发

    def _on_release(self, key):
        name = _pynput_key_name(key)
        if name and name in self._pressed:
            self._pressed.discard(name)

    def start(self):
        if not _HAS_PYNPUT:
            print("[hotkey] 未安装 pynput，全局热键不可用", file=sys.stderr)
            return False
        try:
            self._listener = keyboard.Listener(
                on_press=self._on_press, on_release=self._on_release
            )
            self._listener.daemon = True
            self._listener.start()
            return True
        except Exception as e:  # 例如无可用 X display
            print(f"[hotkey] 无法启动全局热键监听: {e}", file=sys.stderr)
            self._listener = None
            return False

    def stop(self):
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def restart(self):
        self.stop()
        self.start()