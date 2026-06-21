@echo off
cd /d "%~dp0"
set HF_HUB_DISABLE_SYMLINKS_WARNING=1
set PATH=%~dp0venv\Lib\site-packages\nvidia\cublas\bin;%~dp0venv\Lib\site-packages\nvidia\cudnn\bin;%PATH%
venv\Scripts\python.exe run.py
pause
