# 打包指南

把 TodoSimple 打包成 Windows 可执行文件。

## 环境要求

- **必须在 Windows 上构建。** PyInstaller 不支持交叉编译 —— 在 Linux / WSL 里执行只会得到 Linux 程序，不是 `.exe`。
- Python 3.8+（建议 3.10+），依赖见 `requirements.txt`：`PySide6`、`pynput`。
- 打包额外需要 `PyInstaller`；`build.py` 会在缺失时自动安装。

> 在 WSL 里开发、又想产出 Windows exe 时，可以借助 WSL 互操作直接调用 Windows 侧的
> Python 来构建（把源码拷到一个 Windows 可访问的目录，用 Windows 的 `python.exe` 跑
> `build.py`）。WSL 自带的 Linux Python 装不出 `.exe`。

## 打包命令

在 Windows 上、项目根目录执行：

```bat
python build.py
```

它会依次：检查依赖（缺失则自动 pip 安装）→ 清理旧的 `build/` 与 `dist/` →
调用 PyInstaller → 生成启动脚本与说明文件。

等价的手动命令：

```bat
python -m PyInstaller todosimple.spec -y
```

完全不使用 spec 时也可以一行搞定：

```bat
pyinstaller --onefile --windowed --name TodoSimple main.py
```

> 另有 `package.py`，是**第三条**打包路径，默认执行效果与 `build.py` 相同
> （都是 `PyInstaller todosimple.spec -y`）。它有一处真实缺陷：
> `--project-dir` 的路径处理写成了 `Path(project_dir or __file__).parent` ——
> `.parent` 对两个分支都生效，传入 `--project-dir /home/todosimple` 实际会得到 `/home`。
> 它的帮助文本还宣传了 `--onefile`，但该参数并未注册（用了会报 unrecognized arguments），
> 且 `build_exe(self, onefile=False)` 的这个形参在函数体里从未被读取。
> 建议统一使用 `build.py`。

## 产物

| 项 | 值 |
|---|---|
| 路径 | `dist/TodoSimple.exe` |
| 形态 | 单文件（onefile），无控制台窗口 |
| 大小 | 约 43.5 MB |
| 启动 | 每次运行都要把内置的 Qt 解压到 `%TEMP%`，首次几秒，之后略快 |

产物名由 spec 里的 `name='TodoSimple'` 决定。

> 根目录还有一个 `build_exe.spec`，是遗留副本：它的 `name='todosimple'` 会产出**小写**的
> `dist/todosimple.exe`，且其中若干字段是 PyInstaller 5 时代的写法。它仍能构建成功，
> 但两份 spec 并存会让产物名混淆 —— 当前以 `todosimple.spec` 为准。

## 用户数据

数据不在 exe 旁边，也不随 exe 移动：

```
%USERPROFILE%\.todosimple\todos.json     待办数据
%USERPROFILE%\.todosimple\config.json    配置（快捷键、开机自启）
```

注意不是 `%APPDATA%`。卸载后需要手动删除这个目录。

## 开机自启

`autostart.py` 往注册表 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
写当前用户的自启项。打包后写入的是 `sys.executable`，也就是 exe 自身的路径 ——
所以**移动过 exe 之后需要重新勾选一次**「开机时自动启动」。

## 体积与瘦身

43.5 MB 几乎全部来自 Qt。实测占用最大的几个内置文件：

| 文件 | 大小 |
|---|---|
| `PySide6\opengl32sw.dll` | 7.3 MB |
| `PySide6\Qt6Gui.dll` | 4.0 MB |
| `PySide6\Qt6Core.dll` | 3.5 MB |
| `PySide6\Qt6Widgets.dll` | 2.8 MB |
| `PySide6\Qt6Quick.dll` | 2.8 MB |
| `PySide6\Qt6Pdf.dll` | 2.3 MB |
| `PySide6\Qt6Qml.dll` | 2.0 MB |
| `python310.dll` | 1.9 MB |

