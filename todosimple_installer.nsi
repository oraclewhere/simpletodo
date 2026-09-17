; todosimple 安装程序脚本 (NSIS)
; 使用 NSIS 创建 Windows 安装程序
; 需要先安装 NSIS: https://nsis.sourceforge.io/

!include "MUI2.nsh"
!include "x64.nsh"

; 定义应用信息
!define APPNAME "todosimple"
!define APPVERSION "1.0.0"
!define APPPUBLISHER "todosimple"
!define APPEXE "todosimple.exe"
!define INSTALLDIR "$PROGRAMFILES\${APPNAME}"

; 安装程序名称和文件输出
Name "${APPNAME} ${APPVERSION}"
OutFile "..\dist\todosimple-${APPVERSION}-installer.exe"
InstallDir "${INSTALLDIR}"

; MUI 配置
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; 语言
!insertmacro MUI_LANGUAGE "SimplifiedChinese"
!insertmacro MUI_LANGUAGE "English"

; 检查管理员权限
Function .onInit
  SetShellVarContext all
  UserInfo::GetAccountType
  pop $0
  ${If} $0 != "admin"
    MessageBox MB_ICONEXCLAMATION|MB_TOPMOST "此安装程序需要管理员权限！"
    ExecShell "runas" "$EXEPATH" ""
    Quit
  ${EndIf}
FunctionEnd

; 安装部分
Section "install"
  SetOverwrite ifnewer
  SetOutPath "${INSTALLDIR}"
  
  ; 复制可执行文件和其他文件
  File "dist\${APPEXE}"
  
  ; 创建开始菜单快捷方式
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortcut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "${INSTALLDIR}\${APPEXE}" "" "${INSTALLDIR}\${APPEXE}" 0
  CreateShortcut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"
  
  ; 创建桌面快捷方式
  CreateShortcut "$DESKTOP\${APPNAME}.lnk" "${INSTALLDIR}\${APPEXE}" "" "${INSTALLDIR}\${APPEXE}" 0
  
  ; 写入卸载信息到注册表
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME} ${APPVERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${APPVERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${APPPUBLISHER}"
  
  ; 创建卸载程序
  WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

; 卸载部分
Section "Uninstall"
  SetShellVarContext all
  
  ; 删除应用文件
  Delete "${INSTALLDIR}\${APPEXE}"
  Delete "${INSTALLDIR}\uninstall.exe"
  RMDir "${INSTALLDIR}"
  
  ; 删除快捷方式
  Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
  Delete "$SMPROGRAMS\${APPNAME}\Uninstall.lnk"
  RMDir "$SMPROGRAMS\${APPNAME}"
  Delete "$DESKTOP\${APPNAME}.lnk"
  
  ; 删除注册表项
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
SectionEnd
