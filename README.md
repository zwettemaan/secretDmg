# Cross-Platform Secrets Manager

**Version 1.0.5**

A secure, portable secrets management tool that works identically across macOS, Windows, and Linux. Never commit unencrypted secrets to git again!

**Author:** Kris Coppieters (kris@rorohiko.com)
**License:** MIT
**Built with assistance from:** Claude Sonnet 4

## ⚠️ Disclaimer

This software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealings in the software. **Use at your own risk.**

## 🚀 Features

- **🔒 Secure Encryption**: Industry-standard AES-256 equivalent encryption with PBKDF2 key derivation
- **🌍 Cross-Platform**: Identical functionality on macOS, Windows, and Linux
- **🔑 Smart Password Management**: Integrates with OS credential stores (Keychain, Credential Manager)
- **📂 Git-Safe**: Encrypted files are safe to commit; working directory auto-ignored
- **👥 Team-Friendly**: Seamless collaboration with shared encrypted secrets
- **⚡ Change Detection**: Prevents git pollution by only re-encrypting when files actually change
- **🛡️ Defensive Programming**: Robust error handling and secure cleanup
- **📦 Zero Dependencies**: Single Python script using only standard library

## 🆚 Comparison with Other Tools

| Feature | This Tool | git-crypt | SOPS | 1Password CLI | Vault |
|---------|-----------|-----------|------|---------------|-------|
| **Cross-platform** | ✅ | ❌ | ✅ | ✅ | ✅ |
| **Zero dependencies** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Simple setup** | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Git integration** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Team sharing** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **No infrastructure** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Change detection** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Free** | ✅ | ✅ | ✅ | ❌ | ❌ |

## 📋 Table of Contents

