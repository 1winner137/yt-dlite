@echo off
setlocal enabledelayedexpansion

echo YT-DLite Installer with FFmpeg
echo ==============================
echo.

:: ===== FFmpeg Installation Section =====
echo FFmpeg Automatic Installer
echo ========================
echo.
:: Create temp directory for downloads
set "TEMP_DIR=%TEMP%\ffmpeg_installer"
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"
:: Set installation directory
set "INSTALL_DIR=C:\ffmpeg"
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
:: Detect architecture
echo Detecting system architecture...
if exist "%PROGRAMFILES(X86)%" (
    echo 64-bit system detected.
    set "ARCH=64"
    set "DOWNLOAD_URL=https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
) else (
    echo 32-bit system detected.
    set "ARCH=32"
    set "DOWNLOAD_URL=https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win32-gpl.zip"
)
:: Download FFmpeg
echo Downloading FFmpeg for Windows %ARCH%-bit...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%TEMP_DIR%\ffmpeg.zip'}"
if not exist "%TEMP_DIR%\ffmpeg.zip" (
    echo Failed to download FFmpeg. Please check your internet connection.
    goto :ffmpeg_cleanup
)
:: Extract the zip file
echo Extracting files...
powershell -Command "& {Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::ExtractToDirectory('%TEMP_DIR%\ffmpeg.zip', '%TEMP_DIR%')}"
:: Find the bin directory in the extracted folder
for /d %%D in ("%TEMP_DIR%\ffmpeg-*") do (
    if exist "%%D\bin" (
        echo Copying FFmpeg files to %INSTALL_DIR%...
        xcopy "%%D\bin\*" "%INSTALL_DIR%\" /E /H /C /I /Y
        goto :add_to_path
    )
)
echo Could not find FFmpeg bin directory in the extracted files.
goto :ffmpeg_cleanup
:add_to_path
:: Add to PATH environment variable
echo Adding FFmpeg to PATH...
setx PATH "%PATH%;%INSTALL_DIR%" /M
:: Create a test file to verify installation
echo Testing FFmpeg installation...
"%INSTALL_DIR%\ffmpeg.exe" -version > "%TEMP_DIR%\ffmpeg_test.txt" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [32mFFmpeg was successfully installed![0m
    echo.
    echo FFmpeg is installed in: %INSTALL_DIR%
    echo FFmpeg has been added to your system PATH.
) else (
    echo [31mFFmpeg installation test failed. Please check the logs.[0m
)
:ffmpeg_cleanup
:: Clean up temporary files
echo Cleaning up temporary files...
rd /s /q "%TEMP_DIR%" 2>nul
echo.
echo FFmpeg installation process completed.
echo.

:: ===== YT-DLite Installation Section =====
echo YT-DLite Installation
echo =====================
echo.

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
    set "YTLITE_DIR=%LOCALAPPDATA%\Programs\YT-DLite"
    set "IS_ADMIN=0"
) else (
    :: Set installation paths for admin user
    set "YTLITE_DIR=%ProgramFiles%\YT-DLite"
    set "IS_ADMIN=1"
)

echo Installation directory: %YTLITE_DIR%

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
if not exist "%YTLITE_DIR%" mkdir "%YTLITE_DIR%"
echo Program directory created successfully.

:: Copy Python files
echo Copying Python files...
:: Assuming the Python files are in the current directory
copy /Y "yt-dlitex.py" "%YTLITE_DIR%\"
copy /Y "yt-dlite.py" "%YTLITE_DIR%\"
echo [32mPython files copied successfully.[0m

:: Create batch files and executables
echo Creating executables and batch files...

:: Create batch files first
echo @echo off > "%YTLITE_DIR%\yt-dlite4cmd.bat"
echo python "%YTLITE_DIR%\yt-dlitex.py" %%* >> "%YTLITE_DIR%\yt-dlite4cmd.bat"

echo @echo off > "%YTLITE_DIR%\yt-dlite.bat"
echo start pythonw "%YTLITE_DIR%\yt-dlite.py" %%* >> "%YTLITE_DIR%\yt-dlite.bat"

:: Create wrapper EXE files using PowerShell
echo Creating EXE wrappers...
echo $code = @'> "%TEMP%\create_exe.ps1"
echo using System;>> "%TEMP%\create_exe.ps1"
echo using System.Diagnostics;>> "%TEMP%\create_exe.ps1"
echo using System.Reflection;>> "%TEMP%\create_exe.ps1"
echo using System.IO;>> "%TEMP%\create_exe.ps1"
echo.>> "%TEMP%\create_exe.ps1"
echo [assembly: AssemblyTitle("YT-DLite")]>> "%TEMP%\create_exe.ps1"
echo [assembly: AssemblyDescription("YouTube Downloader")]>> "%TEMP%\create_exe.ps1"
echo [assembly: AssemblyCompany("YT-DLite")]>> "%TEMP%\create_exe.ps1"
echo [assembly: AssemblyProduct("YT-DLite")]>> "%TEMP%\create_exe.ps1"
echo [assembly: AssemblyCopyright("YT-DLite")]>> "%TEMP%\create_exe.ps1"
echo [assembly: AssemblyVersion("1.0.0.0")]>> "%TEMP%\create_exe.ps1"
echo.>> "%TEMP%\create_exe.ps1"
echo namespace YTDLite {>> "%TEMP%\create_exe.ps1"
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
echo Add-Type -TypeDefinition $code -OutputAssembly "%YTLITE_DIR%\yt-dlite4cmd.exe" -OutputType WindowsExe>> "%TEMP%\create_exe.ps1"
echo.>> "%TEMP%\create_exe.ps1"
echo $codeGUI = $code.Replace("UseShellExecute = false;", "UseShellExecute = false;").Replace("CreateNoWindow = true;", "CreateNoWindow = true;")>> "%TEMP%\create_exe.ps1"
echo Add-Type -TypeDefinition $codeGUI -OutputAssembly "%YTLITE_DIR%\yt-dlite.exe" -OutputType WindowsExe>> "%TEMP%\create_exe.ps1"

powershell -ExecutionPolicy Bypass -File "%TEMP%\create_exe.ps1"
if %ERRORLEVEL% neq 0 (
    echo [33mFailed to create EXE wrappers. Batch files will still work.[0m
) else (
    echo [32mEXE wrappers created successfully.[0m
)

:: Add to PATH based on admin status
echo Adding YT-DLite to PATH...
if "%IS_ADMIN%"=="1" (
    :: System-wide PATH update
    setx /M PATH "%PATH%;%YTLITE_DIR%"
    echo [32mYT-DLite added to system PATH.[0m
) else (
    :: User PATH update
    setx PATH "%PATH%;%YTLITE_DIR%"
    echo [32mYT-DLite added to user PATH.[0m
    echo [33mNote: This will only affect new command prompts.[0m
)

:: Create shortcuts on desktop
echo Creating desktop shortcuts...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\YT-DLite CLI.lnk'); $Shortcut.TargetPath = '%YTLITE_DIR%\yt-dlite4cmd.exe'; $Shortcut.Save()"
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\YT-DLite GUI.lnk'); $Shortcut.TargetPath = '%YTLITE_DIR%\yt-dlite.exe'; $Shortcut.Save()"
echo [32mDesktop shortcuts created successfully.[0m

:: Create Start Menu shortcuts
echo Creating Start Menu shortcuts...
set "START_MENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\YT-DLite"
if not exist "%START_MENU_DIR%" mkdir "%START_MENU_DIR%"
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU_DIR%\YT-DLite CLI.lnk'); $Shortcut.TargetPath = '%YTLITE_DIR%\yt-dlite4cmd.exe'; $Shortcut.Save()"
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU_DIR%\YT-DLite GUI.lnk'); $Shortcut.TargetPath = '%YTLITE_DIR%\yt-dlite.exe'; $Shortcut.Save()"
echo [32mStart Menu shortcuts created successfully.[0m

echo [32mYT-DLite installation completed successfully![0m
echo You can now use 'yt-dlite4cmd' or 'yt-dlite' from the command line.
echo You can also use the desktop or Start Menu shortcuts.

if "%IS_ADMIN%"=="0" (
    echo.
    echo [33mSince you installed without administrator privileges:[0m
    echo 1. The application was installed to: %YTLITE_DIR%
    echo 2. PATH changes will only affect new command prompts
    echo 3. You may need to restart your command prompt or computer for the PATH changes to take effect
)

echo.
echo [32mInstallation Complete! Press any key to exit...[0m
pause
endlocal
