# Getting Started - Windows

A quick guide to set up secure secrets management in your project on Windows.

## 🚀 Quick Setup (5 minutes)

### Prerequisites

**Python 3.6+ Required:**
- **Microsoft Store (Recommended):** Search "Python" in Microsoft Store
- **Official Installer:** https://www.python.org/downloads/windows/
- **Chocolatey:** `choco install python`
- **Anaconda:** https://www.anaconda.com/products/distribution

**For PHP Projects (Optional):**
- **XAMPP (Easiest):** https://www.apachefriends.org/download.html
- **Official PHP:** https://windows.php.net/download/
- **Laravel Valet for Windows:** https://github.com/cretueusebiu/valet-windows

### 1. Add to Your Project

Copy these files to your project root:

**Using PowerShell (Recommended):**
```powershell
# Download the essential files
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/zwettemaan/secretDmg/main/secrets_manager.py" -OutFile "secrets_manager.py"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/zwettemaan/secretDmg/main/secrets_manager.bat" -OutFile "secrets_manager.bat"

# For PHP projects, also download:
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/zwettemaan/secretDmg/main/SecretsManagerLib.php" -OutFile "SecretsManagerLib.php"
```

**Using Command Prompt with curl:**
```cmd
curl -O https://raw.githubusercontent.com/zwettemaan/secretDmg/main/secrets_manager.py
curl -O https://raw.githubusercontent.com/zwettemaan/secretDmg/main/secrets_manager.bat

REM For PHP projects:
curl -O https://raw.githubusercontent.com/zwettemaan/secretDmg/main/SecretsManagerLib.php
```

### 2. Create Your First Secrets Store

```cmd
REM Create empty secrets store
secrets_manager.bat create

REM Add your secret files
echo API_KEY=your_api_key_here > secrets\.env
echo DATABASE_URL=postgres://user:pass@host/db > secrets\database.conf

REM For JWT secret, you can use:
REM echo JWT_SECRET=your_random_secret_here > secrets\jwt.key

REM Encrypt and clean up
secrets_manager.bat unmount

REM Commit the encrypted file (safe!)
git add .myproject.secrets .gitignore
git commit -m "Add encrypted secrets"
```

## 🔄 Daily Workflow

### Working with Secrets
```cmd
REM Start working (decrypt secrets)
secrets_manager.bat mount

REM Edit your secret files
notepad secrets\.env
REM or: code secrets\.env  (VS Code)

REM Finish working (encrypt & cleanup)
secrets_manager.bat unmount

REM Commit any changes
git add .myproject.secrets
git commit -m "Update API keys"
```

### Quick Status Check
```cmd
secrets_manager.bat status    REM See if secrets are mounted
secrets_manager.bat list      REM See what secret files exist
```

## 👥 Team Scenarios

### Scenario 1: New Team Member Joining

**New team member runs:**
```cmd
REM 1. Clone the project
git clone <your-repo>
cd <project>

REM 2. Set up secrets access (one-time setup)
secrets_manager.bat mount
REM Enter shared password: [team_password]
REM Store in Windows Credential Manager? y

REM 3. Start working immediately
type secrets\.env  REM Your secrets are now accessible
```

### Scenario 2: Onboarding a Team Member

**Team lead shares:**
1. The repository URL
2. The shared password (via secure channel like 1Password, Bitwarden)

**That's it!** The new team member can immediately access all project secrets.

### Scenario 3: Rotating Shared Password

**Team lead runs:**
```cmd
secrets_manager.bat change-password
REM Old password: [current_password]
REM New password: [new_password]
```

**Team members update their stored password:**
```cmd
secrets_manager.bat clear     REM Clear old password from Credential Manager
secrets_manager.bat pass      REM Store new password
```

## 🌐 PHP Web Development

### Setup for PHP Projects
```cmd
REM 1. Copy the PHP library to your web app
copy SecretsManagerLib.php C:\xampp\htdocs\your-app\

REM 2. Use in your PHP code:
```

```php
<?php
require_once 'SecretsManagerLib.php';

$secrets = new SecretsManager();

// Read specific secret files (no mount/unmount needed!)
$envVars = $secrets->readEnvFile('.env');
$dbConfig = $secrets->readSecrets('database.conf');

echo $envVars['API_KEY'];     // Direct access to your API key
?>
```

### Production Deployment
```cmd
REM Set password on production server (one-time)
echo your_shared_password | python secrets_manager.py pass

REM Your PHP app can now access secrets without mounting
```

## 🛠️ Common Use Cases

