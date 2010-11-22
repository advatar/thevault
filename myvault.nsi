;NSIS Modern User Interface
;Basic Example Script
;Written by Joost Verburg

;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"

;--------------------------------
;General

  ;Name and file
  Name "MyCube Vault"
  OutFile "setup.exe"

  ;Default installation folder
  InstallDir "$PROGRAMFILES\MyCube Vault"
  
  ;Get installation folder from registry if available
  InstallDirRegKey HKCU "Software\MyCube Vault" ""

  ;Request application privileges for Windows Vista
  RequestExecutionLevel admin

;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING

;--------------------------------
;Pages

#  !insertmacro MUI_PAGE_LICENSE "${NSISDIR}\Docs\Modern UI\License.txt"
  !insertmacro MUI_PAGE_LICENSE "license.txt"
#  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES
  
;--------------------------------
;Languages
 
  !insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections

Section "MyCube Vault"

  SetOutPath "$INSTDIR"
  
  ;ADD YOUR OWN FILES HERE...
  File /r build\exe.win32-2.7\*
  ;Store installation folder
  WriteRegStr HKCU "Software\MyCube Vault" "" $INSTDIR
  
  ;Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Shortcuts"
  CreateDirectory "$SMPROGRAMS\MyCube Vault"
  CreateShortCut "$SMPROGRAMS\MyCube Vault\MyCube Vault.lnk" "$INSTDIR\launcherwindows.exe" "" "$INSTDIR\launcherwindows.exe" 0
  CreateShortCut "$SMPROGRAMS\MyCube Vault\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
  CreateShortCut "$SMSTARTUP\MyCube Vault.lnk" "$INSTDIR\launcherwindows.exe"
SectionEnd

Section "BackupDir"
    CreateDirectory "$APPDATA\MyCube Vault"
    #CopyFiles /SILENT "$INSTDIR\mc.db" "$APPDATA\MyVault"
SectionEnd

;--------------------------------
;Descriptions

  ;Language strings
  ;LangString DESC_SecDummy ${LANG_ENGLISH} "A test section."

  ;Assign language strings to sections
  ;!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  ;  !insertmacro MUI_DESCRIPTION_TEXT ${SecDummy} $(DESC_SecDummy)
  ;!insertmacro MUI_FUNCTION_DESCRIPTION_END

;--------------------------------
;Uninstaller Section

Section "Uninstall"

  ;ADD YOUR OWN FILES HERE...

  Delete "$INSTDIR\Uninstall.exe"

  RMDir /r "$SMPROGRAMS\MyCube Vault"
  RMDir /r "$INSTDIR"
  Delete "$SMSTARTUP\MyCube Vault.lnk"
  # let's leave all user data for now
  #RMDIR /r "$APPDATA\MyVault"

  DeleteRegKey /ifempty HKCU "Software\MyCube Vault"

SectionEnd

