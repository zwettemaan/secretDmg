# Getting Started - Linux

A quick guide to set up secure secrets management in your project on Linux.

## 🚀 Quick Setup (5 minutes)

### 1. Add to Your Project

Copy these files to your project root:
```bash
# Download the essential files
wget https://raw.githubusercontent.com/zwettemaan/secretDmg/main/secrets_manager.py
wget https://raw.githubusercontent.com/zwettemaan/secretDmg/main/secrets_manager.sh
chmod +x secrets_manager.sh

# For PHP projects, also download:
wget https://raw.githubusercontent.com/zwettemaan/secretDmg/main/SecretsManagerLib.php

# Alternative with curl:
# curl -O https://raw.githubusercontent.com/zwettemaan/secretDmg/main/secrets_manager.py
# curl -O https://raw.githubusercontent.com/zwettemaan/secretDmg/main/secrets_manager.sh
```

### 2. Create Your First Secrets Store

```bash
# Create empty secrets store
./secrets_manager.sh create

# Add your secret files
echo "API_KEY=your_api_key_here" > secrets/.env
echo "DATABASE_URL=postgres://user:pass@host/db" > secrets/database.conf
echo "JWT_SECRET=$(openssl rand -base64 32)" > secrets/jwt.key

# Encrypt and clean up
./secrets_manager.sh unmount

# Commit the encrypted file (safe!)
git add .myproject.secrets .gitignore
git commit -m "Add encrypted secrets"
```

## 🔄 Daily Workflow

### Working with Secrets
```bash
# Start working (decrypt secrets)
./secrets_manager.sh mount

# Edit your secret files
nano secrets/.env
# or: vim secrets/.env
# or: code secrets/.env  (VS Code)

# Finish working (encrypt & cleanup)
./secrets_manager.sh unmount

# Commit any changes
git add .myproject.secrets
git commit -m "Update API keys"
```

### Quick Status Check
```bash
./secrets_manager.sh status    # See if secrets are mounted
./secrets_manager.sh list      # See what secret files exist
```

## 👥 Team Scenarios

### Scenario 1: New Team Member Joining

**New team member runs:**
```bash
# 1. Clone the project
git clone <your-repo>
cd <project>

# 2. Set up secrets access (one-time setup)
./secrets_manager.sh mount
# Enter shared password: [team_password]
# Store in credential store? y

# 3. Start working immediately
cat secrets/.env  # Your secrets are now accessible
```

### Scenario 2: Onboarding a Team Member

**Team lead shares:**
1. The repository URL
2. The shared password (via secure channel like Bitwarden, 1Password)

**That's it!** The new team member can immediately access all project secrets.

### Scenario 3: Rotating Shared Password

**Team lead runs:**
```bash
./secrets_manager.sh change-password
# Old password: [current_password]
# New password: [new_password]
```

**Team members update their stored password:**
```bash
./secrets_manager.sh clear     # Clear old password from credential store
./secrets_manager.sh pass      # Store new password
```

## 🌐 PHP Web Development

### Setup for PHP Projects
```bash
# 1. Copy the PHP library to your web app
cp SecretsManagerLib.php /var/www/html/your-app/

# 2. Use in your PHP code:
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
```bash
# Set password on production server (one-time)
echo "your_shared_password" | python3 secrets_manager.py pass

# Your PHP app can now access secrets without mounting
```

## 🛠️ Common Use Cases

### Environment Variables
```bash
# Create .env file
./secrets_manager.sh mount
echo "APP_ENV=production
API_KEY=sk-1234567890
DATABASE_URL=postgres://..." > secrets/.env
./secrets_manager.sh unmount
```

### SSL Certificates
```bash
./secrets_manager.sh mount
cp /etc/ssl/certs/server.crt secrets/
cp /etc/ssl/private/server.key secrets/
./secrets_manager.sh unmount
```

### Configuration Files
```bash
./secrets_manager.sh mount
cat > secrets/app.conf << EOF
[database]
host=db.example.com
username=app_user
password=super_secret

[api]
key=your_api_key
secret=your_api_secret
EOF
./secrets_manager.sh unmount
```

### Docker Integration
```bash
# In your Dockerfile or docker-compose.yml setup script:
echo "$SECRETS_PASSWORD" | python3 secrets_manager.py pass
python3 secrets_manager.py mount
# Now your container can access secrets/ folder
```

## 🔐 Security Best Practices

- **Never commit the `secrets/` folder** (auto-ignored by the tool)
- **Do commit the `.myproject.secrets` file** (encrypted, safe)
- **Share passwords securely** (Bitwarden, 1Password, or encrypted communication)
- **Rotate passwords periodically** using `change-password`
- **Use `./secrets_manager.sh destroy`** when decommissioning projects

## 🐧 Linux-Specific Notes

### Credential Storage
- Uses `libsecret` (GNOME Keyring) when available
- Falls back to encrypted file storage if no keyring available
- Works in headless/server environments

### Distribution-Specific Setup

**Ubuntu/Debian:**
```bash
# If you want keyring integration (optional):
sudo apt update
sudo apt install python3-secretstorage
```

**RHEL/CentOS/Fedora:**
```bash
# If you want keyring integration (optional):
sudo dnf install python3-secretstorage
# or: sudo yum install python3-secretstorage
```

**Arch Linux:**
```bash
# If you want keyring integration (optional):
sudo pacman -S python-secretstorage
```

### Headless Servers
The tool works perfectly on headless servers without GUI:
```bash
# Password is stored in encrypted file instead of keyring
./secrets_manager.sh mount
# Works without any desktop environment
```

## 🚨 Emergency Procedures

### Lost Password
```bash
# If you lose the password and have no backup:
rm .myproject.secrets .secrets_keychain_entry
./secrets_manager.sh create
# Re-add all your secrets manually
```

### Security Breach
```bash
# 1. Change password immediately
./secrets_manager.sh change-password

# 2. Update all secret values
./secrets_manager.sh mount
# Update all files in secrets/
./secrets_manager.sh unmount

# 3. Notify team to update their passwords
```

## ✅ Verify Setup

```bash
# Run the test suite to verify everything works
wget https://raw.githubusercontent.com/zwettemaan/secretDmg/main/test_secrets_manager.py
python3 test_secrets_manager.py
```

## 💡 Tips

- Use `./secrets_manager.sh` (shell script) for auto-detection of Python
- Password storage adapts to your Linux desktop environment
- The tool works with any file types (text, binary, certificates, etc.)
- For CI/CD: set password with `echo "password" | python3 secrets_manager.py pass`
- Perfect for Docker containers and deployment automation
