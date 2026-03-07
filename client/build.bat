@echo off
chcp 65001 >nul
setlocal

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"

echo === rapid_share - Build EXE ===

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
    --name RapidShare ^
    --icon "%SCRIPT_DIR%rapidshare.ico" ^
    --version-file "%SCRIPT_DIR%version_info.py" ^
    "%SCRIPT_DIR%data_share_client.py"

if exist "%SCRIPT_DIR%dist\RapidShare.exe" (
    echo.
    echo Build complete: %SCRIPT_DIR%dist\RapidShare.exe
) else (
    echo.
    echo Build FAILED
)
pause
