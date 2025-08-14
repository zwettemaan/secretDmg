@echo off
REM Cross-platform wrapper script for secrets_manager.py (Windows)
REM Automatically detects Python executable and provides helpful error messages

setlocal EnableDelayedExpansion

REM Debug mode - set to 1 to see debug output
set "DEBUG=0"

REM Function to check if a command exists
call :command_exists python python_found
if !DEBUG!==1 echo [DEBUG] python found: !python_found!
if !python_found!==1 (
    call :check_python_version python python_version python_compatible
    if !DEBUG!==1 echo [DEBUG] python version: !python_version!, compatible: !python_compatible!
    if !python_compatible!==1 (
        set "PYTHON_CMD=python"
        goto :run_script
    )
)

call :command_exists python3 python3_found
if !DEBUG!==1 echo [DEBUG] python3 found: !python3_found!
if !python3_found!==1 (
    call :check_python_version python3 python3_version python3_compatible
    if !DEBUG!==1 echo [DEBUG] python3 version: !python3_version!, compatible: !python3_compatible!
    if !python3_compatible!==1 (
        set "PYTHON_CMD=python3"
        goto :run_script
    )
)

REM Try other common Python installations
for %%p in (python3.12 python3.11 python3.10 python3.9 python3.8 python3.7 python3.6) do (
    call :command_exists %%p cmd_found
    if !DEBUG!==1 echo [DEBUG] %%p found: !cmd_found!
    if !cmd_found!==1 (
        call :check_python_version %%p version compatible
        if !DEBUG!==1 echo [DEBUG] %%p version: !version!, compatible: !compatible!
        if !compatible!==1 (
            set "PYTHON_CMD=%%p"
            goto :run_script
        )
    )
)

REM Try Windows Python Launcher last (can be unreliable)
call :command_exists py py_found
if !DEBUG!==1 echo [DEBUG] py launcher found: !py_found!
if !py_found!==1 (
    call :check_python_version py py_version py_compatible
    if !DEBUG!==1 echo [DEBUG] py launcher version: !py_version!, compatible: !py_compatible!
    if !py_compatible!==1 (
        set "PYTHON_CMD=py"
        goto :run_script
    )
)

REM No compatible Python found
goto :provide_installation_guidance

:run_script
REM Check if secrets_manager.py exists
if not exist "%~dp0secrets_manager.py" (
    echo [ERROR] secrets_manager.py not found in %~dp0
    echo Please ensure secrets_manager.py is in the same directory as this script.
    exit /b 1
)

REM Show success message
for /f "tokens=*" %%i in ('!PYTHON_CMD! --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Using !PYTHON_CMD! (!PYTHON_VERSION!)

REM Execute secrets_manager.py with all arguments
!PYTHON_CMD! "%~dp0secrets_manager.py" %*
exit /b %ERRORLEVEL%

:provide_installation_guidance
echo.
echo [ERROR] No compatible Python installation found!
echo.
echo The secrets manager requires Python 3.6 or later. Here's how to install it:
echo.
echo Windows Installation Options:
echo   1. Official installer (recommended):
echo      Download from https://www.python.org/downloads/
echo      Make sure to check 'Add Python to PATH' during installation
echo.
echo   2. Microsoft Store:
echo      Search for 'Python 3' in Microsoft Store
echo.
echo   3. Chocolatey:
echo      choco install python3
echo.
echo   4. Winget:
echo      winget install Python.Python.3
echo.
echo After installation, restart your command prompt and try running this script again.
echo.
exit /b 1

REM Function to check if command exists
:command_exists
where "%1" >nul 2>&1
if %ERRORLEVEL%==0 (
    set "%2=1"
) else (
    set "%2=0"
)
exit /b 0

REM Function to check Python version compatibility
:check_python_version
set "cmd=%1"
set "version_output="
set "version="
set "major="
set "minor="

REM Try to get version output
"%cmd%" --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    set "%3="
    set "%4=0"
    exit /b 0
)

for /f "tokens=*" %%v in ('"%cmd%" --version 2^>^&1') do set "version_output=%%v"

REM Extract version number from output (format: Python 3.11.3)
for /f "tokens=2" %%v in ("!version_output!") do set "version=%%v"

REM If we couldn't parse version, mark as incompatible
if "!version!"=="" (
    set "%3="
    set "%4=0"
    exit /b 0
)

REM Parse major and minor version numbers
for /f "tokens=1,2 delims=." %%a in ("!version!") do (
    set "major=%%a"
    set "minor=%%b"
)

REM If we couldn't parse major/minor, mark as incompatible
if "!major!"=="" (
    set "%3=!version!"
    set "%4=0"
    exit /b 0
)

REM Check if version is compatible (3.6+)
if !major! GTR 3 (
    set "%3=!version!"
    set "%4=1"
) else if !major!==3 (
    if "!minor!"=="" (
        set "%3=!version!"
        set "%4=0"
    ) else if !minor! GEQ 6 (
        set "%3=!version!"
        set "%4=1"
    ) else (
        set "%3=!version!"
        set "%4=0"
    )
) else (
    set "%3=!version!"
    set "%4=0"
)
exit /b 0

REM Help message
if "%1"=="--help" goto :show_help
if "%1"=="-h" goto :show_help
if "%1"=="/?" goto :show_help
goto :eof

:show_help
echo Secrets Manager - Windows Wrapper Script
echo.
echo This script automatically detects your Python installation and runs secrets_manager.py
echo.
echo Usage: %~nx0 [secrets_manager.py arguments...]
echo.
echo Examples:
echo   %~nx0 create                    # Create new secrets project
echo   %~nx0 mount                     # Decrypt secrets for editing
echo   %~nx0 unmount                   # Encrypt secrets for storage
echo   %~nx0 status                    # Show current status
echo   %~nx0 --help                    # Show this help
echo.
echo For secrets_manager.py help: %~nx0 --help-secrets
exit /b 0
