@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set "PYTHONUTF8=1"
set "ISFT_MODE=--open"
if "%~1"=="--configure-sheets" set "ISFT_MODE=--configure-sheets"

where py >nul 2>&1
if not errorlevel 1 (
    py -3 -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
    if not errorlevel 1 (
        py -3 server.py %ISFT_MODE%
        goto :done
    )
)

where python >nul 2>&1
if not errorlevel 1 (
    python -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
    if not errorlevel 1 (
        python server.py %ISFT_MODE%
        goto :done
    )
)

echo Python 3.10 yoki yangiroq versiya kerak.
echo Pythonni ornating, song START_ISFT.bat faylini qayta oching.
pause
exit /b 1

:done
set "ISFT_EXIT=%ERRORLEVEL%"
if "%ISFT_MODE%"=="--configure-sheets" (
    pause
) else if not "%ISFT_EXIT%"=="0" (
    pause
)
exit /b %ISFT_EXIT%
