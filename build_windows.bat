@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
pyinstaller --noconfirm --clean --windowed --name "Workout Tracker" --add-data "app;app" --collect-all mediapipe --collect-all cv2 app\main.py
echo Created: %CD%\dist\Workout Tracker\Workout Tracker.exe
