@echo off
setlocal

py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    echo Python 3.12 is already installed.
    echo You can now run ..\run_windows.bat
    pause
    exit /b 0
)

echo Fitness Counter needs Python 3.12 to run from source code.
echo.
where winget >nul 2>&1
if not errorlevel 1 (
    echo Installing Python 3.12 with Windows Package Manager...
    winget install --id Python.Python.3.12 -e --source winget
    if not errorlevel 1 (
        echo.
        echo Python 3.12 was installed. Close and reopen Command Prompt, then run ..\run_windows.bat
        pause
        exit /b 0
    )
)

echo Opening the official Python download page.
echo Download and install Python 3.12, then run ..\run_windows.bat
start "" "https://www.python.org/downloads/"
pause
