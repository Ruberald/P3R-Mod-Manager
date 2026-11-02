@echo off
cd /d "%~dp0"
py -3 mod_manager.py
if errorlevel 1 pause