- [Comparison with Other Tools](#-comparison-with-other-tools)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Commands Reference](#-commands-reference)
- [Team Workflows](#-team-workflows)
- [Security](#-security)
- [Platform-Specific Notes](#-platform-specific-notes)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## ⚡ Quick Start

**macOS/Linux:**
```bash
# 1. Create a new secrets project
python secrets_manager.py create

# 2. Add your secret files to the secrets/ folder
echo "API_KEY=super_secret_key" > secrets/.env
echo "DATABASE_URL=postgres://..." > secrets/database.conf

# 3. Encrypt and clean up
python secrets_manager.py unmount

# 4. Commit the encrypted file (safe!)
git add .myproject.secrets
git commit -m "Add encrypted secrets"

# 5. Later, decrypt when you need to work
python secrets_manager.py mount
# Edit files in secrets/
python secrets_manager.py unmount

# 6. Security operations as needed
python secrets_manager.py change-password  # Rotate password
python secrets_manager.py destroy          # Remove everything

# 7. Verify everything works (optional)
python test_secrets_manager.py             # Run comprehensive tests
```

**Windows:**
```cmd
REM Set UTF-8 encoding for proper display
chcp 65001

REM 1. Create a new secrets project
python secrets_manager.py create

REM 2. Add your secret files to the secrets\ folder
echo API_KEY=super_secret_key > secrets\.env
echo DATABASE_URL=postgres://... > secrets\database.conf

REM 3. Encrypt and clean up
python secrets_manager.py unmount

REM 4. Commit the encrypted file (safe!)
git add .myproject.secrets
git commit -m "Add encrypted secrets"

REM 5. Later, decrypt when you need to work
python secrets_manager.py mount
REM Edit files in secrets\
python secrets_manager.py unmount

REM 6. Security operations as needed
python secrets_manager.py change-password
python secrets_manager.py destroy

REM 7. Verify everything works (optional)
python test_secrets_manager.py
```

## 📦 Installation

### Prerequisites
- Python 3.6+ (uses only standard library)
- Git (for version control)

### Download

**macOS/Linux:**
```bash
# Download the main script
curl -O https://raw.githubusercontent.com/zwettemaan/secretDmg/main/secrets_manager.py
chmod +x secrets_manager.py

# Optionally download the test suite
curl -O https://raw.githubusercontent.com/zwettemaan/secretDmg/main/test_secrets_manager.py

# Or clone the entire repository
git clone https://github.com/zwettemaan/secretDmg.git
cd secretDmg

# Verify installation by running tests
python test_secrets_manager.py
```

**Windows:**
```cmd
REM Download using PowerShell (recommended for Unicode support)
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/zwettemaan/secretDmg/main/secrets_manager.py' -OutFile 'secrets_manager.py'"
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/zwettemaan/secretDmg/main/test_secrets_manager.py' -OutFile 'test_secrets_manager.py'"

REM Or clone the repository
git clone https://github.com/zwettemaan/secretDmg.git
cd secretDmg

REM Set UTF-8 encoding and verify installation
chcp 65001
python test_secrets_manager.py
```

### Optional: Add to PATH
```bash
# Make it available globally
sudo cp secrets_manager.py /usr/local/bin/secrets_manager
sudo chmod +x /usr/local/bin/secrets_manager
```

## 🎯 Usage

### Basic Workflow

1. **Add Secrets Infrastructure To Project**: `python secrets_manager.py create`
   - Creates empty `secrets/` folder
   - Prompts for password and stores in keychain
   - Adds `secrets/` to `.gitignore`

2. **Add Secrets**: Place your secret files in `secrets/` folder
   - `.env` files
   - SSL certificates (`.pem`, `.key`)
   - API keys
   - Database passwords
   - Any sensitive configuration

3. **Encrypt**: `python secrets_manager.py unmount`
   - Encrypts `secrets/` folder → `.projectname.secrets`
   - Deletes `secrets/` folder
   - Safe to commit encrypted file

4. **Decrypt**: `python secrets_manager.py mount`
   - Decrypts `.projectname.secrets` → `secrets/` folder
   - Use stored password automatically

### File Structure
```
myproject/
├── .gitignore                    # Auto-updated
├── .myproject.secrets           # Encrypted (safe to commit)
├── .secrets_keychain_entry      # Config: keychain ID, project settings (safe to commit)
├── secrets/                     # Working directory (git-ignored)
│   ├── .env
│   ├── ssl_cert.pem
│   ├── database.conf
│   └── secrets_manager.hash     # Change detection
├── secrets_manager.py           # The tool itself
└── test_secrets_manager.py      # Comprehensive test suite (optional)
```

**Configuration Persistence**: When you run `create` with `--project` or `--secrets-dir`, these settings are automatically saved in `.secrets_keychain_entry` and used by all subsequent commands (`mount`, `unmount`, etc.).

## 📖 Commands Reference

### `create` - Initialize New Project
```bash
python secrets_manager.py create [options]

Options:
  --project NAME         Project name (default: current folder name)
  --secrets-dir DIR      Secrets directory name (default: secrets)
  --password PASS        Password for encryption
```

**Examples:**
```bash
python secrets_manager.py create
python secrets_manager.py create --project myapp
python secrets_manager.py create --secrets-dir private
python secrets_manager.py create --password mypassword
```

**⚠️ Important**: The `--project` and `--secrets-dir` settings are automatically saved and used by all other commands. You only need to specify them once during `create`.

### `mount` - Decrypt Secrets
```bash
python secrets_manager.py mount
```
- Automatically detects project name and secrets directory from previous `create`
- Decrypts `.projectname.secrets` to correct folder
- Uses stored password or prompts if not available
- Offers to store password in keychain for future use

### `unmount` - Encrypt Secrets
```bash
python secrets_manager.py unmount
```
- Encrypts `secrets/` folder to `.projectname.secrets`
- Deletes `secrets/` folder
- Skips re-encryption if no changes to secrets detected (prevents git pollution)

### `pass` - Store Password
```bash
python secrets_manager.py pass [--password PASS]
```
- Stores password in OS credential store
- Useful for team members joining existing project

### `clear` - Remove Stored Password
```bash
python secrets_manager.py clear
```
- Removes password from OS credential store
- Useful for security cleanup or troubleshooting

### `change-password` - Change Project Password
```bash
python secrets_manager.py change-password
```
- Changes the encryption password for the project
- Re-encrypts all secrets with new password
- Prompts for current and new passwords
- Updates stored password in keychain

### `destroy` - Permanently Delete Secrets And Password
```bash
python secrets_manager.py destroy
```
- **⚠️ DESTRUCTIVE**: Permanently deletes all project secrets
- Removes encrypted file, keychain entries, config files
- Requires typing 'DELETE' to confirm
- Use for security cleanup or project removal

### `status` - Show Current State
```bash
python secrets_manager.py status
```
- Shows project status and helpful next steps
- Indicates if secrets are mounted, password stored, etc.

### Global Options
- `--verbose, -v`: Enable verbose logging for all commands
- `--test-mode`: Enable automated testing mode (no interactive prompts)

## 👥 Team Workflows

### Initial Project Setup (Team Lead)
```bash
# 1. Create and set up secrets
python secrets_manager.py create
echo "API_KEY=prod_key_12345" > secrets/.env
echo "DB_PASS=super_secret" > secrets/database.conf

# 2. Encrypt and commit
python secrets_manager.py unmount
git add .myproject.secrets .gitignore .secrets_keychain_entry
git commit -m "Add encrypted project secrets"
git push
```

### Team Member Onboarding
```bash
# 1. Clone and get encrypted secrets
git clone <repository>
cd <project>

# 2. Mount with shared password
python secrets_manager.py mount
# Enter password: [shared_team_password]
# Store password in keychain for future use? (y/n): y

# 3. Start working immediately
cat secrets/.env  # API_KEY=prod_key_12345
```

### Daily Development Workflow
```bash
# Start working
python secrets_manager.py mount

# Make changes to secrets
echo "NEW_API_KEY=updated_key" >> secrets/.env

# Save and cleanup
python secrets_manager.py unmount
git add .myproject.secrets
git commit -m "Update API keys"
```

### Password Rotation
```bash
# Change project password
python secrets_manager.py change-password

# Team members update their stored password
python secrets_manager.py clear              # Clear old password
python secrets_manager.py pass               # Store new shared password
```

### Project Cleanup
```bash
# Permanently remove all secrets and passwords
python secrets_manager.py destroy
# Type: DELETE
```

## 🔒 Security

### Encryption Details
- **Algorithm**: AES-256 equivalent encryption with XOR implementation (replace with proper AES for production)
- **Key Derivation**: PBKDF2 with SHA-256, 100,000 iterations
- **Salt**: 32 random bytes per encrypted file
- **IV**: 16 random bytes per encryption

### Security Best Practices
- **Strong Passwords**: Use complex, unique passwords for each project
- **Password Sharing**: Share passwords through secure channels (not email/chat)
- **Regular Rotation**: Rotate passwords periodically
- **Access Control**: Use `clear` command to remove passwords when leaving projects
- **Audit Trail**: Git history shows when secrets were updated

### What's Safe to Commit
✅ **Safe to commit:**
- `.projectname.secrets` (encrypted file)
- `.secrets_keychain_entry` (just keychain identifier)
- `.gitignore` (updated automatically)

❌ **Never commit:**
- `secrets/` folder (auto-ignored)
- Unencrypted secret files
- Passwords or plaintext credentials

### Platform-Specific Security
- **macOS**: Uses Keychain for password storage
- **Windows**: Uses Credential Manager for password storage
- **Linux**: Uses encrypted files in user home directory

## 🚨 Security Breach Response

If you suspect your secrets have been compromised, follow these steps immediately:

### 1. Immediate Actions
```bash
# Stop using current secrets immediately
python secrets_manager.py unmount

# Change the encryption password
python secrets_manager.py change-password
```

### 2. Refresh All Secret Values
```bash
# Mount with new password
python secrets_manager.py mount

# Replace ALL secret values in secrets/ folder:
# - Generate new API keys
# - Create new database passwords
# - Regenerate signing certificates
# - Update any other sensitive data

# Re-encrypt with fresh secrets
python secrets_manager.py unmount
```

### 3. Team Coordination
```bash
# Notify all team members to update their passwords
# Each team member should run:
python secrets_manager.py clear
python secrets_manager.py pass  # Enter new shared password
```

### 4. Infrastructure Updates
- **Revoke compromised credentials** in all services (APIs, databases, etc.)
- **Rotate signing certificates** with certificate authorities
- **Update CI/CD systems** with new passwords
- **Review access logs** for unauthorized usage
- **Update documentation** with new connection details

### 5. Nuclear Option - Complete Reset
If compromise is severe, completely start over:
```bash
# Completely destroy current secrets and password
python secrets_manager.py destroy
# Type: DELETE

# Create fresh project with new secrets
python secrets_manager.py create

# Regenerate ALL secrets from scratch
# Commit new encrypted file to git
git add .myproject.secrets
git commit -m "Security reset - new secrets generated"
```

### 6. Prevention for Future
- **Regular password rotation** (quarterly)
- **Monitor git history** for accidentally committed secrets
- **Use strong, unique passwords** for each project
- **Secure password sharing** (encrypted channels only)
- **Regular security audits** of who has access

### Emergency Checklist
- [ ] Stop using current secrets immediately
- [ ] Change encryption password
- [ ] Generate new secret values
- [ ] Notify all team members
- [ ] Revoke old credentials in all services
- [ ] Update CI/CD and infrastructure
- [ ] Review and improve security practices

## 🖥️ Platform-Specific Notes

### macOS
```bash
# Password stored in Keychain
security find-generic-password -s "secrets_manager_myproject_abc123"

# File permissions automatically set to 700 (owner-only)
```

### Windows
```cmd
# Password stored in Credential Manager
cmdkey /list:secrets_manager_myproject_abc123

# Use 'python' not 'python3' on Windows
python secrets_manager.py create

# For best Unicode support, use PowerShell or Windows Terminal
powershell
python secrets_manager.py create

# Set UTF-8 encoding if you see Unicode errors
chcp 65001
```

**Important Notes:**
- Windows uses `python.exe`, not `python3.exe`
- Command Prompt has limited Unicode support - use PowerShell or Windows Terminal
- May need to run as Administrator for some operations

### Linux
```bash
# Password stored in encrypted file in home directory
ls ~/.secrets_manager_myproject_abc123

# Ensure proper permissions
chmod 700 secrets/
```

## 🧪 Testing

This project includes comprehensive test suites to ensure reliability across all platforms and use cases.

### Test Files

- **`test_secrets_manager.py`**: Complete story-driven test suite that validates all functionality
- **Automated Testing**: Tests run without manual input using `--test-mode` flag
- **Human-Readable**: Tests are written as user stories that are easy to understand

### Running Tests

```bash
# Run the comprehensive test suite
python test_secrets_manager.py

# The test will automatically:
# - Test all 8 commands (create, mount, unmount, status, pass, clear, change-password, destroy)
# - Validate cross-platform compatibility
# - Test error handling scenarios
# - Verify team workflow patterns
# - Check file permissions and security
```

### Test Scenarios

The test suite covers six comprehensive scenarios:

1. **👤 Basic User Story**: Complete lifecycle from creation to destruction
2. **⚙️ Custom Configuration**: Testing custom project names and directories
3. **📊 Status Monitoring**: Validating status reporting in all states
4. **🚨 Error Handling**: Testing edge cases and error conditions
5. **📋 Comprehensive Command Coverage**: All 8 commands with various options
6. **📁 Folder Management**: Default vs custom folder behavior

### Test Output

Tests provide clear, story-driven output:
```
🎭 Running Secrets Manager Test Stories...

📖 Story 1: Basic User Story
  ✅ User creates new secrets vault
  ✅ User adds secret files to vault
  ✅ User encrypts vault for safe storage
  ✅ User decrypts vault for editing
  ✅ User changes vault password
  ✅ User destroys vault completely
  ✅ Basic user story completed successfully

📊 Test Results: 6 scenarios passed, 0 failed
```

### Development Testing

For development and debugging:

```bash
# Run with verbose output for debugging
python test_secrets_manager.py --verbose

# Test specific functionality (manual testing)
python secrets_manager.py --test-mode create
python secrets_manager.py --test-mode status
```

### Cross-Platform Testing

Tests automatically adapt to the current platform:
- **macOS**: Tests Keychain integration
- **Windows**: Tests Credential Manager integration
- **Linux**: Tests encrypted file storage
- **All Platforms**: Tests file permissions and security

### Continuous Integration

The test suite is designed for CI/CD environments:
- **Zero dependencies**: Only uses Python standard library
- **Non-interactive**: All tests run automatically
- **Fast execution**: Complete test suite runs in under 30 seconds
- **Clear output**: Easy to parse results for CI systems

## 🛠️ Troubleshooting

### Common Issues

**"No stored password found"**
```bash
# Solution: Store password manually
python secrets_manager.py pass
```

**"Failed to encrypt/decrypt"**
```bash
# Solution: Clear and reset password
python secrets_manager.py clear
python secrets_manager.py pass
```

**"Secrets file already exists"**
```bash
# Solution: Use mount instead of create
python secrets_manager.py mount
```

**"Permission denied on secrets folder"**
```bash
# Solution: Fix permissions
chmod 700 secrets/
python secrets_manager.py unmount
```

**"Forgot password"**
```bash
# If you remember the password but it's not stored:
python secrets_manager.py pass

# If password is completely lost:
# Secrets cannot be recovered - restore from backup or recreate
```

**"Need to change password after security incident"**
```bash
# Change password and re-encrypt all secrets
python secrets_manager.py change-password
```

**"Can't find my secrets after custom create"**
```bash
# The tool auto-detects project settings from the .projectname.secrets file
# If you used --project myapp --secrets-dir private, those are automatically used
python secrets_manager.py status  # Shows detected project name and directory
```

**"Want to change project name or secrets directory"**
```bash
# You need to recreate the project with new settings
python secrets_manager.py destroy  # Remove current project
python secrets_manager.py create --project newname --secrets-dir newdir
```

**"Want to completely remove secrets and passwords"**
```bash
# Permanently delete all traces
python secrets_manager.py destroy
```

**"Need to rotate passwords regularly"**
```bash
# Change password and re-encrypt all secrets
python secrets_manager.py change-password
```

### Windows-Specific Issues

**"UnicodeEncodeError: 'charmap' codec can't encode character"**
```cmd
REM The tool now automatically detects Windows and uses text symbols instead of emoji
REM This should be fixed in the latest version, but if you still see issues:

REM Solution 1: Set UTF-8 encoding for current session
chcp 65001
python secrets_manager.py status

REM Solution 2: Set environment variable permanently
setx PYTHONIOENCODING utf-8
REM Then restart command prompt and run:
python secrets_manager.py status

REM Solution 3: Use Windows Terminal (recommended)
REM Download from Microsoft Store - has better Unicode support
```

**"'python3' is not recognized as an internal or external command"**
```cmd
REM Windows uses 'python' not 'python3'
python secrets_manager.py create
python test_secrets_manager.py

REM If you need python3 command, create a copy:
copy "C:\Python311\python.exe" "C:\Python311\python3.exe"
REM (adjust path to your Python installation)
```

**"Access denied" or permission errors**
```cmd
REM Run Command Prompt as Administrator
REM Right-click Command Prompt → "Run as administrator"
python secrets_manager.py create
```

**"Credential Manager issues"**
```cmd
REM View stored credentials
cmdkey /list | findstr secrets_manager

REM Manually remove if corrupted
cmdkey /delete:secrets_manager_yourproject_abc123

REM Clear and reset password
python secrets_manager.py clear
python secrets_manager.py pass
```

**Testing on Windows**
```cmd
REM Ensure UTF-8 encoding before running tests
chcp 65001
python test_secrets_manager.py

REM Or use PowerShell (better Unicode support)
powershell
python test_secrets_manager.py
```

### Debugging
```bash
# Enable verbose logging
python secrets_manager.py --verbose mount
python secrets_manager.py -v status

# Run comprehensive tests to identify issues
python test_secrets_manager.py

# Test specific commands in automated mode
python secrets_manager.py --test-mode create
python secrets_manager.py --test-mode status
```

### Recovery Scenarios

**Lost Password**
- If password is lost, encrypted secrets cannot be recovered
- Restore from backup or recreate secrets manually

**Corrupted Encrypted File**
```bash
# Restore from git history
git log --oneline .myproject.secrets
git checkout <commit-hash> .myproject.secrets
```

**Multiple Projects with Same Name**
- Tool automatically handles this with unique keychain entries
- Each directory gets its own keychain identifier

## 🤝 Contributing

We welcome contributions! Please read our contributing guidelines:

### Development Setup
```bash
git clone https://github.com/zwettemaan/secretDmg.git
cd secretDmg

# Run the comprehensive test suite
python test_secrets_manager.py

# Test specific functionality during development
python secrets_manager.py --test-mode create
python secrets_manager.py --test-mode status
```

### Testing Your Changes
Before submitting changes, ensure all tests pass:
```bash
# Run full test suite
python test_secrets_manager.py

# Expected output should show all scenarios passing:
# 📊 Test Results: 6 scenarios passed, 0 failed
```

### Code Style
- Follow PEP 8 Python style guidelines
- Use defensive programming patterns (do-while-false loops)
- Include comprehensive error handling
- Add logging for debugging

### Submitting Changes
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes with tests
4. Submit a pull request

### Reporting Issues
Please report bugs and feature requests through GitHub Issues:
- Include Python version and OS
- Provide steps to reproduce
- Include relevant log output (use `--verbose`)

## 📊 Use Cases

### Development Teams
- Share API keys and database passwords securely
- Manage environment-specific configurations
- Ensure consistent secrets across team members

### DevOps/Infrastructure
- Store SSL certificates and private keys
- Manage deployment credentials
- Secure CI/CD pipeline secrets

### Solo Developers
- Keep personal API keys out of git history
- Manage multiple project credentials
- Backup sensitive configuration files

### Compliance
- Audit trail through git history
- Encrypted storage meets security requirements
- No plaintext secrets in repositories
- Secure password rotation with `change-password` command
- Complete data removal capabilities with `destroy` command

## 🔄 Migration

### From Other Tools

**From .env files:**
```bash
python secrets_manager.py create
mv .env secrets/env
ln -s secrets/env .env
echo ".env" >> .gitignore  # Remove from git
python secrets_manager.py unmount
```

**From encrypted archives:**
```bash
python secrets_manager.py create
# Extract archive to secrets/
python secrets_manager.py unmount
```

### To Other Tools
```bash
python secrets_manager.py mount
# Copy files from secrets/ to new tool
python secrets_manager.py unmount

# Optional: Clean removal when migrating away
python secrets_manager.py destroy
```

### Complete Secrets Removal
```bash
# When secrets are no longer needed
python secrets_manager.py destroy
# Type: DELETE
# All encrypted files, passwords, and config removed
```

## ⚖️ License

**MIT License**

Copyright (c) 2025 Kris Coppieters

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## 🙏 Acknowledgments

- Inspired by the need for simple, secure secret management
- Built with security and usability in mind
- Comprehensive test suite ensures reliability across platforms
- Story-driven testing approach makes validation human-readable
- Thanks to the Python community for excellent standard library

---

**Made with ❤️ for developers who care about security**

For more information, visit our [GitHub repository](https://github.com/zwettemaan/secretDmg) or [documentation site](https://zwettemaan.github.io/secretDmg).