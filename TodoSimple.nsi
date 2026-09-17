; NSIS 安装程序脚本 - TodoSimple (Todo 悬浮工具)
; 使用方法: 用 NSIS (makensis) 编译这个脚本

!include "MUI2.nsh"

; 基础信息
Name "TodoSimple - Todo 悬浮工具"
OutFile "dist\TodoSimple-Installer.exe"
InstallDir "$PROGRAMFILES\TodoSimple"
InstallDirRegKey HKCU "Software\TodoSimple" ""

; MUI 设置
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "SimplifiedChinese"
!insertmacro MUI_LANGUAGE "English"

; 安装器部分
Section "Install"
  SetOutPath "$INSTDIR"
  
  ; 从 PyInstaller 输出复制文件
  File /r "dist\TodoSimple\*.*"
  
  ; 创建开始菜单快捷方式
  SetShellVarContext all
  CreateDirectory "$SMPROGRAMS\TodoSimple"
  CreateShortCut "$SMPROGRAMS\TodoSimple\TodoSimple.lnk" "$INSTDIR\TodoSimple.exe"
  CreateShortCut "$SMPROGRAMS\TodoSimple\Uninstall.lnk" "$INSTDIR\uninstall.exe"
  
  ; 创建桌面快捷方式
  CreateShortCut "$DESKTOP\TodoSimple.lnk" "$INSTDIR\TodoSimple.exe"
  
  ; 保存安装路径到注册表
  WriteRegStr HKCU "Software\TodoSimple" "" $INSTDIR
  
  ; 创建卸载程序
  WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

; 卸载器部分
Section "Uninstall"
  SetShellVarContext all
  
  ; 删除文件和目录
  RMDir /r "$INSTDIR"
  
  ; 删除开始菜单项
  RMDir /r "$SMPROGRAMS\TodoSimple"
  
  ; 删除桌面快捷方式
  Delete "$DESKTOP\TodoSimple.lnk"
  
  ; 删除注册表项
  DeleteRegKey HKCU "Software\TodoSimple"
SectionEnd
