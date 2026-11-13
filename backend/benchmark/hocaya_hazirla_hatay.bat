@echo off
cd /d "%~dp0.."
venv\Scripts\python.exe benchmark\prepare_demo.py hatay
echo.
echo Bu pencereyi KAPATMA. Sunum bitene kadar acik birak.
pause
