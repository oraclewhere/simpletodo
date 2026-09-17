"""Todo 悬浮工具入口：截图工具式遮罩 + 全局热键 + 右下角悬浮窗 + 托盘。"""
import sys

from autostart import AutoStart
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from config import Config
from hotkey import HotkeyListener, HotkeyNotifier
from storage import TodoStore
from ui import CornerWidget, SettingsDialog, TodoOverlay


APP_STYLE = """
QFrame#card {
    background-color: rgba(249, 250, 252, 242);
    border: 1px solid rgba(255, 255, 255, 190);
    border-radius: 24px;
}
QLabel#title { font-size: 22px; font-weight: 700; color: #1d1d1f; }
QLabel#count { color: #8e8e93; font-size: 13px; font-weight: 500; }
QLabel#hint { color: #8e8e93; font-size: 12px; padding-top: 2px; }
QLabel#empty { color: #8e8e93; font-size: 14px; padding: 28px 0; }
QLabel#sectionLabel {
    color: #8e8e93; font-size: 12px; font-weight: 700;
    padding: 14px 8px 5px; letter-spacing: 0.5px;
}
QLabel#sectionEmpty { color: #a1a1a6; font-size: 13px; padding: 10px 12px 14px; }
QLineEdit {
    border: 1px solid rgba(60, 60, 67, 35); border-radius: 13px;
    padding: 10px 13px; font-size: 14px; background: rgba(255, 255, 255, 210);
    color: #1d1d1f; selection-background-color: #0a84ff;
}
QLineEdit:focus { border: 1px solid #0a84ff; background: #ffffff; }
QPushButton#addBtn {
    background: #0a84ff; color: #ffffff; border: none; border-radius: 13px;
    padding: 10px 18px; font-size: 14px; font-weight: 600;
}
QPushButton#addBtn:hover { background: #0077ed; }
QPushButton#addBtn:pressed { background: #006edb; }
QPushButton#addBtn:disabled { background: #9dcef9; }
QWidget#todoRow {
    background: rgba(255, 255, 255, 185); border: 1px solid rgba(60, 60, 67, 22);
    border-radius: 13px;
}
QWidget#todoRow:hover { background: rgba(255, 255, 255, 235); border-color: rgba(10, 132, 255, 75); }
QWidget#todoRow[completed="true"] { background: rgba(235, 235, 240, 155); border-color: transparent; }
QCheckBox { spacing: 0; padding-left: 3px; }
QCheckBox::indicator {
    width: 18px; height: 18px; border-radius: 9px;
    border: 1.5px solid #b0b0b5; background: rgba(255, 255, 255, 220);
}
QCheckBox::indicator:hover { border-color: #0a84ff; }
QCheckBox::indicator:checked { background: #34c759; border-color: #34c759; }
QPushButton#deleteBtn {
    color: #a1a1a6; border: none; background: transparent; font-size: 19px;
    border-radius: 11px; font-weight: 400;
}
QPushButton#deleteBtn:hover { background: rgba(255, 69, 58, 20); color: #ff453a; }
QScrollArea#scroll { border: none; background: transparent; }
QWidget#listContainer { background: transparent; }
QWidget#corner { background: rgba(28, 28, 30, 235); border: 1px solid rgba(255, 255, 255, 55); border-radius: 18px; }
QLabel#cornerLabel { color: #ffffff; font-size: 13px; padding: 8px 14px; background: transparent; }
QLabel#keyDisplay { background: #f1f1f4; border-radius: 10px; font-size: 18px; color: #1d1d1f; font-weight: 600; }
"""


def _make_icon():
    """绘制一个简单的勾选图标用于系统托盘。"""
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#1a73e8"))
    p.drawRoundedRect(4, 4, 56, 56, 14, 14)
    pen = QPen(QColor("#ffffff"))
    pen.setWidth(6)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawPolyline([QPoint(20, 34), QPoint(29, 43), QPoint(46, 24)])
    p.end()
    return QIcon(pm)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("todosimple")
    app.setQuitOnLastWindowClosed(False)  # 隐藏窗口时保持常驻
    app.setStyleSheet(APP_STYLE)

    config = Config()
    store = TodoStore()
    autostart = AutoStart()

    overlay = TodoOverlay()
    overlay.set_hint(config.hotkey_label)
    corner = CornerWidget()

    notifier = HotkeyNotifier()
    hotkey = HotkeyListener(notifier)

    # ---- 状态刷新 ----
    def refresh_all():
        overlay.set_todos(store.todos)
        corner.update_state(store.pending_count(), config.hotkey_label)

    def update_counts():
        pending = store.pending_count()
        overlay.count_label.setText(
            f"{pending} 待办 · {len(store.todos)} 总计" if store.todos else "0 待办"
        )
        corner.update_state(pending, config.hotkey_label)

    def open_overlay():
        corner.hide()
        overlay.set_todos(store.todos)  # 打开前刷新
        overlay.show_overlay()

    def collapse_overlay():
        overlay.hide()
        corner.show_at_corner()

    def toggle_overlay():
        if overlay.isVisible():
            collapse_overlay()
        else:
            open_overlay()

    # ---- 数据操作回调 ----
    def on_add(text):
        store.add(text)
        refresh_all()

    def on_toggle(todo_id, done):
        store.set_done(todo_id, done)
        update_counts()  # 先更新计数，列表等退出动画结束后再重建

    def on_remove(todo_id):
        store.remove(todo_id)
        refresh_all()

    # ---- 设置快捷键 ----
    def apply_hotkey(hotkey_str, label):
        config.set_hotkey(hotkey_str, label)
        hotkey.set_hotkey(hotkey_str)
        overlay.set_hint(label)
        corner.update_state(store.pending_count(), label)

    def apply_autostart(enabled):
        # Keep the preference in sync only when the Windows startup entry changed.
        if autostart.set_enabled(enabled):
            config.set_autostart(enabled)

    def on_settings():
        dialog = SettingsDialog(
            config.hotkey_label,
            autostart.is_enabled() or config.autostart,
        )
        dialog.hotkey_changed.connect(apply_hotkey)
        dialog.autostart_changed.connect(apply_autostart)
        dialog.exec()

    # ---- 信号连接 ----
    overlay.add_requested.connect(on_add)
    overlay.toggle_requested.connect(on_toggle)
    overlay.rebuild_requested.connect(refresh_all)
    overlay.remove_requested.connect(on_remove)
    overlay.collapsed.connect(collapse_overlay)
    corner.open_requested.connect(open_overlay)
    corner.quit_requested.connect(app.quit)
    corner.settings_requested.connect(on_settings)
    notifier.triggered.connect(toggle_overlay)

    # ---- 系统托盘 ----
    if QSystemTrayIcon.isSystemTrayAvailable():
        tray = QSystemTrayIcon(_make_icon(), app)
        menu = QMenu()
        menu.addAction("打开待办", toggle_overlay)
        menu.addAction("设置快捷键…", on_settings)
        menu.addSeparator()
        menu.addAction("退出", app.quit)
        tray.setContextMenu(menu)
        tray.setToolTip("Todo 悬浮工具")
        tray.activated.connect(
            lambda reason: toggle_overlay()
            if reason == QSystemTrayIcon.Trigger
            else None
        )
        tray.show()

    # ---- 启动 ----
    hotkey.set_hotkey(config.hotkey)  # 内部会启动监听
    refresh_all()
    corner.show_at_corner()  # 常驻右下角

    exit_code = app.exec()

    hotkey.stop()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
