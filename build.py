#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""一键把 TodoSimple 打包成 Windows exe。

用法（在 Windows 上、项目根目录）：
    python build.py

产物：dist/TodoSimple.exe
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

# 中文版 Windows 控制台默认是 GBK，输出 emoji 会抛 UnicodeEncodeError。
# 这里统一成「不会崩」的编码，装饰性符号也只使用 ASCII。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(errors="replace")

REQUIRED = ("PySide6", "pynput")
LINE = "=" * 60


def run_command(cmd, desc):
    print(f"\n{LINE}\n[BUILD] {desc}\n{LINE}\n执行: {' '.join(cmd)}")
    if subprocess.run(cmd).returncode != 0:
        print(f"[FAIL] {desc} 失败!")
        sys.exit(1)
    print(f"[OK] {desc} 成功!")


def ensure_module(module, pip_name=None):
    """确认 module 可导入，缺失则 pip 安装。"""
    if subprocess.run([sys.executable, "-c", f"import {module}"],
                      capture_output=True).returncode == 0:
        return
    name = pip_name or module
    print(f"\n[GET] 未检测到 {module}，正在安装 {name} ...")
    run_command([sys.executable, "-m", "pip", "install", name], f"安装 {name}")


def main():
    project_dir = Path(__file__).parent.absolute()
    os.chdir(project_dir)
    print(f"{LINE}\n[PKG] TodoSimple 打包工具\n{LINE}\n项目: {project_dir}")

    if os.name != "nt":
        print("[WARN] 当前不是 Windows：PyInstaller 无法交叉编译，"
              "这里只会产出当前平台的程序，而非 .exe。")
        print("       要得到 Windows exe，请在 Windows 上运行本脚本。")

    # ---- 依赖检查 ----
    print("\n[CHK] 检查依赖...")
    for module in REQUIRED:
        ensure_module(module)
        print(f"  [OK] {module}")
    ensure_module("PyInstaller", "pyinstaller")

    # ---- 清理旧构建 ----
    print("\n[CLN] 清理旧构建...")
    for d in ["build", "dist"]:
        if (project_dir / d).exists():
            shutil.rmtree(project_dir / d)
            print(f"  已删除 {d}/")

    # ---- 打包 ----
    run_command(
        [sys.executable, "-m", "PyInstaller", "todosimple.spec", "-y"],
        "PyInstaller 打包",
    )

    # ---- 附带文件 ----
    print("\n[DOC] 创建启动脚本...")
    (project_dir / "dist" / "TodoSimple_launcher.bat").write_text(
        '@echo off\nstart "" "%~dp0TodoSimple.exe"\n', encoding="utf-8"
    )

    print("\n[DOC] 创建说明文件...")
    (project_dir / "dist" / "README.txt").write_text(
        "TodoSimple - Todo 悬浮工具\n\n"
        "直接双击 TodoSimple.exe 运行\n"
        "按 F2 呼出，ESC 收起到右下角\n\n"
        "数据保存在 %USERPROFILE%\\.todosimple\\\n",
        encoding="utf-8",
    )

    print(f"\n{LINE}\n[OK] 打包完成!\n{LINE}\n"
          f" 输出: dist/TodoSimple.exe\n{LINE}")


if __name__ == "__main__":
    main()