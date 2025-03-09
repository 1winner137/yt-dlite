@echo off
setlocal enabledelayedexpansion

:: Check for administrator privileges
NET SESSION >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [33mWARNING: This script is not running with administrator privileges.[0m
    echo Some features may not work properly.
    echo It's recommended to run this script as administrator.
    echo.
    set /p CONTINUE="Do you want to continue with limited installation? (y/n): "
    if /i not "!CONTINUE!"=="y" (
        echo Installation aborted.
        pause
        exit /b 1
    )
    
    :: Set installation paths for non-admin user
    set "INSTALL_DIR=%LOCALAPPDATA%\Programs\YT-Lite"
    set "IS_ADMIN=0"
) else (
    :: Set installation paths for admin user
    set "INSTALL_DIR=%ProgramFiles%\YT-Lite"
    set "IS_ADMIN=1"
)

echo Installation directory: %INSTALL_DIR%

:: Install required Python packages
echo Installing required Python packages...
pip3 install argparse yt-dlp
if %ERRORLEVEL% neq 0 (
    echo Failed to install Python packages with pip3. Trying pip...
    pip install argparse yt-dlp
    if %ERRORLEVEL% neq 0 (
        echo [31mFailed to install Python packages. Please make sure pip is installed.[0m
        pause
        exit /b 1
    )
)
echo [32mRequired Python packages installed successfully.[0m

:: Create program directory
echo Creating program directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
echo Program directory created successfully.

:: Copy Python files
echo Copying Python files...
:: Assuming the Python files are in the current directory
copy /Y "yt-lite.py" "%INSTALL_DIR%\"
copy /Y "yt-liteg.py" "%INSTALL_DIR%\"
echo [32mPython files copied successfully.[0m

:: Create batch files and executables
echo Creating executables and batch files...

:: Create batch files first
echo @echo off > "%INSTALL_DIR%\yt-lite.bat"
echo python "%INSTALL_DIR%\yt-lite.py" %%* >> "%INSTALL_DIR%\yt-lite.bat"

echo @echo off > "%INSTALL_DIR%\yt-liteg.bat"
echo start pythonw "%INSTALL_DIR%\yt-liteg.py" %%* >> "%INSTALL_DIR%\yt-liteg.bat"

:: Create wrapper EXE files using PowerShell
echo Creating EXE wrappers...
echo $code = @'> "%TEMP%\create_exe.ps1"
echo using System;>> "%TEMP%\create_exe.ps1"
echo using System.Diagnostics;>> "%TEMP%\create_exe.ps1"
echo using System.Reflection;>> "%TEMP%\create_exe.ps1"
echo using System.IO;>> "%TEMP%\create_exe.ps1"
echo.>> "%TEMP%\create_exe.ps1"
echo [assembly: AssemblyTitle("YT-Lite")]>> "%TEMP%\create_exe.ps1"
echo [assembly: AssemblyDescription("YouTube Downloader")]>> "%TEMP%\create_exe.ps1"
echo [assembly: AssemblyCompany("YT-Lite")]>> "%TEMP%\create_exe.ps1"
echo [assembly: AssemblyProduct("YT-Lite")]>> "%TEMP%\create_exe.ps1"
echo [assembly: AssemblyCopyright("YT-Lite")]>> "%TEMP%\create_exe.ps1"
echo [assembly: AssemblyVersion("1.0.0.0")]>> "%TEMP%\create_exe.ps1"
echo.>> "%TEMP%\create_exe.ps1"
echo namespace YTLite {>> "%TEMP%\create_exe.ps1"
echo     class Program {>> "%TEMP%\create_exe.ps1"
echo         static void Main(string[] args) {>> "%TEMP%\create_exe.ps1"
echo             string exePath = Process.GetCurrentProcess().MainModule.FileName;>> "%TEMP%\create_exe.ps1"
echo             string exeDir = Path.GetDirectoryName(exePath);>> "%TEMP%\create_exe.ps1"
echo             string scriptName = Path.GetFileNameWithoutExtension(exePath) + ".bat";>> "%TEMP%\create_exe.ps1"
echo             string scriptPath = Path.Combine(exeDir, scriptName);>> "%TEMP%\create_exe.ps1"
echo.>> "%TEMP%\create_exe.ps1"
echo             if (!File.Exists(scriptPath)) {>> "%TEMP%\create_exe.ps1"
echo                 Console.WriteLine("Error: Could not find " + scriptName);>> "%TEMP%\create_exe.ps1"
echo                 return;>> "%TEMP%\create_exe.ps1"
echo             }>> "%TEMP%\create_exe.ps1"
echo.>> "%TEMP%\create_exe.ps1"
echo             ProcessStartInfo psi = new ProcessStartInfo();>> "%TEMP%\create_exe.ps1"
echo             psi.FileName = scriptPath;>> "%TEMP%\create_exe.ps1"
echo             psi.UseShellExecute = false;>> "%TEMP%\create_exe.ps1"
echo             psi.CreateNoWindow = true;>> "%TEMP%\create_exe.ps1"
echo.>> "%TEMP%\create_exe.ps1"
echo             if (args.Length > 0) {>> "%TEMP%\create_exe.ps1"
echo                 psi.Arguments = string.Join(" ", args);>> "%TEMP%\create_exe.ps1"
echo             }>> "%TEMP%\create_exe.ps1"
echo.>> "%TEMP%\create_exe.ps1"
echo             Process.Start(psi);>> "%TEMP%\create_exe.ps1"
echo         }>> "%TEMP%\create_exe.ps1"
echo     }>> "%TEMP%\create_exe.ps1"
echo }>> "%TEMP%\create_exe.ps1"
echo '@>> "%TEMP%\create_exe.ps1"
echo.>> "%TEMP%\create_exe.ps1"
echo Add-Type -TypeDefinition $code -OutputAssembly "%INSTALL_DIR%\yt-lite.exe" -OutputType WindowsExe>> "%TEMP%\create_exe.ps1"
echo.>> "%TEMP%\create_exe.ps1"
echo $codeGUI = $code.Replace("UseShellExecute = false;", "UseShellExecute = false;").Replace("CreateNoWindow = true;", "CreateNoWindow = true;")>> "%TEMP%\create_exe.ps1"
echo Add-Type -TypeDefinition $codeGUI -OutputAssembly "%INSTALL_DIR%\yt-liteg.exe" -OutputType WindowsExe>> "%TEMP%\create_exe.ps1"

powershell -ExecutionPolicy Bypass -File "%TEMP%\create_exe.ps1"
if %ERRORLEVEL% neq 0 (
    echo [33mFailed to create EXE wrappers. Batch files will still work.[0m
) else (
    echo [32mEXE wrappers created successfully.[0m
)

:: Add to PATH based on admin status
echo Adding YT-Lite to PATH...
if "%IS_ADMIN%"=="1" (
    :: System-wide PATH update
    setx /M PATH "%PATH%;%INSTALL_DIR%"
    echo [32mYT-Lite added to system PATH.[0m
) else (
    :: User PATH update
    setx PATH "%PATH%;%INSTALL_DIR%"
    echo [32mYT-Lite added to user PATH.[0m
    echo [33mNote: This will only affect new command prompts.[0m
)

:: Create shortcuts on desktop
echo Creating desktop shortcuts...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\YT-Lite CLI.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\yt-lite.exe'; $Shortcut.Save()"
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\YT-Lite GUI.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\yt-liteg.exe'; $Shortcut.Save()"
echo [32mDesktop shortcuts created successfully.[0m

:: Create Start Menu shortcuts
echo Creating Start Menu shortcuts...
set "START_MENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\YT-Lite"
if not exist "%START_MENU_DIR%" mkdir "%START_MENU_DIR%"
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU_DIR%\YT-Lite CLI.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\yt-lite.exe'; $Shortcut.Save()"
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU_DIR%\YT-Lite GUI.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\yt-liteg.exe'; $Shortcut.Save()"
echo [32mStart Menu shortcuts created successfully.[0m

echo [32mYT-Lite installation completed successfully![0m
echo You can now use 'yt-lite' or 'yt-liteg' from the command line.
echo You can also use the desktop or Start Menu shortcuts.

if "%IS_ADMIN%"=="0" (
    echo.
    echo [33mSince you installed without administrator privileges:[0m
    echo 1. The application was installed to: %INSTALL_DIR%
    echo 2. PATH changes will only affect new command prompts
    echo 3. You may need to restart your command prompt or computer for the PATH changes to take effect
)

pause
