; DogeSolo - Windows Installer Script (Inno Setup 6+)
; Descarrega Inno Setup: https://jrsoftware.org/isdl.php

#define AppName "DogeSolo"
#define AppVersion "1.0.0"
#define AppPublisher "DogeSolo Project"
#define AppURL "https://github.com/dogesolo/dogesolo"
#define AppExeName "DogeSolo.exe"

[Setup]
AppId={{A7F3E2B1-4C8D-4E5F-9A0B-1D2E3F4A5B6C}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
LicenseFile=..\..\LICENSE
OutputDir=..\..\dist\windows
OutputBaseFilename=DogeSolo-Setup-{#AppVersion}
SetupIconFile=..\..\src\resources\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#AppExeName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Requerir Windows 10+
MinVersion=10.0.17763

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "catalan"; MessagesFile: "compiler:Languages\Catalan.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Iniciar DogeSolo amb Windows"; GroupDescription: "Inici automàtic:"; Flags: unchecked

[Files]
Source: "..\..\dist\DogeSolo.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\src\resources\*"; DestDir: "{app}\resources"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; No eliminar les dades del node (~/.dogecoin) ni la config (~/.dogesolo)
; L'usuari ha de fer-ho manualment si vol

[Messages]
WelcomeLabel2=Això instal·larà [name/ver] al teu ordinador.%n%nDogeSolo et permet minar Dogecoin en solitari directament des del teu PC.%n%nNecessitaràs ~60 GB d'espai lliure per sincronitzar la blockchain.

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;