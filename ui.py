"""界面组件：TodoOverlay（全屏遮罩）、CornerWidget（右下角悬浮窗）、SettingsDialog（快捷键设置）。"""
from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QKeySequence, QShortcut, QCursor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class TodoRow(QWidget):
    """单条待办：复选框 + 文本 + 删除按钮。"""
    toggled = Signal(str, bool)  # todo_id, done
    removed = Signal(str)        # todo_id

    def __init__(self, todo, parent=None):
        super().__init__(parent)
        self.todo_id = todo["id"]
        self.setObjectName("todoRow")
        self.setProperty("completed", bool(todo.get("done")))
        self._anim = None
        self._on_finished = None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        self.check = QCheckBox()
        self.check.blockSignals(True)  # 初始化 setChecked 不触发信号
        self.check.setChecked(bool(todo.get("done")))
        self.check.blockSignals(False)
        self.check.setCursor(Qt.PointingHandCursor)
        self.check.stateChanged.connect(self._on_toggle)

        self.label = QLabel(todo.get("text", ""))
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._apply_done(bool(todo.get("done")))

        self.delete_btn = QPushButton("×")
        self.delete_btn.setObjectName("deleteBtn")
        self.delete_btn.setFixedSize(22, 22)
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setToolTip("删除")
        self.delete_btn.clicked.connect(lambda: self.removed.emit(self.todo_id))

        layout.addWidget(self.check)
        layout.addWidget(self.label, 1)
        layout.addWidget(self.delete_btn)

    def _on_toggle(self, state):
        # stateChanged emits an int in PySide6, while Qt.Checked is an enum.
        # Comparing them directly always evaluates to False on Qt 6.
        done = state == Qt.CheckState.Checked.value
        self._apply_done(done)
        self.toggled.emit(self.todo_id, done)

    def _apply_done(self, done):
        font = self.label.font()
        font.setStrikeOut(done)
        self.label.setFont(font)
        self.label.setStyleSheet(
            f"color: {'#9aa0a6' if done else '#202124'};"
        )

    def animate_out(self, on_finished=None):
        """退出动画：淡出 + 高度塌缩，结束后回调 on_finished。"""
        self._on_finished = on_finished

        opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(opacity)
        fade = QPropertyAnimation(opacity, b"opacity", self)
        fade.setDuration(200)
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)
        fade.setEasingCurve(QEasingCurve.InCubic)

        collapse = QPropertyAnimation(self, b"maximumHeight", self)
        collapse.setDuration(200)
        collapse.setStartValue(max(self.height(), 1))
        collapse.setEndValue(0)
        collapse.setEasingCurve(QEasingCurve.InCubic)

        self._anim = QParallelAnimationGroup(self)
        self._anim.addAnimation(fade)
        self._anim.addAnimation(collapse)
        self._anim.finished.connect(self._on_anim_finished)
        self._anim.start()

    def _on_anim_finished(self):
        callback = self._on_finished
        self._on_finished = None
        self._anim = None
        if callback is not None:
            callback()


