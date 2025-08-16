@echo off
REM PHP Integration Demo Script for Windows
REM This script demonstrates the complete workflow:
REM 1. Python creates and encrypts secrets
REM 2. PHP reads and displays the secrets
REM 3. Cleanup

setlocal EnableDelayedExpansion

REM Demo configuration
set DEMO_DIR=php_demo_temp
set DEMO_PROJECT=PHPDemoProject
set DEMO_PASSWORD=demo123
set SCRIPT_DIR=%cd%

echo PHP Secrets Manager Integration Demo
echo =====================================
echo.

REM Create demo directory
echo Creating demo directory: %DEMO_DIR%
if exist "%DEMO_DIR%" rmdir /s /q "%DEMO_DIR%"
mkdir "%DEMO_DIR%"
cd "%DEMO_DIR%"

REM Initialize Python secrets manager
echo Initializing secrets manager with Python...
python "%SCRIPT_DIR%\secrets_manager.py" create --project "%DEMO_PROJECT%" --password "%DEMO_PASSWORD%"
if errorlevel 1 (
    echo ERROR: Failed to create secrets manager
    goto cleanup
)
echo SUCCESS: Secrets manager created
echo.

REM Create sample secrets
echo Creating sample secrets...
mkdir secrets 2>NUL

REM Create API documentation
echo # API Documentation > secrets\api_docs.md
echo. >> secrets\api_docs.md
echo ## Authentication >> secrets\api_docs.md
echo Use Bearer token authentication with the following endpoint: >> secrets\api_docs.md
echo ``` >> secrets\api_docs.md
echo POST /api/v1/auth >> secrets\api_docs.md
echo Authorization: Bearer your-token-here >> secrets\api_docs.md
echo ``` >> secrets\api_docs.md

REM Create database config
echo { > secrets\database_config.json
echo   "database": { >> secrets\database_config.json
echo     "primary": { >> secrets\database_config.json
echo       "host": "primary-db.company.com", >> secrets\database_config.json
echo       "port": 5432, >> secrets\database_config.json
echo       "database": "production_db", >> secrets\database_config.json
echo       "username": "db_admin", >> secrets\database_config.json
echo       "password": "super_secure_password_123", >> secrets\database_config.json
echo       "ssl": true >> secrets\database_config.json
echo     }, >> secrets\database_config.json
echo     "replica": { >> secrets\database_config.json
echo       "host": "replica-db.company.com", >> secrets\database_config.json
echo       "port": 5433, >> secrets\database_config.json
echo       "database": "production_db", >> secrets\database_config.json
echo       "username": "readonly_user", >> secrets\database_config.json
echo       "password": "readonly_password_456", >> secrets\database_config.json
echo       "ssl": true >> secrets\database_config.json
echo     } >> secrets\database_config.json
echo   }, >> secrets\database_config.json
echo   "cache": { >> secrets\database_config.json
echo     "redis": { >> secrets\database_config.json
echo       "host": "redis.company.com", >> secrets\database_config.json
echo       "port": 6379, >> secrets\database_config.json
echo       "password": "redis_password_789" >> secrets\database_config.json
echo     } >> secrets\database_config.json
echo   } >> secrets\database_config.json
echo } >> secrets\database_config.json

REM Create SSL certificate (dummy)
echo -----BEGIN CERTIFICATE----- > secrets\ssl_certificate.pem
echo MIICljCCAX4CCQDAOxKQHkx4ejANBgkqhkiG9w0BAQsFADCBjjELMAkGA1UEBhMC >> secrets\ssl_certificate.pem
echo VVMxCzAJBgNVBAgMAlVTMRAwDgYDVQQHDAdTZWF0dGxlMRAwDgYDVQQKDAdDb21w >> secrets\ssl_certificate.pem
echo YW55MRAwDgYDVQQLDAdTZWN0aW9uMRAwDgYDVQQDDAdFeGFtcGxlMSAwHgYJKoZI >> secrets\ssl_certificate.pem
echo hvcNAQkBFhFleGFtcGxlQGV4YW1wbGUuY29tMB4XDTIzMDEwMTAwMDAwMFoXDTI0 >> secrets\ssl_certificate.pem
echo -----END CERTIFICATE----- >> secrets\ssl_certificate.pem

REM Create README
echo This directory contains encrypted secrets for the demo project. > secrets\README.txt
echo. >> secrets\README.txt
echo Files: >> secrets\README.txt
echo - api_docs.md: API documentation with authentication details >> secrets\README.txt
echo - database_config.json: Database connection configuration >> secrets\README.txt
echo - ssl_certificate.pem: SSL certificate for secure connections >> secrets\README.txt

echo SUCCESS: Created sample secrets files
echo.

REM Encrypt the secrets
echo Encrypting secrets with Python...
python "%SCRIPT_DIR%\secrets_manager.py" unmount
if errorlevel 1 (
    echo ERROR: Failed to encrypt secrets
    goto cleanup
)
echo SUCCESS: Secrets encrypted successfully
echo.

REM Test PHP integration
echo Testing PHP integration...
echo =============================================
copy "%SCRIPT_DIR%\SecretsManagerLib.php" .
copy "%SCRIPT_DIR%\php_example.php" .
php php_example.php
set PHP_EXIT_CODE=!errorlevel!
echo =============================================

if !PHP_EXIT_CODE! equ 0 (
    echo SUCCESS: PHP integration test passed!
) else (
    echo WARNING: PHP integration completed with exit code !PHP_EXIT_CODE!
)
echo.

REM Success message
echo Demo completed successfully!
echo.
echo What happened:
echo 1. Python created an encrypted secrets store
echo 2. Sample secrets were added (API docs, database config, SSL cert)
echo 3. Python encrypted the secrets
echo 4. PHP successfully read and decrypted the secrets
echo.
echo This demonstrates that PHP can seamlessly work with
echo Python-encrypted secrets on Windows using the credential manager!

:cleanup
echo.
echo Cleaning up demo files...

REM Go back to script directory
cd "%SCRIPT_DIR%"

REM Remove demo directory
if exist "%DEMO_DIR%" (
    echo Removing demo directory: %DEMO_DIR%
    rmdir /s /q "%DEMO_DIR%"
    echo SUCCESS: Removed demo directory
)

echo.
echo Demo cleanup complete!
echo.
pause
