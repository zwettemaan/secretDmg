#!/usr/bin/env python3
"""
Cross-Platform Secrets Manager
A secure, portable secrets management tool that works identically across macOS, Windows, and Linux.

SIMPLE WORKFLOW:
1. Run: python secrets_manager.py create
   - Creates empty 'secrets' folder (fails if .projectname.secrets already exists)
2. Add your secret files to 'secrets' folder
3. Run: python secrets_manager.py unmount
   - Encrypts 'secrets' folder → .projectname.secrets
   - Deletes 'secrets' folder
4. Run: python secrets_manager.py mount
   - Decrypts .projectname.secrets into 'secrets' folder

The 'secrets' folder is automatically added to .gitignore.
Only the encrypted .projectname.secrets file should be committed to git.

TEAM WORKFLOW:
1. One team member: create, add files, unmount, commit .projectname.secrets
2. Other team members: git pull, then python secrets_manager.py pass (enter shared password)
3. Then: python secrets_manager.py mount
4. Work in secrets/, unmount when done
5. Optional security: python secrets_manager.py clear (removes stored password)
"""

import os
import sys
import json
import hashlib
import base64
import shutil
import subprocess
import platform
import getpass
import argparse
import logging
from pathlib import Path
from typing import Dict, Optional, Any
import secrets as secure_random

class SecretsManager:
    """Cross-platform secrets manager with defensive programming patterns."""
    
    VERSION = "1.0.0"
    CHUNK_SIZE = 64 * 1024  # 64KB chunks for file operations
    HASH_FILE = "secrets_manager.hash"
    
    def __init__(self, project_name: str, secrets_dir: str = "secrets"):
        self.ret_val = False
        self.project_name = project_name
        self.secrets_dir = secrets_dir
        self.secrets_file = f".{project_name}.secrets"
        self.gitignore_file = ".gitignore"
        self.keychain_config_file = ".secrets_keychain_entry"
        self.logger = self._setup_logging()
        self.platform = platform.system().lower()
        
        # Create unique keychain entry name to prevent clashes
        self.keychain_entry_name = self._get_or_create_keychain_entry_name()
        
        self.logger.info(f"Initializing SecretsManager for project: {project_name}")
        self.logger.info(f"Using keychain entry: {self.keychain_entry_name}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup defensive logging system."""
        logger = logging.getLogger(f"secrets_manager_{self.project_name}")
        logger.setLevel(logging.WARNING)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _get_or_create_keychain_entry_name(self) -> str:
        """Get or create unique keychain entry name for this project directory."""
        ret_val = ""
        self.logger.info("ENTRY: _get_or_create_keychain_entry_name")
        
        do_once = True
        while do_once:
            do_once = False
            
            # Check if config file exists
            if os.path.exists(self.keychain_config_file):
                try:
                    with open(self.keychain_config_file, 'r') as f:
                        entry_name = f.read().strip()
                    
                    if entry_name:
                        ret_val = entry_name
                        self.logger.info(f"Found existing keychain entry: {entry_name}")
                        break
                except Exception as e:
                    self.logger.warning(f"Could not read keychain config: {e}")
            
            # Create new unique entry name
            try:
                # Create unique identifier based on project name + absolute path
                current_dir = os.path.abspath(os.getcwd())
                unique_string = f"{self.project_name}_{current_dir}"
                
                # Create hash for shorter, cleaner entry name
                hash_object = hashlib.sha256(unique_string.encode())
                hash_hex = hash_object.hexdigest()[:12]  # First 12 chars
                
                entry_name = f"secrets_manager_{self.project_name}_{hash_hex}"
                
                # Save to config file
                with open(self.keychain_config_file, 'w') as f:
                    f.write(entry_name)
                
                # Add to gitignore
                self._add_to_gitignore(self.keychain_config_file)
                
                ret_val = entry_name
                self.logger.info(f"Created new keychain entry: {entry_name}")
                
            except Exception as e:
                # Fallback to simple name if creation fails
                ret_val = f"secrets_manager_{self.project_name}"
                self.logger.warning(f"Could not create unique keychain entry, using fallback: {e}")
                break
        
        self.logger.info(f"EXIT: _get_or_create_keychain_entry_name, returning: {ret_val}")
        return ret_val
    
    def create_secrets(self, password: Optional[str] = None) -> bool:
        """Create new secrets project - only works if no .projectname.secrets exists."""
        ret_val = False
        self.logger.info("ENTRY: create_secrets")
        
        do_once = True
        while do_once:
            do_once = False
            
            # Check if encrypted file already exists
            if os.path.isfile(self.secrets_file):
                print(f"❌ {self.secrets_file} already exists!")
                print("💡 Use 'mount' to decrypt existing secrets, or delete the file first")
                break
            
            # Check if secrets folder already exists
            if os.path.exists(self.secrets_dir):
                print(f"✅ Found existing {self.secrets_dir}/ folder")
                response = input("Encrypt existing folder contents? (y/n): ").lower()
                if response != 'y' and response != 'yes':
                    print("❌ Cannot create - secrets folder exists but not encrypting")
                    break
                
                # Get password for encryption
                if not password:
                    password = getpass.getpass("Enter password to encrypt secrets: ")
                    if not password:
                        print("❌ Password required to encrypt secrets")
                        break
                
                # Encrypt existing folder
                if self.unmount_secrets():
                    print("✅ Successfully created encrypted secrets from existing folder")
                    ret_val = True
                break
            
            # Create new empty secrets folder
            try:
                print(f"📁 Creating empty {self.secrets_dir}/ folder...")
                os.makedirs(self.secrets_dir, exist_ok=True)
                self._secure_directory(self.secrets_dir)
                self._add_to_gitignore(f"{self.secrets_dir}/")
                
                # Get password for future use
                if not password:
                    password = getpass.getpass("Enter password for this project: ")
                    if not password:
                        print("❌ Password required for project setup")
                        shutil.rmtree(self.secrets_dir, ignore_errors=True)
                        break
                
                # Store password for future mount/unmount operations
                if self._store_password(password):
                    print("🔑 Password stored in keychain")
                else:
                    print("⚠️  Warning: Could not store password in keychain")
                
                # Create helpful README
                readme_path = os.path.join(self.secrets_dir, "README.txt")
                with open(readme_path, 'w') as f:
                    f.write(f"Put your secret files here:\n")
                    f.write("- .env files\n")
                    f.write("- SSL certificates (.pem, .key)\n") 
                    f.write("- API keys\n")
                    f.write("- Database passwords\n")
                    f.write("- Any other sensitive files\n\n")
                    f.write(f"When done, run: python secrets_manager.py unmount\n")
                
                print(f"✅ Created empty {self.secrets_dir}/ folder")
                print(f"✅ Added {self.secrets_dir}/ to .gitignore")
                print(f"💡 Add your secret files to {self.secrets_dir}/ then run:")
                print(f"   python secrets_manager.py unmount")
                ret_val = True
                
            except Exception as e:
                print(f"❌ Failed to create secrets folder: {e}")
                break
        
        self.logger.info(f"EXIT: create_secrets, returning: {ret_val}")
        return ret_val
    
    def clear_password(self) -> bool:
        """Remove stored password from keychain for this project."""
        ret_val = False
        self.logger.info("ENTRY: clear_password")
        
        do_once = True
        while do_once:
            do_once = False
            
            # Check if password is stored
            if not self._has_stored_password():
                print(f"ℹ️  No password stored for project '{self.project_name}'")
                ret_val = True
                break
            
            try:
                service_name = self.keychain_entry_name
                
                if self.platform == "darwin":  # macOS
                    subprocess.run([
                        "security", "delete-generic-password",
                        "-s", service_name,
                        "-a", getpass.getuser()
                    ], check=True, capture_output=True)
                    
                elif self.platform == "windows":
                    subprocess.run([
                        "cmdkey", "/delete:" + service_name
                    ], check=True, capture_output=True)
                    
                else:  # Linux and others
                    cred_file = os.path.expanduser(f"~/.{service_name}")
                    if os.path.exists(cred_file):
                        os.remove(cred_file)
                
                print(f"✅ Password cleared from keychain for project '{self.project_name}'")
                print("💡 Use 'pass' command to store a new password")
                ret_val = True
                
            except subprocess.CalledProcessError:
                print(f"❌ Failed to clear password from keychain")
                break
            except Exception as e:
                print(f"❌ Failed to clear password: {e}")
                self.logger.error(f"Failed to clear password: {e}")
                break
        
        self.logger.info(f"EXIT: clear_password, returning: {ret_val}")
        return ret_val
    
    def store_password(self, password: Optional[str] = None) -> bool:
        """Store password in keychain for this project."""
        ret_val = False
        self.logger.info("ENTRY: store_password")
        
        do_once = True
        while do_once:
            do_once = False
            
            if not password:
                password = getpass.getpass(f"Enter password for project '{self.project_name}': ")
                if not password:
                    print("❌ Password cannot be empty")
                    break
            
            if self._store_password(password):
                print(f"✅ Password stored in keychain for project '{self.project_name}'")
                print("💡 You can now use 'mount' without entering the password")
                ret_val = True
            else:
                print("❌ Failed to store password in keychain")
                break
        
        self.logger.info(f"EXIT: store_password, returning: {ret_val}")
        return ret_val
    
    def mount_secrets(self) -> bool:
        """Mount secrets - decrypt .projectname.secrets to secrets folder."""
        ret_val = False
        self.logger.info("ENTRY: mount_secrets")
        
        do_once = True
        while do_once:
            do_once = False
            
            # Check if already mounted
            if os.path.exists(self.secrets_dir):
                print("✅ Secrets are already mounted!")
                print(f"📁 Working in: {os.path.abspath(self.secrets_dir)}/")
                self._show_mounted_files()
                ret_val = True
                break
            
            # Check if encrypted file exists
            if not os.path.isfile(self.secrets_file):
                print(f"❌ {self.secrets_file} not found!")
                print("💡 Create secrets first with:")
                print(f"   python secrets_manager.py create")
                break
            
            # Get password
            password = self._get_password()
            if not password:
                print(f"ℹ️  No stored password found for project '{self.project_name}'")
                password = getpass.getpass(f"Enter password for project '{self.project_name}': ")
                if not password:
                    print("❌ Password required to decrypt secrets")
                    break
            
            try:
                print(f"🔓 Decrypting {self.secrets_file}...")
                
                # Load and validate secrets file
                with open(self.secrets_file, 'r') as f:
                    package = json.load(f)
                
                if "metadata" not in package or "files" not in package:
                    print("❌ Invalid secrets file format")
                    break
                
                metadata = package["metadata"]
                salt = base64.b64decode(metadata["salt"])
                key = self._derive_key(password, salt)
                
                # Create secrets directory
                os.makedirs(self.secrets_dir, exist_ok=True)
                self._secure_directory(self.secrets_dir)
                self._add_to_gitignore(f"{self.secrets_dir}/")
                
                file_count = len(package["files"])
                if file_count > 0:
                    print(f"📂 Extracting {file_count} files...")
                
                # Extract and decrypt files
                for relative_path, file_info in package["files"].items():
                    full_path = os.path.join(self.secrets_dir, relative_path)
                    
                    # Create parent directories
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    
                    # Decrypt content
                    encrypted_content = base64.b64decode(file_info["content"])
                    decrypted_content = self._decrypt_data(encrypted_content, key)
                    
                    if decrypted_content is None:
                        print(f"❌ Failed to decrypt file: {relative_path}")
                        print("❌ Wrong password or corrupted file")
                        shutil.rmtree(self.secrets_dir, ignore_errors=True)
                        break
                    
                    # Write file
                    with open(full_path, 'wb') as f:
                        f.write(decrypted_content)
                    
                    # Set permissions (Unix-like systems)
                    if self.platform != "windows" and "permissions" in file_info:
                        try:
                            perms = int(file_info["permissions"], 8)
                            os.chmod(full_path, perms)
                        except:
                            pass
                    
                    print(f"  ✓ {relative_path}")
                
                ret_val = True
                print(f"✅ Secrets mounted to {self.secrets_dir}/")
                self._show_mounted_files()
                print()
                print("💡 Edit files in secrets/ folder, then unmount to save changes")
                
                # Store hash of mounted files for change detection
                current_hash = self._calculate_secrets_hash()
                if current_hash:
                    self._store_secrets_hash(current_hash)
                
                # Offer to store password if it wasn't stored before
                if not self._has_stored_password():
                    response = input("\n💾 Store password in keychain for future use? (y/n): ").lower()
                    if response == 'y' or response == 'yes':
                        if self._store_password(password):
                            print("✅ Password stored in keychain")
                        else:
                            print("⚠️  Warning: Could not store password in keychain")
                
            except Exception as e:
                print(f"❌ Failed to mount secrets: {e}")
                if "wrong password" in str(e).lower() or "decrypt" in str(e).lower():
                    print("💡 Update stored password with: python secrets_manager.py pass")
                shutil.rmtree(self.secrets_dir, ignore_errors=True)
                break
        
        self.logger.info(f"EXIT: mount_secrets, returning: {ret_val}")
        return ret_val
    
    def unmount_secrets(self) -> bool:
        """Unmount secrets - encrypt secrets folder to .projectname.secrets and delete folder."""
        ret_val = False
        self.logger.info("ENTRY: unmount_secrets")
        
        do_once = True
        while do_once:
            do_once = False
            
            if not os.path.exists(self.secrets_dir):
                print("ℹ️  No secrets folder to unmount")
                ret_val = True
                break
            
            if not os.path.isdir(self.secrets_dir):
                print(f"❌ {self.secrets_dir} is not a directory")
                break
            
            # Get password from stored credentials
            password = self._get_password()
            if not password:
                print(f"❌ No stored password found for project '{self.project_name}'")
                print("💡 Store password first with:")
                print(f"   python secrets_manager.py pass")
                break
            
            # Check if secrets have changed since last mount
            if not self._secrets_have_changed():
                print("ℹ️  No changes detected in secrets folder")
                print("💡 Skipping re-encryption to avoid git pollution")
                
                # Clean up secrets folder anyway
                shutil.rmtree(self.secrets_dir, ignore_errors=True)
                print(f"✅ Deleted {self.secrets_dir}/ folder")
                ret_val = True
                break
            
            try:
                # Count files (excluding hash file)
                secrets_path = Path(self.secrets_dir)
                all_files = list(secrets_path.rglob('*'))
                files = [f for f in all_files if f.is_file() and f.name != self.HASH_FILE]
                file_count = len(files)
                
                if file_count == 0:
                    print("⚠️  No files found in secrets folder")
                    response = input("Delete empty secrets folder? (y/n): ").lower()
                    if response == 'y' or response == 'yes':
                        shutil.rmtree(self.secrets_dir, ignore_errors=True)
                        print(f"✅ Deleted empty {self.secrets_dir}/ folder")
                        ret_val = True
                    break
                
                print(f"🔐 Encrypting {file_count} files...")
                
                # Generate salt and derive key
                salt = secure_random.token_bytes(32)
                key = self._derive_key(password, salt)
                
                # Create metadata
                metadata = {
                    "version": self.VERSION,
                    "project": self.project_name,
                    "created": self._get_timestamp(),
                    "salt": base64.b64encode(salt).decode('utf-8')
                }
                
                # Collect and encrypt all files (excluding hash file)
                file_data = {}
                
                for file_path in files:
                    relative_path = file_path.relative_to(secrets_path)
                    
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    # Encrypt file content
                    encrypted_content = self._encrypt_data(content, key)
                    if not encrypted_content:
                        print(f"❌ Failed to encrypt file: {relative_path}")
                        break
                    
                    file_data[str(relative_path)] = {
                        "content": base64.b64encode(encrypted_content).decode('utf-8'),
                        "permissions": oct(file_path.stat().st_mode)[-3:] if self.platform != "windows" else "644"
                    }
                    print(f"  ✓ {relative_path}")
                
                # Create the secrets package
                package = {
                    "metadata": metadata,
                    "files": file_data
                }
                
                # Create backup if file exists
                backup_created = False
                if os.path.exists(self.secrets_file):
                    backup_file = f"{self.secrets_file}.backup"
                    shutil.copy2(self.secrets_file, backup_file)
                    backup_created = True
                
                # Write encrypted file
                with open(self.secrets_file, 'w') as f:
                    json.dump(package, f, indent=2, sort_keys=True)
                
                # Store password for future use
                self._store_password(password)
                
                # Calculate and store new hash for next comparison
                new_hash = self._calculate_secrets_hash()
                if new_hash:
                    self._store_secrets_hash(new_hash)
                
                # Clean up secrets folder
                shutil.rmtree(self.secrets_dir, ignore_errors=True)
                
                # Remove backup if successful
                if backup_created:
                    os.remove(backup_file)
                
                ret_val = True
                print(f"✅ Secrets encrypted to {self.secrets_file}")
                print(f"✅ Deleted {self.secrets_dir}/ folder")
                print("")
                print("💡 The encrypted file is safe to commit to git:")
                print(f"   git add {self.secrets_file}")
                print("   git commit -m 'Update encrypted secrets'")
                
            except Exception as e:
                print(f"❌ Failed to unmount secrets: {e}")
                # Restore backup if it exists
                backup_file = f"{self.secrets_file}.backup"
                if os.path.exists(backup_file):
                    shutil.move(backup_file, self.secrets_file)
                    print("🔄 Restored backup of encrypted file")
                break
        
        self.logger.info(f"EXIT: unmount_secrets, returning: {ret_val}")
        return ret_val
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of secrets manager."""
        mounted = os.path.exists(self.secrets_dir)
        secrets_file_exists = os.path.isfile(self.secrets_file)
        
        status = {
            "project": self.project_name,
            "secrets_file_exists": secrets_file_exists,
            "mounted": mounted,
            "secrets_dir": self.secrets_dir,
            "password_stored": self._has_stored_password()
        }
        
        if secrets_file_exists:
            try:
                with open(self.secrets_file, 'r') as f:
                    package = json.load(f)
                status["version"] = package.get("metadata", {}).get("version", "unknown")
                status["encrypted_file_count"] = len(package.get("files", {}))
                status["created"] = package.get("metadata", {}).get("created", "unknown")
            except:
                status["version"] = "error"
                status["encrypted_file_count"] = 0
                status["created"] = "error"
        
        if mounted:
            # Count current files in secrets dir (excluding hash file)
            try:
                secrets_path = Path(self.secrets_dir)
                files = [f for f in secrets_path.rglob('*') if f.is_file() and f.name != self.HASH_FILE]
                status["current_file_count"] = len(files)
            except:
                status["current_file_count"] = 0
        
        return status
    
    def _show_mounted_files(self):
        """Show helpful information about mounted files."""
        if not os.path.exists(self.secrets_dir):
            return
        
        print(f"📋 Files in {self.secrets_dir}/:")
        
        # Show files in a helpful way
        file_found = False
        for root, dirs, files in os.walk(self.secrets_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.secrets_dir)
                print(f"   • {rel_path}")
                file_found = True
                
                # Show helpful suggestions for common file types
                if file.endswith('.env'):
                    print(f"     💡 Source: source {full_path}")
                elif file.endswith(('.pem', '.key')):
                    print(f"     💡 SSH/SSL key")
                elif file.endswith(('.p12', '.pfx')):
                    print(f"     💡 Certificate bundle")
                elif file == "README.txt":
                    print(f"     💡 Helpful information")
        
        if not file_found:
            print("   (no files yet - add some!)")
    
    def _show_helpful_status(self, status: Dict[str, Any]):
        """Show status in a user-friendly way."""
        print(f"📋 Status for project: {status['project']}")
        print(f"   Encrypted file: {'✅ exists' if status['secrets_file_exists'] else '❌ not found'}")
        
        if status['secrets_file_exists']:
            print(f"   Encrypted files: {status['encrypted_file_count']} files")
            print(f"   Created: {status['created']}")
        
        print(f"   Currently mounted: {'✅ yes' if status['mounted'] else '❌ no'}")
        
        if status['mounted']:
            print(f"   Working folder: {status['secrets_dir']}/")
            print(f"   Current files: {status.get('current_file_count', 0)} files")
        
        print(f"   Password stored: {'✅ yes' if status['password_stored'] else '❌ no'}")
        
        # Show next steps
        print("\n💡 Next steps:")
        if not status['secrets_file_exists']:
            print(f"   python secrets_manager.py create")
        elif not status['mounted']:
            print(f"   python secrets_manager.py mount")
            if not status['password_stored']:
                print(f"   (will prompt for password)")
        else:
            print("   1. Edit files in secrets/ folder")
            print(f"   2. python secrets_manager.py unmount")
            print(f"   3. python secrets_manager.py clear  # Optional: remove stored password")
    
    def _calculate_secrets_hash(self) -> str:
        """Calculate combined hash of all files in secrets directory (excluding hash file)."""
        ret_val = ""
        self.logger.info("ENTRY: _calculate_secrets_hash")
        
        do_once = True
        while do_once:
            do_once = False
            
            if not os.path.exists(self.secrets_dir):
                ret_val = ""
                break
                
            try:
                hash_obj = hashlib.sha256()
                secrets_path = Path(self.secrets_dir)
                
                # Get all files except the hash file, sorted for deterministic hashing
                all_files = list(secrets_path.rglob('*'))
                files = sorted([f for f in all_files if f.is_file() and f.name != self.HASH_FILE])
                
                for file_path in files:
                    # Add relative path to hash for structure changes
                    relative_path = file_path.relative_to(secrets_path)
                    hash_obj.update(str(relative_path).encode('utf-8'))
                    
                    # Add file content to hash
                    with open(file_path, 'rb') as f:
                        while chunk := f.read(self.CHUNK_SIZE):
                            hash_obj.update(chunk)
                
                ret_val = hash_obj.hexdigest()
                self.logger.info(f"Calculated hash for {len(files)} files: {ret_val[:12]}...")
                
            except Exception as e:
                self.logger.error(f"Failed to calculate secrets hash: {e}")
                ret_val = ""
                break
        
        self.logger.info(f"EXIT: _calculate_secrets_hash, returning: {ret_val}")
        return ret_val
    
    def _store_secrets_hash(self, hash_value: str):
        """Store the secrets hash in the hash file."""
        try:
            hash_file_path = os.path.join(self.secrets_dir, self.HASH_FILE)
            with open(hash_file_path, 'w') as f:
                f.write(hash_value)
            self.logger.info(f"Stored secrets hash: {hash_value[:12]}...")
        except Exception as e:
            self.logger.warning(f"Could not store secrets hash: {e}")
    
    def _get_stored_hash(self) -> Optional[str]:
        """Get the stored secrets hash from the hash file."""
        try:
            hash_file_path = os.path.join(self.secrets_dir, self.HASH_FILE)
            if os.path.exists(hash_file_path):
                with open(hash_file_path, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            self.logger.warning(f"Could not read stored hash: {e}")
        return None
    
    def _secrets_have_changed(self) -> bool:
        """Check if secrets have changed since last mount."""
        current_hash = self._calculate_secrets_hash()
        stored_hash = self._get_stored_hash()
        
        if not stored_hash:
            # No stored hash means first time or error, assume changed
            return True
        
        has_changed = current_hash != stored_hash
        if has_changed:
            self.logger.info("Secrets have changed")
        else:
            self.logger.info("Secrets unchanged")
        
        return has_changed
    
    def _add_to_gitignore(self, entry: str):
        """Add a single entry to .gitignore if not already present."""
        try:
            # Read existing .gitignore
            existing_lines = []
            if os.path.exists(self.gitignore_file):
                with open(self.gitignore_file, 'r') as f:
                    existing_lines = [line.strip() for line in f.readlines()]
            
            # Check if already present
            if entry not in existing_lines:
                # Add to .gitignore
                with open(self.gitignore_file, 'a') as f:
                    if existing_lines and existing_lines[-1].strip():
                        f.write('\n')
                    f.write(f"{entry}\n")
                
                self.logger.info(f"Added {entry} to .gitignore")
        
        except Exception as e:
            self.logger.warning(f"Could not update .gitignore: {e}")
        """Add a single entry to .gitignore if not already present."""
        try:
            # Read existing .gitignore
            existing_lines = []
            if os.path.exists(self.gitignore_file):
                with open(self.gitignore_file, 'r') as f:
                    existing_lines = [line.strip() for line in f.readlines()]
            
            # Check if already present
            if entry not in existing_lines:
                # Add to .gitignore
                with open(self.gitignore_file, 'a') as f:
                    if existing_lines and existing_lines[-1].strip():
                        f.write('\n')
                    f.write(f"{entry}\n")
                
                self.logger.info(f"Added {entry} to .gitignore")
        
        except Exception as e:
            self.logger.warning(f"Could not update .gitignore: {e}")
    
    # Security and utility methods
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000, 32)
    
    def _encrypt_data(self, data: bytes, key: bytes) -> Optional[bytes]:
        """Encrypt data using AES-256 (simplified implementation)."""
        try:
            # Simple XOR encryption for demo (use proper AES in production)
            iv = secure_random.token_bytes(16)
            encrypted = bytearray()
            key_extended = (key * ((len(data) // len(key)) + 1))[:len(data)]
            
            for i, byte in enumerate(data):
                encrypted.append(byte ^ key_extended[i] ^ iv[i % len(iv)])
            
            return iv + bytes(encrypted)
            
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            return None
    
    def _decrypt_data(self, encrypted_data: bytes, key: bytes) -> Optional[bytes]:
        """Decrypt data."""
        try:
            if len(encrypted_data) < 16:
                return None
            
            iv = encrypted_data[:16]
            encrypted = encrypted_data[16:]
            
            # Simple XOR decryption
            decrypted = bytearray()
            key_extended = (key * ((len(encrypted) // len(key)) + 1))[:len(encrypted)]
            
            for i, byte in enumerate(encrypted):
                decrypted.append(byte ^ key_extended[i] ^ iv[i % len(iv)])
            
            return bytes(decrypted)
            
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            return None
    
    def _store_password(self, password: str) -> bool:
        """Store password in platform-specific credential store."""
        service_name = self.keychain_entry_name
        
        try:
            if self.platform == "darwin":  # macOS
                subprocess.run([
                    "security", "add-generic-password",
                    "-s", service_name,
                    "-a", getpass.getuser(),
                    "-w", password,
                    "-U"  # Update if exists
                ], check=True, capture_output=True)
                
            elif self.platform == "windows":
                subprocess.run([
                    "cmdkey", "/generic:" + service_name,
                    "/user:" + getpass.getuser(),
                    "/pass:" + password
                ], check=True, capture_output=True)
                
            else:  # Linux and others
                # Store in encrypted file as fallback
                cred_file = os.path.expanduser(f"~/.{service_name}")
                salt = secure_random.token_bytes(32)
                key = self._derive_key(getpass.getuser(), salt)
                encrypted_password = self._encrypt_data(password.encode(), key)
                
                with open(cred_file, 'wb') as f:
                    f.write(salt + encrypted_password)
                os.chmod(cred_file, 0o600)
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Could not store password: {e}")
            return False
    
    def _get_password(self) -> Optional[str]:
        """Retrieve password from platform-specific credential store."""
        service_name = self.keychain_entry_name
        
        try:
            if self.platform == "darwin":  # macOS
                result = subprocess.run([
                    "security", "find-generic-password",
                    "-s", service_name,
                    "-a", getpass.getuser(),
                    "-w"
                ], check=True, capture_output=True, text=True)
                return result.stdout.strip()
                
            elif self.platform == "windows":
                # Windows credential retrieval requires parsing output
                result = subprocess.run([
                    "cmdkey", "/list:" + service_name
                ], capture_output=True, text=True)
                
                if service_name in result.stdout:
                    # Password stored, but Windows doesn't easily return it
                    # For simplicity, ask for password
                    return getpass.getpass("Enter secrets password: ")
                else:
                    return None
                    
            else:  # Linux and others
                cred_file = os.path.expanduser(f"~/.{service_name}")
                if os.path.exists(cred_file):
                    with open(cred_file, 'rb') as f:
                        data = f.read()
                    
                    if len(data) > 32:
                        salt = data[:32]
                        encrypted_password = data[32:]
                        key = self._derive_key(getpass.getuser(), salt)
                        decrypted = self._decrypt_data(encrypted_password, key)
                        
                        if decrypted:
                            return decrypted.decode()
                
                return None
                
        except subprocess.CalledProcessError:
            return None
        except Exception as e:
            self.logger.warning(f"Could not retrieve stored password: {e}")
            return None
    
    def _has_stored_password(self) -> bool:
        """Check if password is stored in credential store."""
        service_name = self.keychain_entry_name
        
        try:
            if self.platform == "darwin":
                subprocess.run([
                    "security", "find-generic-password",
                    "-s", service_name,
                    "-a", getpass.getuser()
                ], check=True, capture_output=True)
                return True
                
            elif self.platform == "windows":
                result = subprocess.run([
                    "cmdkey", "/list:" + service_name
                ], capture_output=True, text=True)
                return service_name in result.stdout
                
            else:  # Linux
                cred_file = os.path.expanduser(f"~/.{service_name}")
                return os.path.exists(cred_file)
                
        except:
            return False
    
    def _secure_directory(self, directory: str):
        """Set secure permissions on directory."""
        if self.platform != "windows":
            try:
                os.chmod(directory, 0o700)  # rwx------
            except:
                pass
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


def main():
    """Main CLI interface."""
    # Show help if no arguments provided
    if len(sys.argv) == 1:
        print(__doc__)
        print("\nUSAGE:")
        print("  python secrets_manager.py <command> [options]")
        print("  python secrets_manager.py create [--project <n>] [--secrets-dir <dir>] [--password <pass>]")
        print("\nCOMMANDS:")
        print("  create    Create empty secrets folder (fails if .projectname.secrets already exists)")
        print("  mount     Mount secrets (decrypt .projectname.secrets to folder)")
        print("  unmount   Unmount secrets (encrypt folder to .projectname.secrets)")
        print("  pass      Store password in keychain for this project")
        print("  clear     Remove stored password from keychain")
        print("  status    Show current status")
        print("\nEXAMPLES:")
        print("  python secrets_manager.py create                    # Create using folder name")
        print("  python secrets_manager.py create --project myapp    # Create with custom name")
        print("  python secrets_manager.py create --secrets-dir work # Create with custom folder")
        print("  python secrets_manager.py mount                     # Mount current project")
        print("  python secrets_manager.py pass --password secret    # Store specific password")
        print("  python secrets_manager.py clear                     # Remove stored password")
        print("  python secrets_manager.py unmount")
        print("  python secrets_manager.py status")
        print("\nOPTIONS:")
        print("  --project NAME       Project name (only for 'create' command)")
        print("  --secrets-dir DIR    Secrets directory name (only for 'create' command, default: secrets)")
        print("  --password PASS      Password (only for 'create' and 'pass' commands)")
        print("  --verbose, -v        Verbose logging")
        sys.exit(0)
    
    parser = argparse.ArgumentParser(
        description="Cross-Platform Secrets Manager",
        epilog="""
Examples:
  python secrets_manager.py create                           # Create project using folder name
  python secrets_manager.py create --project myapp           # Create project with specific name  
  python secrets_manager.py create --secrets-dir mysecrets   # Create with custom secrets folder
  python secrets_manager.py create --password mypass         # Create with specified password
  python secrets_manager.py mount                            # Mount project in current folder
  python secrets_manager.py pass                             # Store password for current project
  python secrets_manager.py pass --password mypass           # Store specific password
  python secrets_manager.py clear                            # Remove stored password
  python secrets_manager.py unmount                          # Unmount current project
  python secrets_manager.py status                           # Show status of current project
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("command", choices=["create", "mount", "unmount", "pass", "clear", "status"],
                       help="Command to execute")
    parser.add_argument("--project", 
                       help="Project name (only used with 'create' command, default: current folder name)")
    parser.add_argument("--secrets-dir", default="secrets", 
                       help="Secrets directory name (only used with 'create' command, default: secrets)")
    parser.add_argument("--password", help="Password (only used with 'create' and 'pass' commands)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Determine project name
    if args.command == "create" and args.project:
        # Only use --project argument for create command
        project_name = args.project
    else:
        # All other commands use current directory name
        project_name = os.path.basename(os.path.abspath(os.getcwd()))
        if not project_name or project_name == '/':
            project_name = "secrets_project"  # fallback name
    
    # Determine secrets directory (only for create command)
    if args.command == "create":
        secrets_dir = args.secrets_dir
    else:
        secrets_dir = "secrets"  # Fixed for all other commands
    
    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print(f"🚀 Using project: {project_name}")
    manager = SecretsManager(project_name, secrets_dir)
    
    try:
        if args.command == "create":
            # Only create accepts --password, --project, --secrets-dir
            if manager.create_secrets(args.password):
                sys.exit(0)
            else:
                sys.exit(1)
        
        elif args.command == "mount":
            # Mount doesn't accept any optional parameters
            if manager.mount_secrets():
                sys.exit(0)
            else:
                sys.exit(1)
        
        elif args.command == "unmount":
            # Unmount doesn't accept any optional parameters
            if manager.unmount_secrets():
                sys.exit(0)
            else:
                sys.exit(1)
        
        elif args.command == "pass":
            # Only pass accepts --password
            if manager.store_password(args.password):
                sys.exit(0)
            else:
                sys.exit(1)
        
        elif args.command == "clear":
            # Clear doesn't accept any optional parameters
            if manager.clear_password():
                sys.exit(0)
            else:
                sys.exit(1)
        
        elif args.command == "status":
            # Status doesn't accept any optional parameters
            status = manager.get_status()
            manager._show_helpful_status(status)
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled")
        # Try to clean up if mounting was interrupted
        if args.command == "mount" and os.path.exists(manager.secrets_dir):
            shutil.rmtree(manager.secrets_dir, ignore_errors=True)
            print(f"🧹 Cleaned up {manager.secrets_dir}/ folder")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()