本程序只用到 QtCore / QtGui / QtWidgets。`opengl32sw.dll`、`Qt6Quick`、`Qt6Qml`、
`Qt6Pdf`、`Qt6Svg`、`Qt6VirtualKeyboard` 以及 `plugins\imageformats\qpdf.dll`、
`plugins\iconengines\qsvgicon.dll` 都是被 PyInstaller 的 PySide6 hook 顺带收进来的，
用 `excludes` 排除掉可以明显减小体积。

`todosimple.spec` 里的 `upx=True` 已经打开，但需要本机装有 UPX 才生效，没装会静默跳过。

## 故障排查

### 打包时报 `No module named PyInstaller`

多半是用了没有装 PyInstaller 的解释器。`build.py` 会自动补装；手动路径下先执行
`python -m pip install pyinstaller`。

### 中文 Windows 控制台报 `UnicodeEncodeError`

中文版 Windows 控制台默认 GBK 编码，打印 emoji 会直接抛异常。
`build.py` 已通过 `sys.stdout.reconfigure(errors="replace")` 把日志限制在 ASCII 符号
（`[OK]`、`[BUILD]` 等）来规避。

### exe 双击没反应

`console=False` 意味着没有控制台输出可看。临时把 `todosimple.spec` 里 `EXE(...)` 的
`console` 改成 `True` 重新打包，就能看到真实的报错。

### 热键没反应

程序在 Windows 原生环境下热键是完全可用的；只有在 WSL2（WSLg）里直接跑源码时，
全局热键依赖 X 事件，焦点不在 WSLg 窗口上就捕获不到。这种情况下右下角悬浮窗始终可点。

## 可选：NSIS 安装包

仓库里有两个 NSIS 脚本，**目前都不能直接编译出可用的安装包**：

| 脚本 | 状态 |
|---|---|
| `TodoSimple.nsi` | 第 26 行 `File /r "dist\TodoSimple\*.*"` 指向 onedir 布局的目录 `dist\TodoSimple\`，而当前产物是单文件 `dist/TodoSimple.exe` —— **编译直接失败**。另外它用了 `SetShellVarContext all` 却没有自提权，非管理员安装会失败，也不写「添加/删除程序」条目。 |
| `todosimple_installer.nsi` | 内容更完整：有 `.onInit` 自提权、有标准的卸载注册表项（会出现在「添加/删除程序」里）、逐文件卸载。可以编译，但第 17 行 `OutFile "..\dist\..."` 里的 `..\` 会把安装包写到项目目录之外，应从项目根目录编译并删掉 `..\`。 |

编译命令（需先安装 [NSIS](https://nsis.sourceforge.io/)，默认装在 `C:\Program Files (x86)\NSIS\`）：

```bat
"C:\Program Files (x86)\NSIS\makensis.exe" todosimple_installer.nsi
```

## 图标

**当前 exe 没有自定义图标** —— `todosimple.spec` 的 `EXE(...)` 里没有 `icon=` 参数。

`generate_icon.py` 想解决这件事，但现在既跑不通也用不上：它依赖 Pillow（不在
`requirements.txt` 里），输出文件名是 `app.ico`，而没有任何 spec 读这个文件。
要启用需要三处改动：把 Pillow 装进打包环境、输出改名 `todosimple.ico`、
在 spec 的 `EXE(...)` 里加上

```python
icon='todosimple.ico' if Path('todosimple.ico').exists() else None
```

## 分发

- 直接分发 `dist/TodoSimple.exe`，双击运行，目标机器无需 Python 环境。
- 或压缩后分发：

```powershell
Compress-Archive -Path dist/TodoSimple.exe -DestinationPath TodoSimple-Portable.zip
```

## 相关文件

```
main.py            入口：装配各模块、托盘、信号连接
ui.py              TodoOverlay / CornerWidget / SettingsDialog
storage.py         TodoStore：数据模型 + JSON 原子持久化
config.py          Config：配置加载保存
hotkey.py          pynput 后台线程全局热键 → Qt 信号
autostart.py       Windows 开机自启（注册表）
build.py           一键打包
todosimple.spec    当前使用的 PyInstaller 配置
```