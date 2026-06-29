@echo off
:: ============================================================
::  build.bat  —  Build both GUI and CLI Windows binaries
::  Usage:
::    build.bat          — build both
::    build.bat gui      — build GUI only
::    build.bat cli      — build CLI only
:: ============================================================
setlocal EnableDelayedExpansion

set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=both"

:: ── Locate pyinstaller ───────────────────────────────────────
where pyinstaller >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYINST=pyinstaller"
) else (
    :: Fall back to running via python -m (works when Scripts/ not on PATH)
    python -m PyInstaller --version >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        set "PYINST=python -m PyInstaller"
    ) else (
        echo [ERROR] pyinstaller not found. Run:  pip install pyinstaller
        exit /b 1
    )
)

echo.
echo ============================================================
echo   windowsOS-coworker  ^|  PyInstaller build
echo ============================================================

:: ── GUI build ────────────────────────────────────────────────
if "%TARGET%"=="both" goto :build_gui
if "%TARGET%"=="gui"  goto :build_gui
goto :maybe_cli

:build_gui
echo.
echo [1/2] Building GUI binary  (dist\coworker-gui\coworker-gui.exe) ...
%PYINST% coworker-gui.spec --noconfirm --clean
if %ERRORLEVEL% neq 0 (
    echo [ERROR] GUI build failed.
    exit /b %ERRORLEVEL%
)
echo [OK] GUI build complete.

:maybe_cli
if "%TARGET%"=="gui" goto :done

:: ── CLI build ────────────────────────────────────────────────
:build_cli
echo.
echo [2/2] Building CLI binary  (dist\coworker-cli\coworker-cli.exe) ...
%PYINST% coworker-cli.spec --noconfirm --clean
if %ERRORLEVEL% neq 0 (
    echo [ERROR] CLI build failed.
    exit /b %ERRORLEVEL%
)
echo [OK] CLI build complete.

:done
echo.
echo ============================================================
echo  Build finished.
if exist "dist\coworker-gui\coworker-gui.exe" (
    echo  GUI : dist\coworker-gui\coworker-gui.exe
)
if exist "dist\coworker-cli\coworker-cli.exe" (
    echo  CLI : dist\coworker-cli\coworker-cli.exe
)
echo.
echo  NOTE: Copy your .env file into the dist\coworker-gui\ (or
echo        dist\coworker-cli\) folder before distributing, OR
echo        set OPENAI_API_KEY as a system environment variable
echo        on the target machine.
echo ============================================================
endlocal
