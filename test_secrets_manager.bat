@echo off
REM Test runner wrapper script for test_secrets_manager.py (Windows)
REM Automatically detects Python executable and provides helpful error messages

setlocal EnableDelayedExpansion

REM Jump to main logic, skip function definitions
goto :main

REM Function to check if command exists
REM Usage: call :command_exists python
REM Returns: sets FOUND_CMD to 1 if found, 0 if not found
:command_exists
where "%1" >nul 2>&1
if %ERRORLEVEL%==0 (
    set "FOUND_CMD=1"
) else (
    set "FOUND_CMD=0"
)
exit /b 0

REM Function to check Python version compatibility  
REM Usage: call :check_python_version python
REM Returns: sets VERSION_FOUND and VERSION_COMPATIBLE
:check_python_version
set "cmd=%1"
set "version_output="
set "version="
set "major="
set "minor="

REM Try to get version output
"%cmd%" --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    set "VERSION_FOUND="
    set "VERSION_COMPATIBLE=0"
    exit /b 0
)

for /f "tokens=*" %%v in ('"%cmd%" --version 2^>^&1') do set "version_output=%%v"

REM Extract version number from output (format: Python 3.11.3)
for /f "tokens=2" %%v in ("!version_output!") do set "version=%%v"

REM If we couldn't parse version, mark as incompatible
if "!version!"=="" (
    set "VERSION_FOUND="
    set "VERSION_COMPATIBLE=0"
    exit /b 0
)

REM Parse major and minor version numbers
for /f "tokens=1,2 delims=." %%a in ("!version!") do (
    set "major=%%a"
    set "minor=%%b"
)

REM If we couldn't parse major/minor, mark as incompatible
if "!major!"=="" (
    set "VERSION_FOUND=!version!"
    set "VERSION_COMPATIBLE=0"
    exit /b 0
)

REM Check if version is compatible (3.6+)
if !major! GTR 3 (
    set "VERSION_FOUND=!version!"
    set "VERSION_COMPATIBLE=1"
) else if !major!==3 (
    if "!minor!"=="" (
        set "VERSION_FOUND=!version!"
        set "VERSION_COMPATIBLE=0"
    ) else if !minor! GEQ 6 (
        set "VERSION_FOUND=!version!"
        set "VERSION_COMPATIBLE=1"
    ) else (
        set "VERSION_FOUND=!version!"
        set "VERSION_COMPATIBLE=0"
    )
) else (
    set "VERSION_FOUND=!version!"
    set "VERSION_COMPATIBLE=0"
)
exit /b 0

:main
REM Main script logic starts here

REM Check for help flags first
if "%1"=="--help" goto :show_help
if "%1"=="-h" goto :show_help
if "%1"=="/?" goto :show_help

REM Function to check if a command exists
call :command_exists python
if !FOUND_CMD!==1 (
    call :check_python_version python
    if !VERSION_COMPATIBLE!==1 (
        set "PYTHON_CMD=python"
        goto :run_tests
    )
)

call :command_exists python3
if !FOUND_CMD!==1 (
    call :check_python_version python3
    if !VERSION_COMPATIBLE!==1 (
        set "PYTHON_CMD=python3"
        goto :run_tests
    )
)

REM Try other common Python installations
for %%p in (py python3.12 python3.11 python3.10 python3.9 python3.8 python3.7 python3.6) do (
    call :command_exists %%p
    if !FOUND_CMD!==1 (
        call :check_python_version %%p
        if !VERSION_COMPATIBLE!==1 (
            set "PYTHON_CMD=%%p"
            goto :run_tests
        )
    )
)

REM No compatible Python found
echo.
echo [ERROR] No compatible Python installation found!
echo Please install Python 3.6+ and try again.
echo See: https://www.python.org/downloads/
echo.
exit /b 1

:run_tests
REM Check if test_secrets_manager.py exists
if not exist "%~dp0test_secrets_manager.py" (
    echo [ERROR] test_secrets_manager.py not found in %~dp0
    echo Please ensure test_secrets_manager.py is in the same directory as this script.
    exit /b 1
)

REM Show success message
for /f "tokens=*" %%i in ('!PYTHON_CMD! --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Using !PYTHON_CMD! (!PYTHON_VERSION!)
echo [INFO] Running comprehensive test suite...
echo.

REM Execute test_secrets_manager.py with all arguments
!PYTHON_CMD! "%~dp0test_secrets_manager.py" %*
exit /b %ERRORLEVEL%

:show_help
echo Secrets Manager Test Runner - Windows Wrapper Script
echo.
echo This script automatically detects your Python installation and runs the test suite
echo.
echo Usage: %~nx0 [test options...]
echo.
echo Examples:
echo   %~nx0                           # Run all tests
echo   %~nx0 --verbose                 # Run tests with verbose output
echo   %~nx0 --help                    # Show this help
echo.
exit /b 0
