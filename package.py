#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TodoSimple 应用打包脚本
一键生成 Windows .exe 可执行程序

使用方式：
    python package.py                # 默认打包
    python package.py --onefile       # 单文件 exe
    python package.py --clean         # 清除旧构建
    python package.py --help          # 显示帮助

要求：
    - Python 3.8+
    - PyInstaller (会自动安装)
    - 依赖项 (会自动安装)
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


class PackageBuilder:
    """TodoSimple 应用打包器"""
    
    def __init__(self, project_dir=None, verbose=False):
        """初始化打包器"""
        self.project_dir = Path(project_dir or __file__).parent.absolute()
        self.verbose = verbose
        self.start_time = datetime.now()
        
        # 关键文件/目录
        self.dist_dir = self.project_dir / 'dist'
        self.build_dir = self.project_dir / 'build'
        self.spec_file = self.project_dir / 'todosimple.spec'
        self.requirements_file = self.project_dir / 'requirements.txt'
        
        # 验证项目结构
        self._validate_project()
    
    def _validate_project(self):
        """验证项目是否完整"""
        required_files = [
            self.project_dir / 'main.py',
            self.spec_file,
            self.requirements_file,
        ]
        
        for file in required_files:
            if not file.exists():
                self.error(f"缺少必要文件: {file.name}")
                sys.exit(1)
    
    def log(self, msg, level='INFO'):
        """打印日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if level == 'INFO':
            print(f"[{timestamp}] ℹ️  {msg}")
        elif level == 'SUCCESS':
            print(f"[{timestamp}] ✅ {msg}")
        elif level == 'WARN':
            print(f"[{timestamp}] ⚠️  {msg}")
        elif level == 'ERROR':
            print(f"[{timestamp}] ❌ {msg}")
        elif level == 'STEP':
            print(f"\n{'='*70}")
            print(f"[{timestamp}] 🔨 {msg}")
            print('='*70)
    
    def error(self, msg):
        """打印错误并退出"""
        self.log(msg, 'ERROR')
        sys.exit(1)
    
    def run_cmd(self, cmd, description, fatal=True):
        """执行命令"""
        self.log(description, 'STEP')
        
        if self.verbose:
            print(f"  命令: {' '.join(cmd)}\n")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                capture_output=not self.verbose,
                text=True
            )
            
            if result.returncode != 0:
                if not self.verbose and result.stderr:
                    print(result.stderr)
                
                if fatal:
                    self.error(f"{description} 失败 (代码: {result.returncode})")
                else:
                    self.log(f"{description} 失败，继续进行", 'WARN')
                    return False
            
            self.log(f"{description} 成功", 'SUCCESS')
            return True
            
        except Exception as e:
            if fatal:
                self.error(f"{description} 异常: {e}")
            else:
                self.log(f"{description} 异常: {e}", 'WARN')
                return False
    
    def check_dependencies(self):
        """检查和安装依赖"""
        self.log("检查 Python 依赖", 'STEP')
        
        # 检查 PyInstaller
        try:
            import PyInstaller
            version = PyInstaller.__version__
            self.log(f"PyInstaller 已安装 (v{version})", 'SUCCESS')
        except ImportError:
            self.log("安装 PyInstaller", 'INFO')
            self.run_cmd(
                [sys.executable, '-m', 'pip', 'install', '-q', 'pyinstaller'],
                "安装 PyInstaller"
            )
        
        # 检查项目依赖
        self.log("检查项目依赖", 'INFO')
        try:
            import PySide6
            import pynput
            self.log("PySide6 和 pynput 已安装", 'SUCCESS')
        except ImportError:
            self.log("安装项目依赖", 'INFO')
            self.run_cmd(
                [sys.executable, '-m', 'pip', 'install', '-q', '-r', 
                 str(self.requirements_file)],
                "安装项目依赖"
            )
    
    def clean_build(self):
        """清除旧的构建文件"""
        self.log("清除旧的构建文件", 'STEP')
        
        for dir_path in [self.dist_dir, self.build_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                self.log(f"已删除 {dir_path.name}/", 'INFO')
    
    def build_exe(self, onefile=False):
        """使用 PyInstaller 打包"""
        self.log("使用 PyInstaller 打包应用", 'STEP')
        
        cmd = [
            sys.executable,
            '-m', 'PyInstaller',
            str(self.spec_file),
            '-y',  # 覆盖输出目录
        ]
        
        self.run_cmd(cmd, "打包应用程序")
    
    def verify_output(self):
        """验证输出"""
        self.log("验证输出文件", 'STEP')
        
        exe_path = self.dist_dir / 'TodoSimple.exe'
        
        if not exe_path.exists():
            self.error(f"未生成 exe 文件: {exe_path}")
        
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        self.log(f"生成 {exe_path.name} ({size_mb:.2f} MB)", 'SUCCESS')
        
        return exe_path
    
    def create_launcher(self):
        """创建启动脚本"""
        self.log("创建辅助启动脚本", 'STEP')
        
        # 批处理启动器
        launcher_bat = self.dist_dir / 'TodoSimple_launcher.bat'
        launcher_bat.write_text(
            '@echo off\n'
            'cd /d "%~dp0"\n'
            'start "" "TodoSimple.exe"\n',
            encoding='gbk'
        )
        self.log(f"已创建 {launcher_bat.name}", 'SUCCESS')
        
        # PowerShell 启动器
        launcher_ps1 = self.dist_dir / 'TodoSimple_launcher.ps1'
        launcher_ps1.write_text(
            '& ".\TodoSimple.exe"\n',
            encoding='utf-8'
        )
        self.log(f"已创建 {launcher_ps1.name}", 'SUCCESS')
    
    def create_readme(self):
        """创建输出目录的 README"""
        self.log("创建 README 文件", 'STEP')
        
        readme_path = self.dist_dir / 'README.txt'
        readme_content = """TodoSimple - Todo 悬浮工具
