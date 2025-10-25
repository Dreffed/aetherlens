@echo off
REM Generate a secure SECRET_KEY for AetherLens (Windows)

setlocal enabledelayedexpansion

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or later
    exit /b 1
)

REM Run the Python script
python "%~dp0generate-secret-key.py" %*