### Environment Variables
```cmd
REM Create .env file
secrets_manager.bat mount
(
echo APP_ENV=production
echo API_KEY=sk-1234567890
echo DATABASE_URL=postgres://...
) > secrets\.env
secrets_manager.bat unmount
```

### SSL Certificates
```cmd
secrets_manager.bat mount
copy C:\ssl\server.crt secrets\
copy C:\ssl\server.key secrets\
secrets_manager.bat unmount
```

### Configuration Files
```cmd
secrets_manager.bat mount
(
echo [database]
echo host=db.example.com
echo username=app_user
echo password=super_secret
echo.
echo [api]
echo key=your_api_key
echo secret=your_api_secret
) > secrets\app.conf
secrets_manager.bat unmount
```

### PowerShell Integration
```powershell
# Mount secrets in PowerShell
& .\secrets_manager.bat mount

# Access secrets programmatically
$envContent = Get-Content "secrets\.env"
$apiKey = ($envContent | Select-String "API_KEY=").ToString().Split("=")[1]

# Unmount when done
& .\secrets_manager.bat unmount
```

## 🔐 Security Best Practices

- **Never commit the `secrets\` folder** (auto-ignored by the tool)
- **Do commit the `.myproject.secrets` file** (encrypted, safe)
- **Share passwords securely** (1Password, Bitwarden, or encrypted communication)
- **Rotate passwords periodically** using `change-password`
- **Use `secrets_manager.bat destroy`** when decommissioning projects

## 🪟 Windows-Specific Notes

### Credential Storage
- Uses Windows Credential Manager automatically
- No additional setup required
- Passwords stored securely per-user

### Python Installation
The tool works with any Python installation:
- **Microsoft Store Python (Recommended)** - Easiest installation and updates
- **Python.org installer** - Most compatibility with packages
- **Anaconda/Miniconda** - Great for data science projects
- **Chocolatey** - Good for automated setups

**Quick Python Check:**
```cmd
python --version
REM or:
python3 --version
REM or:
py --version
```

**Don't have Python?** Download from:
- Microsoft Store: Search "Python 3.11" or "Python 3.12"
- Official site: https://www.python.org/downloads/windows/
- Chocolatey: `choco install python` (requires Chocolatey)

### PHP Setup (For Web Projects)
If you need PHP for web development:
- **XAMPP** (recommended): https://www.apachefriends.org/download.html
- **Laravel Herd** (modern): https://herd.laravel.com/windows  
- **Official PHP**: https://windows.php.net/download/

### File Paths
The tool handles Windows paths automatically:
- Uses backslashes (`\`) for paths
- Works with drive letters (C:, D:, etc.)
- Handles spaces in folder names

### PowerShell vs Command Prompt
Both work perfectly:
```cmd
REM Command Prompt
secrets_manager.bat mount
```

```powershell
# PowerShell
.\secrets_manager.bat mount
```

## 🚨 Emergency Procedures

### Lost Password
```cmd
REM If you lose the password and have no backup:
del .myproject.secrets .secrets_keychain_entry
secrets_manager.bat create
REM Re-add all your secrets manually
```

### Security Breach
```cmd
REM 1. Change password immediately
secrets_manager.bat change-password

REM 2. Update all secret values
secrets_manager.bat mount
REM Update all files in secrets\
secrets_manager.bat unmount

REM 3. Notify team to update their passwords
```

## ✅ Verify Setup

```cmd
REM Download and run the test suite
curl -O https://raw.githubusercontent.com/zwettemaan/secretDmg/main/test_secrets_manager.py
python test_secrets_manager.py

REM Alternative with PowerShell:
REM Invoke-WebRequest -Uri "https://raw.githubusercontent.com/zwettemaan/secretDmg/main/test_secrets_manager.py" -OutFile "test_secrets_manager.py"
```

## 💡 Tips

- Use `secrets_manager.bat` (batch script) for auto-detection of Python
- Password is stored in Windows Credential Manager automatically
- The tool works with any file types (text, binary, certificates, etc.)
- For CI/CD: set password with `echo password | python secrets_manager.py pass`
- Perfect for IIS deployments and Windows servers
- Works great with WSL (Windows Subsystem for Linux) too

## 🖥️ Development Environment Integration

### Visual Studio Code
```json
// In .vscode/tasks.json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Mount Secrets",
            "type": "shell",
            "command": "secrets_manager.bat",
            "args": ["mount"],
            "group": "build"
        },
        {
            "label": "Unmount Secrets", 
            "type": "shell",
            "command": "secrets_manager.bat",
            "args": ["unmount"],
            "group": "build"
        }
    ]
}
```

### Visual Studio
Add as external tools or pre-build events:
```cmd
secrets_manager.bat mount
```