class TodoOverlay(QWidget):
    """全屏灰黑遮罩，居中显示待办卡片。"""
    add_requested = Signal(str)         # 新增文本
    toggle_requested = Signal(str, bool)  # todo_id, done
    remove_requested = Signal(str)      # todo_id
    collapsed = Signal()                # ESC 收起
    rebuild_requested = Signal()        # 条目动画退出后请求重建列表

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._rows = {}  # todo_id -> TodoRow，用于定位待动画的条目

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(1)

        self.card = QFrame()
        self.card.setObjectName("card")
        self.card.setFixedSize(500, 600)
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(42)
        shadow.setOffset(0, 16)
        shadow.setColor(QColor(0, 0, 0, 110))
        self.card.setGraphicsEffect(shadow)

        inner = QVBoxLayout(self.card)
        inner.setContentsMargins(20, 16, 20, 16)
        inner.setSpacing(10)

        # 标题行
        title_row = QHBoxLayout()
        title = QLabel("待办事项")
        title.setObjectName("title")
        self.count_label = QLabel()
        self.count_label.setObjectName("count")
        title_row.addWidget(title)
        title_row.addStretch(1)
        title_row.addWidget(self.count_label)
        inner.addLayout(title_row)

        # 输入行
        input_row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("输入新待办，回车添加…")
        self.input.returnPressed.connect(self._submit)
        self.add_btn = QPushButton("添加")
        self.add_btn.setObjectName("addBtn")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(self._submit)
        input_row.addWidget(self.input, 1)
        input_row.addWidget(self.add_btn)
        inner.addLayout(input_row)

        # 滚动列表
        self.scroll = QScrollArea()
        self.scroll.setObjectName("scroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.list_container = QWidget()
        self.list_container.setObjectName("listContainer")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(4)
        self.list_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.list_container)
        inner.addWidget(self.scroll, 1)

        # 底部提示
        self.hint = QLabel("ESC 收起 · F2 呼出 · 回车添加")
        self.hint.setObjectName("hint")
        self.hint.setAlignment(Qt.AlignCenter)
        inner.addWidget(self.hint)

        outer.addWidget(self.card, 0, Qt.AlignHCenter)
        outer.addStretch(1)

        # ESC 收起
        self._esc = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self._esc.activated.connect(self._collapse)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 140))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._collapse()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _collapse(self):
        self.hide()
        self.collapsed.emit()

    def _submit(self):
        text = self.input.text().strip()
        if text:
            self.add_requested.emit(text)
            self.input.clear()

    def show_overlay(self):
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        if screen is not None:
            self.setGeometry(screen.geometry())
        self.show()
        self.activateWindow()
        self.raise_()
        self.input.setFocus()

    def set_hint(self, hotkey_label):
        self.hint.setText(f"ESC 收起 · {hotkey_label} 呼出 · 回车添加")

    def set_todos(self, todos):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._rows.clear()

        pending_todos = [todo for todo in todos if not todo.get("done")]
        completed_todos = [todo for todo in todos if todo.get("done")]

        if not todos:
            empty = QLabel("还没有待办，先添加一件吧")
            empty.setObjectName("empty")
            empty.setAlignment(Qt.AlignCenter)
            self.list_layout.addWidget(empty)
        else:
            self._add_section("待办", pending_todos, "目前没有待办，享受片刻空闲吧")
            self._add_section("已完成", completed_todos, "还没有完成的事项")

        pending = len(pending_todos)
        total = len(todos)
        self.count_label.setText(
            f"{pending} 待办 · {total} 总计" if total else "0 待办"
        )

    def _add_section(self, title, todos, empty_text=None):
        header = QLabel(title)
        header.setObjectName("sectionLabel")
        self.list_layout.addWidget(header)

        if not todos and empty_text:
            empty = QLabel(empty_text)
            empty.setObjectName("sectionEmpty")
            self.list_layout.addWidget(empty)
            return

        for todo in todos:
            row = TodoRow(todo)
            row.toggled.connect(self._on_row_toggled)
            row.removed.connect(self.remove_requested.emit)
            self._rows[todo["id"]] = row
            self.list_layout.addWidget(row)

    def _on_row_toggled(self, todo_id, done):
        # 立即同步数据；退出动画结束后再重建列表，把条目移动到对应栏目。
        self.toggle_requested.emit(todo_id, done)
        row = self._rows.get(todo_id)
        if row is not None:
            row.check.setEnabled(False)  # 动画期间禁止再次点击
            row.animate_out(self.rebuild_requested.emit)
        else:
            self.rebuild_requested.emit()


class CornerWidget(QWidget):
    """右下角悬浮药丸，点击打开遮罩，可拖拽，右键菜单。"""
    open_requested = Signal()
    settings_requested = Signal()
    quit_requested = Signal()

    DRAG_THRESHOLD = 5

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setObjectName("corner")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel("📋")
        self.label.setObjectName("cornerLabel")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.label.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.label)

        self._press_pos = None
        self._origin = None
        self._moved = False

    def update_state(self, pending_count, hotkey_label):
        self.label.setText(
            f"📋 {pending_count} 待办" if pending_count else "📋"
        )
        self.label.setToolTip(f"点击打开待办（{hotkey_label} 呼出）")
        self.adjustSize()

    def show_at_corner(self):
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        margin = 16
        self.adjustSize()
        self.move(
            geo.right() - self.width() - margin,
            geo.bottom() - self.height() - margin,
        )
        self.show()
        self.raise_()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_pos = event.globalPosition().toPoint()
            self._origin = self.pos()
            self._moved = False
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._press_pos is not None and event.buttons() & Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._press_pos
            if delta.manhattanLength() > self.DRAG_THRESHOLD:
                self._moved = True
            if self._moved:
                self.move(self._origin + delta)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._press_pos is not None and not self._moved:
                self.open_requested.emit()  # 视为点击
            self._press_pos = None
            self._origin = None
            self._moved = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction("打开待办", self.open_requested.emit)
        menu.addAction("设置快捷键…", self.settings_requested.emit)
        menu.addSeparator()
        menu.addAction("退出", self.quit_requested.emit)
        menu.exec(event.globalPos())


