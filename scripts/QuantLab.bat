@echo off
REM Double-click launcher (Windows).
cd /d "%~dp0\.."
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
set QUANT_LAB_MODE=research
python -m quantlab.ui
