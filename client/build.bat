@echo off
chcp 65001 >nul
setlocal

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"

echo === Data Share Client - Build EXE ===

REM venvがなければ作成
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment...
    py -m venv "%VENV_DIR%"
)

echo Installing dependencies...
"%VENV_DIR%\Scripts\pip" install -q -r "%SCRIPT_DIR%requirements.txt"

echo Building EXE...
"%VENV_DIR%\Scripts\pyinstaller" ^
    --onefile ^
    --windowed ^
    --name DataShare ^
    --icon NUL ^
    --add-data "%SCRIPT_DIR%config.json;." ^
    --hidden-import pystray._win32 ^
    --hidden-import winotify ^
    "%SCRIPT_DIR%data_share_client.py"

if exist "%SCRIPT_DIR%dist\DataShare.exe" (
    echo.
    echo Build complete: %SCRIPT_DIR%dist\DataShare.exe
) else (
    echo.
    echo Build FAILED
)
pause