_QT_TO_PYNPUT = {
    Qt.Key_Space: "space",
    Qt.Key_Tab: "tab",
    Qt.Key_Return: "enter",
    Qt.Key_Enter: "enter",
    Qt.Key_Escape: "esc",
    Qt.Key_Backspace: "backspace",
    Qt.Key_Delete: "delete",
    Qt.Key_Insert: "insert",
    Qt.Key_Home: "home",
    Qt.Key_End: "end",
    Qt.Key_PageUp: "page_up",
    Qt.Key_PageDown: "page_down",
    Qt.Key_Left: "left",
    Qt.Key_Right: "right",
    Qt.Key_Up: "up",
    Qt.Key_Down: "down",
}

_PRETTY = {
    "ctrl": "Ctrl", "alt": "Alt", "shift": "Shift", "cmd": "Super",
    "space": "Space", "tab": "Tab", "enter": "Enter", "esc": "Esc",
    "backspace": "Backspace", "delete": "Delete", "insert": "Insert",
    "home": "Home", "end": "End", "page_up": "PageUp", "page_down": "PageDown",
    "left": "Left", "right": "Right", "up": "Up", "down": "Down",
}


def _qt_key_to_name(key):
    """把 Qt 键值映射为 pynput 规范键名（与 hotkey.py 保持一致）。"""
    if Qt.Key_A <= key <= Qt.Key_Z:
        return chr(ord("a") + (key - Qt.Key_A))
    if Qt.Key_0 <= key <= Qt.Key_9:
        return chr(ord("0") + (key - Qt.Key_0))
    if Qt.Key_F1 <= key <= Qt.Key_F35:
        return f"f{key - Qt.Key_F1 + 1}"
    return _QT_TO_PYNPUT.get(key)


def _pretty_name(part):
    if part in _PRETTY:
        return _PRETTY[part]
    if len(part) == 1:
        return part.upper()
    if part.startswith("f") and part[1:].isdigit():
        return part.upper()
    return part


class SettingsDialog(QDialog):
    """按下新快捷键即捕捉，保存后回传。"""
    hotkey_changed = Signal(str, str)  # hotkey 规范字符串, 显示 label

    autostart_changed = Signal(bool)

    def __init__(self, current_label, autostart_enabled=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置全局快捷键")
        self.setModal(True)
        self.setFixedWidth(360)

        self._captured_key = None
        self._captured_label = None

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.autostart_check = QCheckBox("开机时自动启动 TodoSimple")
        self.autostart_check.setChecked(autostart_enabled)

        hint = QLabel("请按下新的全局快捷键组合（例如 Ctrl+Alt+Space），然后点击保存。")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.disp = QLabel(current_label)
        self.disp.setObjectName("keyDisplay")
        self.disp.setAlignment(Qt.AlignCenter)
        self.disp.setMinimumHeight(56)
        layout.addWidget(self.disp)
        layout.addWidget(self.autostart_check)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.save_btn = QPushButton("保存")
        self.save_btn.setObjectName("addBtn")
        self.save_btn.setEnabled(False)
        self.autostart_check.toggled.connect(
            lambda _checked: self.save_btn.setEnabled(True)
        )
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addLayout(buttons)

        self.save_btn.clicked.connect(self._save)
        self.setFocusPolicy(Qt.StrongFocus)

    def _save(self):
        if self._captured_key:
            self.hotkey_changed.emit(self._captured_key, self._captured_label)
        self.autostart_changed.emit(self.autostart_check.isChecked())
        self.accept()

    def keyPressEvent(self, event):
        # 忽略纯修饰键的单独按下，等待真正的功能键
        if event.key() in (
            Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta, Qt.Key_AltGr,
        ):
            event.accept()
            return

        parts = []
        mods = event.modifiers()
        if mods & Qt.ControlModifier:
            parts.append("ctrl")
        if mods & Qt.AltModifier:
            parts.append("alt")
        if mods & Qt.ShiftModifier:
            parts.append("shift")
        if mods & Qt.MetaModifier:
            parts.append("cmd")

        name = _qt_key_to_name(event.key())
        if name is None:
            event.accept()
            return

        # 若只有单个修饰键（不太可能到这里），忽略
        parts.append(name)

        self._captured_key = "+".join(parts)
        self._captured_label = "+".join(_pretty_name(p) for p in parts)
        self.disp.setText(self._captured_label)
        self.save_btn.setEnabled(True)
        event.accept()
