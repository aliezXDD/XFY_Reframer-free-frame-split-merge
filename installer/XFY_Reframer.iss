#define AppName "XFY Reframer"
#define AppVersion "1.0.0"
#define AppPublisher "XFY"
#define AppExeName "XFY_Reframer.exe"

[Setup]
AppId={{A1D83E6E-4D36-4E14-B157-4D27D531B985}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=..\release
OutputBaseFilename=XFY_Reframer_Setup_win64
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\XFY_Reframer.ico
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "chinesesimplified"; MessagesFile: "ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"; Flags: unchecked

[Files]
Source: "..\dist\XFY_Reframer\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "启动 {#AppName}"; Flags: nowait postinstall skipifsilent
