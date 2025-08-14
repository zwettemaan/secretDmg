@echo off
REM Test runner wrapper script for test_secrets_manager.py (Windows)
REM Automatically detects Python executable and provides helpful error messages

setlocal EnableDelayedExpansion

REM Function to check if a command exists
call :command_exists python python_found
if !python_found!==1 (
    call :check_python_version python python_version python_compatible
    if !python_compatible!==1 (
        set PYTHON_CMD=python
        goto :run_tests
    )
)

call :command_exists python3 python3_found
if !python3_found!==1 (
    call :check_python_version python3 python3_version python3_compatible
    if !python3_compatible!==1 (
        set PYTHON_CMD=python3
        goto :run_tests
    )
)

REM Try other common Python installations
for %%p in (py python3.12 python3.11 python3.10 python3.9 python3.8 python3.7 python3.6) do (
    call :command_exists %%p cmd_found
    if !cmd_found!==1 (
        call :check_python_version %%p version compatible
        if !compatible!==1 (
            set PYTHON_CMD=%%p
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

REM Function to check if command exists
:command_exists
where %1 >nul 2>&1
if %ERRORLEVEL%==0 (
    set %2=1
) else (
    set %2=0
)
exit /b 0

REM Function to check Python version compatibility
:check_python_version
set cmd=%1
for /f "tokens=2 delims= " %%v in ('%cmd% --version 2^>^&1') do set version=%%v
for /f "tokens=1,2 delims=." %%a in ("!version!") do (
    set major=%%a
    set minor=%%b
)

if !major! GTR 3 (
    set %3=!version!
    set %4=1
) else if !major!==3 (
    if !minor! GEQ 6 (
        set %3=!version!
        set %4=1
    ) else (
        set %3=!version!
        set %4=0
    )
) else (
    set %3=!version!
    set %4=0
)
exit /b 0

REM Help message
if "%1"=="--help" goto :show_help
if "%1"=="-h" goto :show_help
if "%1"=="/?" goto :show_help
goto :eof

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
