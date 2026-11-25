@echo off
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 goto needpython
py -3.12 --version >nul 2>&1
if errorlevel 1 goto needpython
if exist .venv\Scripts\python.exe goto install
py -3.12 -m venv .venv
if errorlevel 1 goto failed
:install
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto failed
if exist .venv\Lib\site-packages\torch rmdir /s /q .venv\Lib\site-packages\torch
if exist .venv\Lib\site-packages\transformers rmdir /s /q .venv\Lib\site-packages\transformers
if exist .venv\Lib\site-packages\safetensors rmdir /s /q .venv\Lib\site-packages\safetensors
if exist .venv\Lib\site-packages\torchvision rmdir /s /q .venv\Lib\site-packages\torchvision
if exist .venv\Lib\site-packages\torchaudio rmdir /s /q .venv\Lib\site-packages\torchaudio
echo local-vachana-tts>.venv\requirements-installed-vachana-tts.txt
echo Setup complete. Run run_receiver.bat next.
pause
exit /b 0
:needpython
echo Python 3.12 64-bit is required. Install it, then run setup.bat again.
echo Keep the Python Launcher (py) enabled during installation.
pause
exit /b 1
:failed
echo Setup failed. Check Python 3.12 64-bit and your internet connection, then retry.
pause
exit /b 1
