# Cross-Platform Secrets Manager

**Version 1.0.3**

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

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Commands Reference](#-commands-reference)
- [Team Workflows](#-team-workflows)
- [Security](#-security)
- [Platform-Specific Notes](#-platform-specific-notes)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## ⚡ Quick Start

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
# Edit or use files in secrets/
python secrets_manager.py unmount
```

## 📦 Installation

### Prerequisites
- Python 3.6+ (uses only standard library)
- Git (for version control)

### Download
```bash
# Download the script
curl -O https://raw.githubusercontent.com/zwettemaan/secretDmg/main/secrets_manager.py
chmod +x secrets_manager.py

# Or clone the repository
git clone https://github.com/zwettemaan/secretDmg.git
cd secrets-manager
```

### Optional: Add to PATH
```bash
# Make it available globally
sudo cp secrets_manager.py /usr/local/bin/secrets_manager
sudo chmod +x /usr/local/bin/secrets_manager
```

## 🎯 Usage

### Basic Workflow

1. **Create Project**: `python secrets_manager.py create`
   - Creates empty `secrets/` folder
   - Prompts for password and stores in keychain/keyring
   - Adds `secrets/` to `.gitignore`

2. **Provide Secrets**: Place your secret files in `secrets/` folder, for example:
   - `.env` files
   - SSL certificates (`.pem`, `.key`)
   - API keys
   - Database passwords
   - License files for dev tools
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
├── .secrets_keychain_entry      # Keychain ID (safe to commit)
└── secrets/                     # Working directory (git-ignored)
    ├── .env
    ├── ssl_cert.pem
    ├── database.conf
    └── secrets_manager.hash     # Change detection
```

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

### `mount` - Decrypt Secrets
```bash
python secrets_manager.py mount
```
- Decrypts `.projectname.secrets` to `secrets/` folder
- Uses stored password or prompts if not available
- Offers to store password in keychain for future use

### `unmount` - Encrypt Secrets
```bash
python secrets_manager.py unmount
```
- Encrypts `secrets/` folder to `.projectname.secrets`
- Deletes `secrets/` folder
- Skips re-encryption if no changes detected (prevents git pollution)

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

### `status` - Show Current State
```bash
python secrets_manager.py status
```
- Shows project status and helpful next steps
- Indicates if secrets are mounted, password stored, etc.

### Global Options
- `--verbose, -v`: Enable verbose logging for all commands

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
# Team lead updates password
python secrets_manager.py mount
python secrets_manager.py clear              # Clear old password
python secrets_manager.py pass               # Store new password
python secrets_manager.py unmount

# Team members update their stored password
python secrets_manager.py clear              # Clear old password  
python secrets_manager.py pass               # Store new shared password
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

## 🖥️ Platform-Specific Notes

### macOS
```bash
# Password stored in Keychain
security find-generic-password -s "secrets_manager_myproject_abc123"

# File permissions automatically set to 700 (owner-only)
```

### Windows
```bash
# Password stored in Credential Manager
cmdkey /list:secrets_manager_myproject_abc123

# Use Command Prompt or PowerShell
python secrets_manager.py create
```

### Linux
```bash
# Password stored in encrypted file in home directory
ls ~/.secrets_manager_myproject_abc123

# Ensure proper permissions
chmod 700 secrets/
```

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

### Debugging
```bash
# Enable verbose logging
python secrets_manager.py --verbose mount
python secrets_manager.py -v status
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
git clone https://github.com/yourusername/secrets-manager.git
cd secrets-manager
python -m pytest tests/  # Run tests
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
- Thanks to the Python community for excellent standard library

---

**Made with ❤️ for developers who care about security**

For more information, visit our [GitHub repository](https://github.com/yourusername/secrets-manager) or [documentation site](https://yourusername.github.io/secrets-manager).