; Inno Setup 安装包配置 - 暮橙体育记账本
; 使用方式: iscc build/installer.iss

#define MyAppName      "暮橙体育记账本"
#define MyAppExeName   "暮橙记账本.exe"
#define MyAppVersion   "dev"
#define MyAppPublisher "暮橙体育"

[Setup]
AppId={{B8F2E3A1-5C4D-4E6F-8A9B-1C2D3E4F5A6B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\暮橙记账本
DefaultGroupName={#MyAppName}
OutputBaseFilename=mucheng-book_setup
OutputDir=..\dist
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#MyAppName}

[Languages]
Name: "default"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; 打包 PyInstaller 输出的整个目录
Source: "..\dist\暮橙记账本\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent
