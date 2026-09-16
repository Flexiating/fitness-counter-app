@echo off
setlocal
cd /d "%~dp0"
py -3.11 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.11"
    set "VENV_DIR=.venv-3.11"
    goto python_found
)
py -3.10 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.10"
    set "VENV_DIR=.venv-3.10"
    goto python_found
)
echo Python 3.10 or 3.11 is required.
exit /b 1

:python_found
if not exist "%VENV_DIR%\Scripts\python.exe" %PYTHON_CMD% -m venv "%VENV_DIR%"
call "%VENV_DIR%\Scripts\activate.bat"
python -m pip install -r requirements.txt
python scripts\build_windows.py --skip-install
