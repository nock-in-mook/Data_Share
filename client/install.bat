@echo off
chcp 65001 >nul
setlocal

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"
set "EXE_PATH=%SCRIPT_DIR%dist\RapidShare.exe"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "STARTMENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "PS_TEMP=%TEMP%\rapid_share_install.ps1"

echo === RapidShare Setup ===

REM Remove old VBS if exists
if exist "%STARTUP_DIR%\RapidShare.vbs" del "%STARTUP_DIR%\RapidShare.vbs"

REM EXE version
if exist "%EXE_PATH%" (
    echo Using pre-built EXE: %EXE_PATH%
    echo Creating shortcuts...

    > "%PS_TEMP%" (
        echo $ws = New-Object -ComObject WScript.Shell
        echo $s = $ws.CreateShortcut^('%STARTUP_DIR%\RapidShare.lnk'^)
        echo $s.TargetPath = '%EXE_PATH%'
        echo $s.WorkingDirectory = '%SCRIPT_DIR%dist'
        echo $s.Description = 'RapidShare'
        echo $s.Save^(^)
        echo $s2 = $ws.CreateShortcut^('%STARTMENU_DIR%\RapidShare.lnk'^)
        echo $s2.TargetPath = '%EXE_PATH%'
        echo $s2.WorkingDirectory = '%SCRIPT_DIR%dist'
        echo $s2.Description = 'RapidShare'
        echo $s2.Save^(^)
    )
    powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_TEMP%"
    del "%PS_TEMP%" 2>nul

    echo.
    echo Setup complete!
    echo   - Startup:    %STARTUP_DIR%\RapidShare.lnk
    echo   - Start Menu: %STARTMENU_DIR%\RapidShare.lnk
    echo.
    echo Starting...
    start "" "%EXE_PATH%"
    pause
    exit /b
)

REM venv fallback
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment...
    py -m venv "%VENV_DIR%"
)

echo Installing dependencies...
"%VENV_DIR%\Scripts\pip" install -q -r "%SCRIPT_DIR%requirements.txt"

echo Creating shortcuts...
> "%PS_TEMP%" (
    echo $ws = New-Object -ComObject WScript.Shell
    echo $s = $ws.CreateShortcut^('%STARTUP_DIR%\RapidShare.lnk'^)
    echo $s.TargetPath = '%VENV_DIR%\Scripts\pythonw.exe'
    echo $s.Arguments = '"%SCRIPT_DIR%data_share_client.py"'
    echo $s.WorkingDirectory = '%SCRIPT_DIR%'
    echo $s.Description = 'RapidShare'
    echo $s.Save^(^)
    echo $s2 = $ws.CreateShortcut^('%STARTMENU_DIR%\RapidShare.lnk'^)
    echo $s2.TargetPath = '%VENV_DIR%\Scripts\pythonw.exe'
    echo $s2.Arguments = '"%SCRIPT_DIR%data_share_client.py"'
    echo $s2.WorkingDirectory = '%SCRIPT_DIR%'
    echo $s2.Description = 'RapidShare'
    echo $s2.Save^(^)
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_TEMP%"
del "%PS_TEMP%" 2>nul

echo.
echo Setup complete!
echo   - Startup:    %STARTUP_DIR%\RapidShare.lnk
echo   - Start Menu: %STARTMENU_DIR%\RapidShare.lnk
echo.
echo Starting...
start "" "%VENV_DIR%\Scripts\pythonw.exe" "%SCRIPT_DIR%data_share_client.py"
pause
