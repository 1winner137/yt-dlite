@echo off
echo ===== YT-DLite Installation for Windows =====
echo Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo or download the precompiled version from:
    echo https://github.com/1winner137/yt-dlite/releases
    pause
    exit /b 1
)
echo Python is installed. Installing yt-dlp...
pip install -U yt-dlp
echo Checking for ffmpeg...
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: ffmpeg not found in PATH. Some features may not work.
    echo You can download ffmpeg from https://ffmpeg.org/download.html
    echo or use the precompiled version from:
    echo https://github.com/1winner137/yt-dlite/releases
)
echo Checking for required files...
if not exist ..\yt-dlite.py (
    echo ERROR: yt-dlite.py not found in the parent directory.
    echo Please make sure you are in the correct directory.
    pause
    exit /b 1
)
if not exist ..\yt-dlitec.py (
    echo ERROR: yt-dlitec.py not found in the parent directory.
    echo Please make sure you are in the correct directory.
    pause
    exit /b 1
)
if not exist ..\misc.py (
    echo ERROR: misc.py not found in the parent directory.
    echo This file is required for yt-dlite to function properly.
    pause
    exit /b 1
)
echo Creating shortcuts for YT-DLite...
echo @echo off > yt-dlite.bat
echo python "%~dp0..\yt-dlite.py" %%* >> yt-dlite.bat
echo @echo off > yt-dlitec.bat
echo python "%~dp0..\yt-dlitec.py" %%* >> yt-dlitec.bat
echo Installation completed successfully!
echo ----------------------------------------
echo You can now run:
echo   - yt-dlite.bat for the GUI version
echo   - yt-dlitec.bat for the terminal version
echo If you encounter any issues, report but you can check the precompiled version at:
echo https://github.com/1winner137/yt-dlite/releases
pause
