; Inno Setup script for the Windows installer. CI passes the version:
;   iscc /DAppVersion=0.1.0 installer\windows.iss
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{0B8D4E62-91A7-4F25-B3C0-7E5D2A9F6C02}
AppName=Mix Ready
AppVersion={#AppVersion}
AppPublisher=ROMMUSER
AppPublisherURL=https://github.com/axelfj/mix-ready
DefaultDirName={autopf}\Mix Ready
DefaultGroupName=Mix Ready
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
LicenseFile=..\LICENSE
OutputDir=Output
OutputBaseFilename=MixReady-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\MixReady.exe

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\MixReady\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Mix Ready"; Filename: "{app}\MixReady.exe"
Name: "{group}\Uninstall Mix Ready"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Mix Ready"; Filename: "{app}\MixReady.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\MixReady.exe"; Description: "{cm:LaunchProgram,Mix Ready}"; Flags: nowait postinstall skipifsilent
