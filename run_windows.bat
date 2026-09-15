@echo off
setlocal
cd /d "%~dp0"

rem MediaPipe's classic Pose API used by this project supports Python 3.9–3.12.
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.12"
    set "VENV_DIR=.venv-3.12"
    goto python_found
)
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
py -3.9 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.9"
    set "VENV_DIR=.venv-3.9"
    goto python_found
)

echo Python 3.9-3.12 is required to run Fitness Counter.
echo Python 3.14 is not supported by the MediaPipe Pose API used by this version.
echo Install Python 3.12 from https://www.python.org/downloads/, then run this file again.
pause
exit /b 1

:python_found
if not exist "%VENV_DIR%\Scripts\python.exe" %PYTHON_CMD% -m venv "%VENV_DIR%"
call "%VENV_DIR%\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m app.main
