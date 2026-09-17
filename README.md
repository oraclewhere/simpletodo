# Todo 悬浮工具（todosimple）

一个极简的桌面 Todo
在你需要的时候，按全局快捷键在全屏灰黑遮罩中呼出 Todo，进行查看或修改
完成后按ESC 收起为右下角悬浮窗

## 功能

- **快捷键呼出**：默认 `F2`，全屏蒙上一层半透明灰黑底，中间显示待办卡片。
- **分区**：「待办」和「已完成」两个栏目，勾选后条目带着退出动画移入「已完成」，取消勾选则回到「待办」。
- **增删改**：输入框回车或点击「添加」新增；点 `×` 删除。
- **ESC 收起**：不退出程序，而是缩到**右下角悬浮窗**；点它即可重新呼出。
- **自定义快捷键**：右下角悬浮窗右键菜单 →「设置快捷键…」，按下新组合键即可修改。
- **系统托盘**：支持托盘菜单「打开 / 设置快捷键 / 退出」。
- **持久化**：数据保存在 `~/.todosimple/todos.json`，配置在 `~/.todosimple/config.json`。

## 安装与运行

需要 Python 3.8+（建议 3.10+）。

```bash
# 1. 创建虚拟环境
python3 -m venv .venv

# 2. 安装依赖
.venv/bin/pip install -r requirements.txt
# Windows 下为： .venv\Scripts\pip install -r requirements.txt

# 3. 运行
.venv/bin/python main.py
# Windows 下为： .venv\Scripts\python main.py
```

## 使用

| 操作 | 效果 |
| --- | --- |
| `F2`（可自定义） | 呼出 / 收起 Todo 遮罩 |
| `ESC` | 收起为右下角悬浮窗 |
| 点击右下角悬浮窗 | 重新呼出遮罩 |
| 拖动悬浮窗 | 移动位置（拖拽超过约 5px 即视为拖动） |
| 悬浮窗右键 | 打开 / 设置快捷键 / 退出 |

新增待办：输入框输入文字后按回车或点「添加」。

## 自定义快捷键

1. 右键右下角悬浮窗（或托盘图标）→「设置快捷键…」。
2. 在弹出的窗口中按下新组合键（如 `Ctrl+Alt+Space`）。
3. 点击「保存」。

也可直接编辑 `~/.todosimple/config.json` 中的 `hotkey` 字段（小写、`+` 分隔，例如 `"ctrl+alt+space"`），保存后重启程序生效。

## WSL2 注意事项

在 WSL2（WSLg）下运行时，全局热键依赖 X 事件，**只有在 WSLg 窗口处于前台时**才能捕获按键；当焦点在某个 Windows 原生程序上时，热键不会被触发。此时右下角悬浮窗始终可点击，作为兜底入口。

在原生 Windows / Linux 桌面环境下，全局热键完全可用。

## 打包成 Windows exe

必须在 **Windows 上**构建（PyInstaller 不支持交叉编译），在项目根目录执行：

```bat
python build.py
```

产物为单文件 `dist/TodoSimple.exe`（约 43.5 MB，双击即用，目标机器无需 Python）。
完整的打包说明、体积构成与故障排查见 **[PACKAGING.md](PACKAGING.md)**。

## 项目结构

```
main.py          # 入口：装配各模块、托盘、信号连接
ui.py            # TodoOverlay / CornerWidget / SettingsDialog
storage.py       # TodoStore：数据模型 + JSON 原子持久化
config.py        # Config：配置加载保存
hotkey.py        # pynput 后台线程全局热键 → Qt 信号
autostart.py     # Windows 开机自启（注册表）
build.py         # 一键打包
todosimple.spec  # PyInstaller 配置
```