========================================

📦 应用说明
这是 TodoSimple 应用的 Windows 可执行程序

🚀 快速开始
1. 双击 TodoSimple.exe 运行
2. 按 F2 呼出 Todo 窗口
3. 按 ESC 最小化到右下角

⌨️  快捷键
- F2: 呼出/隐藏 Todo 窗口
- ESC: 最小化到右下角
- 右键: 打开菜单

📂 配置文件
数据保存在: %APPDATA%\\todosimple\\
- todos.json: 待办事项数据
- config.json: 配置和快捷键

🔧 功能
✓ 全屏 Todo 遮罩
✓ 自定义快捷键
✓ 系统托盘集成
✓ 自动数据保存
✓ 轻量级应用

📋 系统要求
- Windows 7 或更新版本
- 256 MB RAM 最低
- 50 MB 硬盘空间

💡 提示
- 首次运行会初始化配置
- 配置会自动保存
- 数据只保存在本地
- 应用完全离线运行

问题排查:
- 快捷键冲突: 在菜单中设置新的快捷键
- 数据丢失: 检查 %APPDATA%\\todosimple\\ 目录
- 无法启动: 更新 Windows 到最新版本
"""
        readme_path.write_text(readme_content, encoding='utf-8')
        self.log(f"已创建 {readme_path.name}", 'SUCCESS')
    
    def print_summary(self, exe_path):
        """打印总结"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print(f"\n{'='*70}")
        print("✅ 打包完成！")
        print('='*70)
        print(f"\n📁 输出文件:")
        print(f"  📄 {exe_path.name}")
        print(f"    大小: {exe_path.stat().st_size / (1024*1024):.2f} MB")
        print(f"    路径: {exe_path}")
        
        print(f"\n📚 辅助文件:")
        print(f"  📜 TodoSimple_launcher.bat (Windows 批处理启动器)")
        print(f"  📜 TodoSimple_launcher.ps1 (PowerShell 启动器)")
        print(f"  📄 README.txt (应用说明)")
        
        print(f"\n⏱️  耗时: {elapsed:.1f} 秒")
        
        print(f"\n🚀 下一步:")
        print(f"  1. 测试: 双击 {exe_path.name} 验证功能")
        print(f"  2. 分发: 将 exe 文件发送给用户")
        print(f"  3. 创建安装程序 (可选):")
        print(f"     - 下载 NSIS: https://nsis.sourceforge.io/")
        print(f"     - 编译 TodoSimple.nsi 脚本")
        
        print(f"\n📖 文档:")
        print(f"  - PACKAGING_GUIDE.md: 详细打包指南")
        print(f"  - QUICKSTART.txt: 快速开始指南")
        print(f"  - 项目 README.md: 应用功能说明")
        print('='*70 + "\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='TodoSimple Windows 应用打包工具',
        epilog='示例: python package.py --clean --verbose'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='清除旧的构建文件后打包'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细输出'
    )
    parser.add_argument(
        '--skip-dependencies',
        action='store_true',
        help='跳过依赖检查'
    )
    parser.add_argument(
        '--project-dir',
        default=None,
        help='项目目录 (默认为脚本所在目录)'
    )
    
    args = parser.parse_args()
    
    try:
        # 创建打包器
        builder = PackageBuilder(args.project_dir, args.verbose)
        
        print("\n" + "="*70)
        print("📦 TodoSimple Windows 打包工具")
        print("="*70)
        print(f"项目目录: {builder.project_dir}\n")
        
        # 清除旧构建
        if args.clean:
            builder.clean_build()
        
        # 检查依赖
        if not args.skip_dependencies:
            builder.check_dependencies()
        
        # 打包应用
        builder.build_exe()
        
        # 验证输出
        exe_path = builder.verify_output()
        
        # 创建辅助文件
        builder.create_launcher()
        builder.create_readme()
        
        # 打印总结
        builder.print_summary(exe_path)
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断打包过程")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 打包失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
