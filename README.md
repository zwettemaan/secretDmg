# Secrets DMG Manager - User Manual

## Overview

The Secrets DMG Manager is a bash script designed to securely manage code signing certificates, passwords, and other sensitive build artifacts for software development projects. It stores these secrets in an encrypted disk image (DMG) that can be safely version-controlled alongside your source code.

This script was built by Kris Coppieters (kris@rorohiko.com), with help from Claude Sonnet 4 

The user manual and script have been AI-generated, under guidance. I've proof-read most of the material but there might still
be errors and oversights. Use at your own risk. Any errors, oversights, and AI-create hallucinations you spot: let Kris know!

The manual is designed to serve both as a tutorial for new users and a reference for experienced users. It includes practical 
examples throughout and addresses the specific use cases we developed during our conversation, like cross-platform code signing, 
team distribution, and CI/CD integration.

The manual emphasizes the tool's main value propositions:

- Secure storage of sensitive build materials
- Consistent integration with build scripts
- Safe version control of encrypted secrets
- Team collaboration without compromising security

## Why This Tool Exists

### The Problem
Modern software development requires managing sensitive materials like:
- Code signing certificates (.pfx files for Windows, .p12 for macOS)
- Signing passwords and API keys
- License files for build tools
- Private keys and configuration files

These files present several challenges:
- **Security**: Cannot be stored in plain text in git repositories
- **Distribution**: Need to be shared securely across team members and build machines
- **Build Integration**: Must be accessible to automated build scripts
- **Cross-platform**: May need Windows certificates on macOS build machines
- **Consistency**: Build scripts need predictable file locations

### The Solution
This tool creates an encrypted DMG file containing your secrets that:
- ✅ Can be safely committed to git (encrypted)
- ✅ Mounts to a consistent, predictable location
- ✅ Integrates seamlessly with build scripts
- ✅ Uses macOS keychain for password management
- ✅ Minimizes git repository pollution
- ✅ Supports secure password transport between machines

## Core Features

- **Encrypted Storage**: AES-256 encrypted DMG files
- **Keychain Integration**: Passwords stored securely in macOS keychain
- **Stable Mount Points**: Consistent paths for build script integration
- **Project Isolation**: Different projects use different mount points
- **Password Management**: Export/import passwords for team sharing
- **Git-Friendly**: Minimal metadata changes to avoid unnecessary commits
- **Defensive Coding**: Robust error handling and logging

## Installation

1. Copy the `secrets_dmg_manager.sh` script to your project directory
2. Make it executable: `chmod +x secrets_dmg_manager.sh`
3. Optionally create a `secrets_template/` directory with default files

## Commands

### Basic Commands

#### `create`
Creates a new encrypted DMG file for storing secrets.
```bash
./secrets_dmg_manager.sh create
```
- Generates a random AES-256 encryption password
- Stores password in macOS keychain
- Creates encrypted DMG file named `secrets.dmg`
- Includes template files if `secrets_template/` directory exists

#### `mount`
Mounts the encrypted DMG to a stable location.
```bash
./secrets_dmg_manager.sh mount
```
- Retrieves password from keychain
- Mounts to `/tmp/secrets_<ProjectName>`
- Exports environment variables for build scripts
- Automatically unmounts any existing mounts first

#### `unmount`
Safely unmounts the DMG.
```bash
./secrets_dmg_manager.sh unmount
```
- Finds and unmounts only this project's DMG
- Cleans up temporary mount directories
- Safe to run multiple times

#### `status`
Shows current DMG and mount status.
```bash
./secrets_dmg_manager.sh status
```
- Displays DMG file size and modification date
- Shows current mount status and location
- Lists contents if mounted

#### `update`
Interactive update of DMG contents.
```bash
./secrets_dmg_manager.sh update
```
- Mounts DMG for editing
- Pauses for manual file modifications
- Recreates DMG with normalized timestamps
- Maintains backup during update process

### Password Management Commands

#### `export-password`
Exports the DMG password for transport to other machines.
```bash
./secrets_dmg_manager.sh export-password > password.txt
```
- Retrieves password from keychain
- Outputs to stdout for redirection to file
- Use for setting up the same DMG on multiple machines

#### `import-password`
Imports a DMG password into the keychain.
```bash
# From command line argument
./secrets_dmg_manager.sh import-password "your_password_here"

# From file
./secrets_dmg_manager.sh import-password $(cat password.txt)

# Interactive prompt (secure)
./secrets_dmg_manager.sh import-password
```
- Stores password in macOS keychain
- Overwrites any existing password
- Required before mounting DMG on new machines

#### `delete-password`
Removes the DMG password from keychain.
```bash
./secrets_dmg_manager.sh delete-password
```
- Useful for testing and cleanup
- Password must be re-imported before next mount

## Logging Levels

Control output verbosity with log levels (0-4):

- **0 = SILENT**: No output (for automated scripts)
- **1 = ERROR**: Show only errors
- **2 = WARN**: Show warnings and errors (default)
- **3 = INFO**: Show informational messages
- **4 = DEBUG**: Show detailed debugging information

Set via environment variable or command argument:
```bash
# Environment variable
LOG_LEVEL=1 ./secrets_dmg_manager.sh mount

# Command argument
./secrets_dmg_manager.sh mount 1
```

## Usage Workflows

### Initial Setup (First Time)

1. **Create the encrypted DMG:**
   ```bash
   ./secrets_dmg_manager.sh create
   ```

2. **Mount and populate with secrets:**
   ```bash
   ./secrets_dmg_manager.sh mount
   # Copy your certificates and keys to /tmp/secrets_YourProject/
   cp ~/Desktop/signing-cert.pfx /tmp/secrets_YourProject/
   ./secrets_dmg_manager.sh unmount
   ```

3. **Commit to git:**
   ```bash
   git add secrets.dmg secrets_dmg_manager.sh
   git commit -m "Add encrypted secrets storage"
   ```

### Team Distribution

When a team member needs access:

1. **Developer exports password:**
   ```bash
   ./secrets_dmg_manager.sh export-password > dmg_password.txt
   # Share dmg_password.txt securely (encrypted email, secure chat, etc.)
   ```

2. **Team member imports password:**
   ```bash
   git pull  # Get the secrets.dmg file
   ./secrets_dmg_manager.sh import-password $(cat dmg_password.txt)
   rm dmg_password.txt  # Clean up
   ```

3. **Test access:**
   ```bash
   ./secrets_dmg_manager.sh mount
   ls /tmp/secrets_YourProject/
   ./secrets_dmg_manager.sh unmount
   ```

### Build Script Integration

For automated builds that need access to secrets:

```bash
#!/bin/bash
# build.sh - Example build script

# Mount secrets with minimal logging
eval $(./secrets_dmg_manager.sh mount 1)

if [[ $? -eq 0 && -n "$SECRETS_PATH" ]]; then
    echo "Building with secrets from: $SECRETS_PATH"
    
    # Use secrets in build process
    codesign --sign "Developer ID" \
        --keychain "$SECRETS_PATH/signing.keychain" \
        MyApp.app
        
    # Windows code signing (cross-platform)
    osslsigncode sign \
        -pkcs12 "$SECRETS_PATH/windows-cert.pfx" \
        -pass "$(cat "$SECRETS_PATH/windows-pass.txt")" \
        -in MyApp.exe -out MyApp.exe
        
    echo "Build completed successfully"
    
    # Cleanup
    ./secrets_dmg_manager.sh unmount 1
else
    echo "ERROR: Failed to mount secrets DMG"
    exit 1
fi
```

### Updating Secrets

When you need to add or modify secrets:

```bash
./secrets_dmg_manager.sh update
# Script will mount DMG and pause
# Add/remove/modify files in the mounted location
# Press Enter when done
# Script automatically recreates DMG with changes
```

### Multi-Machine Development

For developers working on multiple machines:

1. **Export from primary machine:**
   ```bash
   ./secrets_dmg_manager.sh export-password > ~/secrets-password.txt
   # Copy both secrets.dmg and password file to other machine
   ```

2. **Import on secondary machine:**
   ```bash
   git pull  # Get latest secrets.dmg
   ./secrets_dmg_manager.sh import-password $(cat ~/secrets-password.txt)
   rm ~/secrets-password.txt
   ```

## File Structure

```
your_project/
├── secrets_dmg_manager.sh          # The management script
├── secrets.dmg                     # Encrypted secrets storage (committed to git)
├── secrets_template/               # Optional: default files for new DMGs
│   ├── README.txt
│   └── signing.env.template
└── build.sh                       # Your build scripts
```

When mounted, secrets are available at:
```
/tmp/secrets_YourProjectName/       # Stable mount point
├── windows-cert.pfx               # Your signing certificates
├── macos-cert.p12
├── signing-passwords.txt
└── license-keys.conf
```

## Security Considerations

### What's Protected
- **DMG Contents**: AES-256 encrypted, unreadable without password
- **Password Storage**: Secured in macOS keychain with optional Touch ID
- **Transport**: Passwords can be shared securely out-of-band

### What's Not Protected
- **DMG File Existence**: The encrypted file is visible in git
- **Mount Point**: When mounted, files are readable (but mount requires password)
- **Build Process**: Secrets are temporarily accessible during builds

### Best Practices
1. **Never commit unencrypted secrets** to git repositories
2. **Use secure channels** for password distribution (encrypted email, secure chat)
3. **Clean up password files** after import
4. **Regularly rotate** signing certificates and passwords
5. **Use Touch ID** keychain protection when available
6. **Monitor git commits** to ensure secrets.dmg changes are intentional

## Troubleshooting

### Common Issues

**"Resource busy" errors:**
```bash
# Force cleanup any stuck mounts
./secrets_dmg_manager.sh unmount 4  # Debug level to see what's happening
```

**"Password not found in keychain":**
```bash
# Re-import the password
./secrets_dmg_manager.sh import-password
```

**DMG appears corrupted:**
```bash
# Check DMG integrity
hdiutil verify secrets.dmg
```

**Build scripts can't find secrets:**
- Verify mount path: `/tmp/secrets_<ProjectName>`
- Check environment variables are exported: `echo $SECRETS_PATH`
- Ensure DMG is mounted: `./secrets_dmg_manager.sh status`

### Debug Mode

For detailed troubleshooting, use debug level logging:
```bash
./secrets_dmg_manager.sh mount 4
```

This shows:
- Keychain access attempts
- Mount/unmount operations
- File system operations
- Environment variable exports

## Advanced Usage

### Custom Mount Locations
The script uses `/tmp/secrets_<ProjectName>` by default. To customize, modify the `MOUNT_BASE` variable in the script.

### Different DMG Names
Change the `DMG_NAME` variable to use different names (useful for multiple secret sets per project).

### Template Files
Create a `secrets_template/` directory with default files that should be included in new DMGs:
```bash
mkdir secrets_template
echo "# Default signing configuration" > secrets_template/signing.conf
```

### CI/CD Integration
For automated builds, import the password once and then use silent operation:
```bash
# One-time setup on build machine
./secrets_dmg_manager.sh import-password "$SECRETS_PASSWORD"

# In build scripts
eval $(./secrets_dmg_manager.sh mount 0)  # Silent operation
# ... build process ...
./secrets_dmg_manager.sh unmount 0
```

## Support

This tool is designed to be self-contained and robust. For issues:

1. **Check logs** with debug level: `LOG_LEVEL=4`
2. **Verify keychain access** manually
3. **Test DMG integrity** with `hdiutil verify`
4. **Review file permissions** and paths

The script uses defensive coding practices and should provide clear error messages for most issues.
