@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  call setup.bat
  if errorlevel 1 exit /b 1
)
if not exist .venv\requirements-installed-vachana-tts.txt (
  echo First run: preparing Python environment...
  call setup.bat
  if errorlevel 1 exit /b 1
)
.venv\Scripts\python.exe cira_receiver.py
pause
