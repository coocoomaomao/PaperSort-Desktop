#define MyAppName "PaperSort Desktop"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "MeowBuild Lab"
#define MyAppExeName "PaperSort-Desktop.exe"

[Setup]
AppId={{EFDDAF79-59EC-4FB4-BDAF-B894791B1F21}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\PaperSort Desktop
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist-installer
OutputBaseFilename=PaperSort-Desktop-v0.1.0-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\build\papersort.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "..\dist\PaperSort-Desktop\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\docs\PRIVACY.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加快捷方式："; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent
