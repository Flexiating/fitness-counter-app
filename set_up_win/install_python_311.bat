@echo off
setlocal

py -3.11 --version >nul 2>&1
if not errorlevel 1 (
    echo Python 3.11 is already installed.
    echo You can now run ..\run_windows.bat
    pause
    exit /b 0
)

echo Fitness Counter needs Python 3.11 to run from source code.
echo.
where winget >nul 2>&1
if not errorlevel 1 (
    echo Installing Python 3.11 with Windows Package Manager...
    winget install --id Python.Python.3.11 -e --source winget
    if not errorlevel 1 (
        echo.
        echo Python 3.11 was installed. Close and reopen Command Prompt, then run ..\run_windows.bat
        pause
        exit /b 0
    )
)

echo Opening the official Python download page.
echo Download and install Python 3.11, then run ..\run_windows.bat
start "" "https://www.python.org/downloads/"
pause
