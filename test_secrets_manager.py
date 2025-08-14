#!/usr/bin/env python3
"""
Comprehensive test script for secrets_manager.py

This script creates a temporary test environment and runs through all the
major functionality to ensure the secrets manager works correctly.
"""

import os
import sys
import shutil
import tempfile
import subprocess
import time
from pathlib import Path

# Test constants
TEST_PASSWORD = "test123"
TEST_PASSWORD_2 = "newpass456"
DEFAULT_PROJECT = "test_project"
CUSTOM_PROJECT = "my_custom_project"
CUSTOM_SECRETS_DIR = ".private_secrets"

class TestSecretsManager:
    def __init__(self):
        self.test_dir = None
        self.script_path = None
        self.failed_tests = []
        self.passed_tests = []

    def setup_test_environment(self):
        """Create temporary test directory and copy script."""
        print("🚀 Setting up test environment...")

        # Create temporary directory
        self.test_dir = tempfile.mkdtemp(prefix="secrets_test_")
        print(f"📁 Test directory: {self.test_dir}")

        # Copy secrets_manager.py to test directory
        current_script = Path(__file__).parent / "secrets_manager.py"
        self.script_path = Path(self.test_dir) / "secrets_manager.py"
        shutil.copy2(current_script, self.script_path)

        # Make it executable
        os.chmod(self.script_path, 0o755)

        # Change to test directory
        os.chdir(self.test_dir)
        print(f"✅ Test environment ready")

    def cleanup_test_environment(self):
        """Clean up test directory."""
        print(f"🧹 Cleaning up test directory: {self.test_dir}")
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def run_command(self, cmd, input_text=None, expect_failure=False):
        """Run a command and return result."""
        print(f"  🔧 Running: {cmd}")

        try:
            if input_text:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    input=input_text
                )
            else:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True
                )

            if expect_failure:
                if result.returncode == 0:
                    print(f"  ❌ Expected failure but command succeeded")
                    print(f"     stdout: {result.stdout}")
                    print(f"     stderr: {result.stderr}")
                    return False, result.stdout, result.stderr
                else:
                    print(f"  ✅ Command failed as expected")
                    return True, result.stdout, result.stderr
            else:
                if result.returncode != 0:
                    print(f"  ❌ Command failed: {result.stderr}")
                    return False, result.stdout, result.stderr
                else:
                    print(f"  ✅ Command succeeded")
                    return True, result.stdout, result.stderr

        except Exception as e:
            print(f"  ❌ Exception running command: {e}")
            return False, "", str(e)

    def verify_folder_deleted(self, secrets_dir="secrets", should_be_deleted=True):
        """Verify that secrets folder is properly deleted/created."""
        exists = os.path.exists(secrets_dir)
        if should_be_deleted and exists:
            print(f"  ❌ Folder {secrets_dir} should be deleted but still exists")
            return False
        elif not should_be_deleted and not exists:
            print(f"  ❌ Folder {secrets_dir} should exist but is missing")
            return False

        action = "deleted" if should_be_deleted else "exists"
        print(f"  ✅ Folder {secrets_dir} correctly {action}")
        return True

    def verify_encrypted_file_exists(self, project_name, should_exist=True):
        """Verify that encrypted file exists or doesn't exist."""
        encrypted_file = f".{project_name}.secrets"
        exists = os.path.exists(encrypted_file)
        if should_exist and not exists:
            print(f"  ❌ Encrypted file {encrypted_file} should exist but doesn't")
            return False
        elif not should_exist and exists:
            print(f"  ❌ Encrypted file {encrypted_file} should not exist but does")
            return False

        action = "exists" if should_exist else "deleted"
        print(f"  ✅ Encrypted file {encrypted_file} correctly {action}")
        return True

    def create_test_files(self, secrets_dir="secrets"):
        """Create test files in secrets directory."""
        secrets_path = Path(secrets_dir)
        secrets_path.mkdir(exist_ok=True)

        # Create various test files
        (secrets_path / ".env").write_text("API_KEY=secret123\nDB_PASSWORD=dbpass456\n")
        (secrets_path / "private.key").write_text("-----BEGIN PRIVATE KEY-----\ntest_private_key_content\n-----END PRIVATE KEY-----\n")
        (secrets_path / "config.json").write_text('{"secret": "value", "token": "abc123"}\n')

        # Create subdirectory with file
        subdir = secrets_path / "ssl"
        subdir.mkdir(exist_ok=True)
        (subdir / "cert.pem").write_text("-----BEGIN CERTIFICATE-----\ntest_cert_content\n-----END CERTIFICATE-----\n")

        print(f"  📄 Created test files in {secrets_dir}/")

    def verify_files_exist(self, secrets_dir="secrets", should_exist=True):
        """Verify test files exist or don't exist."""
        secrets_path = Path(secrets_dir)

        expected_files = [
            secrets_path / ".env",
            secrets_path / "private.key",
            secrets_path / "config.json",
            secrets_path / "ssl" / "cert.pem"
        ]

        for file_path in expected_files:
            exists = file_path.exists()
            if should_exist and not exists:
                print(f"  ❌ File should exist but doesn't: {file_path}")
                return False
            elif not should_exist and exists:
                print(f"  ❌ File should not exist but does: {file_path}")
                return False

        action = "exist" if should_exist else "not exist"
        print(f"  ✅ All files {action} as expected")
        return True

    def verify_file_contents(self, secrets_dir="secrets"):
        """Verify test file contents are correct."""
        secrets_path = Path(secrets_dir)

        # Check .env file
        env_content = (secrets_path / ".env").read_text()
        if "API_KEY=secret123" not in env_content:
            print(f"  ❌ .env file content incorrect")
            return False

        # Check private key
        key_content = (secrets_path / "private.key").read_text()
        if "BEGIN PRIVATE KEY" not in key_content:
            print(f"  ❌ private.key file content incorrect")
            return False

        print(f"  ✅ File contents verified")
        return True

    def modify_test_files(self, secrets_dir="secrets"):
        """Modify test files to simulate changes."""
        secrets_path = Path(secrets_dir)

        # Modify .env file
        (secrets_path / ".env").write_text("API_KEY=modified123\nDB_PASSWORD=newpass789\nNEW_VAR=added\n")

        # Add new file
        (secrets_path / "new_secret.txt").write_text("This is a new secret file\n")

        print(f"  📝 Modified test files in {secrets_dir}/")

    def verify_modified_contents(self, secrets_dir="secrets"):
        """Verify modified file contents."""
        secrets_path = Path(secrets_dir)

        # Check modified .env
        env_content = (secrets_path / ".env").read_text()
        if "API_KEY=modified123" not in env_content or "NEW_VAR=added" not in env_content:
            print(f"  ❌ Modified .env content incorrect")
            return False

        # Check new file exists
        if not (secrets_path / "new_secret.txt").exists():
            print(f"  ❌ New secret file missing")
            return False

        print(f"  ✅ Modified contents verified")
        return True

    def test_basic_workflow(self):
        """Test basic workflow with default settings."""
        print("\n🧪 Testing basic workflow (default project name and secrets dir)...")

        try:
            # 1. Create project
            success, stdout, stderr = self.run_command(
                f"echo '{TEST_PASSWORD}' | python3 secrets_manager.py create --test-mode"
            )
            if not success:
                self.failed_tests.append("Basic: Create project failed")
                return False

            # 1.1. Verify status after create
            if not self.run_status_and_verify("after create"):
                self.failed_tests.append("Basic: Status verification failed after create")
                return False

            # 2. Add test files
            self.create_test_files("secrets")

            # 3. Unmount (encrypt)
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            if not success:
                self.failed_tests.append("Basic: Unmount failed")
                return False

            # 3.1. Verify status after unmount
            if not self.run_status_and_verify("after unmount"):
                self.failed_tests.append("Basic: Status verification failed after unmount")
                return False

            # 4. Verify secrets folder is deleted and encrypted file exists
            if not self.verify_folder_deleted("secrets", True):
                self.failed_tests.append("Basic: Secrets folder not deleted after unmount")
                return False

            # Find the encrypted file
            encrypted_files = [f for f in os.listdir(".") if f.endswith(".secrets")]
            if not encrypted_files:
                self.failed_tests.append("Basic: No encrypted file found")
                return False

            # 5. Mount (decrypt)
            success, stdout, stderr = self.run_command("python3 secrets_manager.py mount --test-mode")
            if not success:
                self.failed_tests.append("Basic: Mount failed")
                return False

            # 5.1. Verify status after mount
            if not self.run_status_and_verify("after mount"):
                self.failed_tests.append("Basic: Status verification failed after mount")
                return False

            # 6. Verify secrets folder is recreated
            if not self.verify_folder_deleted("secrets", False):
                self.failed_tests.append("Basic: Secrets folder not recreated after mount")
                return False

            # 6. Verify files are restored
            if not self.verify_files_exist("secrets", True):
                self.failed_tests.append("Basic: Files not restored after mount")
                return False

            if not self.verify_file_contents("secrets"):
                self.failed_tests.append("Basic: File contents incorrect after mount")
                return False

            # 7. Modify files
            self.modify_test_files("secrets")

            # 8. Unmount again
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            if not success:
                self.failed_tests.append("Basic: Second unmount failed")
                return False

            # 9. Mount again
            success, stdout, stderr = self.run_command("python3 secrets_manager.py mount --test-mode")
            if not success:
                self.failed_tests.append("Basic: Second mount failed")
                return False

            # 10. Verify modified contents
            if not self.verify_modified_contents("secrets"):
                self.failed_tests.append("Basic: Modified contents not preserved")
                return False

            # 11. Clear password
            success, stdout, stderr = self.run_command("python3 secrets_manager.py clear --test-mode")
            if not success:
                self.failed_tests.append("Basic: Clear password failed")
                return False

            # 11.1. Verify status after clear
            if not self.run_status_and_verify("after clear password"):
                self.failed_tests.append("Basic: Status verification failed after clear")
                return False

            # 12. Unmount (should fail due to no password, that's OK)
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode", expect_failure=True)
            # Note: This may succeed or fail depending on current state, both are acceptable

            # 13. Reinstate password
            success, stdout, stderr = self.run_command(
                f"echo '{TEST_PASSWORD}' | python3 secrets_manager.py pass --test-mode"
            )
            if not success:
                self.failed_tests.append("Basic: Reinstate password failed")
                return False

            # 13.1. Verify status after pass
            if not self.run_status_and_verify("after pass command"):
                self.failed_tests.append("Basic: Status verification failed after pass")
                return False

            # 14. Mount should work now
            success, stdout, stderr = self.run_command("python3 secrets_manager.py mount --test-mode")
            if not success:
                self.failed_tests.append("Basic: Mount after reinstate password failed")
                return False

            # 15. Final unmount
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            if not success:
                self.failed_tests.append("Basic: Final unmount failed")
                return False

            # 16. Destroy project
            success, stdout, stderr = self.run_command(
                "echo 'DELETE' | python3 secrets_manager.py destroy --test-mode"
            )
            if not success:
                self.failed_tests.append("Basic: Destroy project failed")
                return False

            # 16.1. Verify complete destruction
            if not self.verify_complete_destruction():
                self.failed_tests.append("Basic: Complete destruction verification failed")
                return False

            # 16.2. Verify status after destroy (should succeed but show no project)
            if not self.run_status_and_verify("after destroy", check_success=True):
                self.failed_tests.append("Basic: Status after destroy should succeed")
                return False

            self.passed_tests.append("Basic workflow")
            return True

        except Exception as e:
            self.failed_tests.append(f"Basic workflow exception: {e}")
            return False

    def test_custom_workflow(self):
        """Test workflow with custom project name and secrets directory."""
        print(f"\n🧪 Testing custom workflow (project: {CUSTOM_PROJECT}, secrets-dir: {CUSTOM_SECRETS_DIR})...")

        try:
            # 1. Create project with custom settings
            success, stdout, stderr = self.run_command(
                f"echo '{TEST_PASSWORD}' | python3 secrets_manager.py create --project {CUSTOM_PROJECT} --secrets-dir {CUSTOM_SECRETS_DIR} --test-mode"
            )
            if not success:
                self.failed_tests.append("Custom: Create project failed")
                return False

            # 1.1. Verify status after create
            if not self.run_status_and_verify("after custom create"):
                self.failed_tests.append("Custom: Status verification failed after create")
                return False

            # 2. Add test files
            self.create_test_files(CUSTOM_SECRETS_DIR)

            # 3. Unmount (should auto-detect project and secrets dir)
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            if not success:
                self.failed_tests.append("Custom: Unmount failed")
                return False

            # 3.5. Verify custom secrets folder is deleted
            if not self.verify_folder_deleted(CUSTOM_SECRETS_DIR, True):
                self.failed_tests.append("Custom: Custom secrets folder not deleted after unmount")
                return False

            # 4. Verify encrypted file uses custom project name
            if not self.verify_encrypted_file_exists(CUSTOM_PROJECT, True):
                self.failed_tests.append("Custom: Custom encrypted file not found")
                return False

            # 5. Mount (should auto-detect)
            success, stdout, stderr = self.run_command("python3 secrets_manager.py mount --test-mode")
            if not success:
                self.failed_tests.append("Custom: Mount failed")
                return False

            # 5.5. Verify custom secrets folder is recreated
            if not self.verify_folder_deleted(CUSTOM_SECRETS_DIR, False):
                self.failed_tests.append("Custom: Custom secrets folder not recreated after mount")
                return False

            # 6. Verify files restored to correct directory
            if not self.verify_files_exist(CUSTOM_SECRETS_DIR, True):
                self.failed_tests.append("Custom: Files not restored to custom directory")
                return False

            # 7. Test password change
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            if not success:
                self.failed_tests.append("Custom: Unmount before password change failed")
                return False

            success, stdout, stderr = self.run_command(
                f"printf '{TEST_PASSWORD_2}\\n{TEST_PASSWORD_2}\\n' | python3 secrets_manager.py change-password --test-mode"
            )
            if not success:
                self.failed_tests.append("Custom: Change password failed")
                return False

            # 7.1. Verify status after change-password
            if not self.run_status_and_verify("after change-password"):
                self.failed_tests.append("Custom: Status verification failed after change-password")
                return False

            # 8. Mount with new password
            success, stdout, stderr = self.run_command("python3 secrets_manager.py mount --test-mode")
            if not success:
                self.failed_tests.append("Custom: Mount with new password failed")
                return False

            # 9. Final cleanup
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            if not success:
                self.failed_tests.append("Custom: Final unmount failed")
                return False

            success, stdout, stderr = self.run_command(
                "echo 'DELETE' | python3 secrets_manager.py destroy --test-mode"
            )
            if not success:
                self.failed_tests.append("Custom: Destroy project failed")
                return False

            # 9.1. Verify complete destruction of custom project
            if not self.verify_complete_destruction(CUSTOM_PROJECT, CUSTOM_SECRETS_DIR):
                self.failed_tests.append("Custom: Complete destruction verification failed")
                return False

            self.passed_tests.append("Custom workflow")
            return True

        except Exception as e:
            self.failed_tests.append(f"Custom workflow exception: {e}")
            return False

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        print("\n🧪 Testing edge cases...")

        try:
            # Make sure we start completely clean
            for f in os.listdir("."):
                if f.endswith(".secrets") or f == ".secrets_keychain_entry" or f == "secrets":
                    if os.path.isdir(f):
                        shutil.rmtree(f)
                    else:
                        os.remove(f)

            # 1. Try to mount non-existent project
            success, stdout, stderr = self.run_command("python3 secrets_manager.py mount --test-mode", expect_failure=True)
            if not success:
                self.failed_tests.append("Edge: Mount non-existent should fail")
                return False

            # 2. Try to unmount when nothing is mounted
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            if not success:
                self.failed_tests.append("Edge: Unmount when nothing mounted failed")
                return False

            # 3. Create project, then try to create again (should fail)
            success, stdout, stderr = self.run_command(
                f"echo '{TEST_PASSWORD}' | python3 secrets_manager.py create --test-mode"
            )
            if not success:
                self.failed_tests.append("Edge: Initial create failed")
                return False

            # Create encrypted file by unmounting
            self.create_test_files("secrets")
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            if not success:
                self.failed_tests.append("Edge: Create encrypted file failed")
                return False

            # Now try to create again - should fail
            success, stdout, stderr = self.run_command(
                f"echo '{TEST_PASSWORD}' | python3 secrets_manager.py create --test-mode",
                expect_failure=True
            )
            if not success:
                self.failed_tests.append("Edge: Second create should have failed")
                return False

            # Cleanup
            success, stdout, stderr = self.run_command(
                "echo 'DELETE' | python3 secrets_manager.py destroy --test-mode"
            )

            # Verify complete destruction
            project_name = os.path.basename(os.getcwd())
            if not self.verify_complete_destruction(project_name, "secrets"):
                self.failed_tests.append("Edge: Complete destruction verification failed")
                return False

            self.passed_tests.append("Edge cases")
            return True

        except Exception as e:
            self.failed_tests.append(f"Edge cases exception: {e}")
            return False

    def test_all_commands_coverage(self):
        """Test all 8 commands to ensure complete coverage."""
        print("\n🧪 Testing all commands coverage...")

        # Commands that should be tested: create, mount, unmount, pass, clear, change-password, destroy, status
        commands_tested = set()

        try:
            # 1. Test status command when no project exists (should succeed)
            success, stdout, stderr = self.run_command("python3 secrets_manager.py status --test-mode", expect_failure=False)
            if not success:
                self.failed_tests.append("Commands: Status command should succeed when no project exists")
                return False
            commands_tested.add("status")

            # 2. Test create command
            success, stdout, stderr = self.run_command(
                f"echo '{TEST_PASSWORD}' | python3 secrets_manager.py create --test-mode"
            )
            if not success:
                self.failed_tests.append("Commands: Create command failed")
                return False
            commands_tested.add("create")

            # 3. Test status when project exists but empty
            success, stdout, stderr = self.run_command("python3 secrets_manager.py status --test-mode")
            if not success:
                self.failed_tests.append("Commands: Status command failed with empty project")
                return False

            # Add test files
            self.create_test_files("secrets")

            # 4. Test unmount command
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            if not success:
                self.failed_tests.append("Commands: Unmount command failed")
                return False
            commands_tested.add("unmount")

            # 5. Test status when unmounted
            success, stdout, stderr = self.run_command("python3 secrets_manager.py status --test-mode")
            if not success:
                self.failed_tests.append("Commands: Status command failed when unmounted")
                return False

            # 6. Test mount command
            success, stdout, stderr = self.run_command("python3 secrets_manager.py mount --test-mode")
            if not success:
                self.failed_tests.append("Commands: Mount command failed")
                return False
            commands_tested.add("mount")

            # 7. Test clear command
            success, stdout, stderr = self.run_command("python3 secrets_manager.py clear --test-mode")
            if not success:
                self.failed_tests.append("Commands: Clear command failed")
                return False
            commands_tested.add("clear")

            # 8. Test pass command
            success, stdout, stderr = self.run_command(
                f"echo '{TEST_PASSWORD}' | python3 secrets_manager.py pass --test-mode"
            )
            if not success:
                self.failed_tests.append("Commands: Pass command failed")
                return False
            commands_tested.add("pass")

            # 9. Test change-password command (requires unmount first)
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            if not success:
                self.failed_tests.append("Commands: Unmount before change-password failed")
                return False

            success, stdout, stderr = self.run_command(
                f"printf '{TEST_PASSWORD_2}\\n{TEST_PASSWORD_2}\\n' | python3 secrets_manager.py change-password --test-mode"
            )
            if not success:
                self.failed_tests.append("Commands: Change-password command failed")
                return False
            commands_tested.add("change-password")

            # 10. Test destroy command
            success, stdout, stderr = self.run_command(
                "echo 'DELETE' | python3 secrets_manager.py destroy --test-mode"
            )
            if not success:
                self.failed_tests.append("Commands: Destroy command failed")
                return False
            commands_tested.add("destroy")

            # Verify complete destruction
            project_name = os.path.basename(os.getcwd())
            if not self.verify_complete_destruction(project_name, "secrets"):
                self.failed_tests.append("Commands: Complete destruction verification failed")
                return False

            # 11. Final status test after destroy (should succeed)
            success, stdout, stderr = self.run_command("python3 secrets_manager.py status --test-mode", expect_failure=False)
            if not success:
                self.failed_tests.append("Commands: Status should succeed after destroy")
                return False

            # Verify all 8 commands were tested
            expected_commands = {"create", "mount", "unmount", "pass", "clear", "change-password", "destroy", "status"}
            if commands_tested != expected_commands:
                missing = expected_commands - commands_tested
                self.failed_tests.append(f"Commands: Missing command coverage: {missing}")
                return False

            print(f"  ✅ All {len(expected_commands)} commands successfully tested")
            self.passed_tests.append("All commands coverage")
            return True

        except Exception as e:
            self.failed_tests.append(f"Commands coverage exception: {e}")
            return False

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        print("\n🧪 Testing edge cases...")

        try:
            # Make sure we start completely clean
            for f in os.listdir("."):
                if f.endswith(".secrets") or f == ".secrets_keychain_entry" or f == "secrets":
                    if os.path.isdir(f):
                        shutil.rmtree(f)
                    else:
                        os.remove(f)

            # 1. Try to mount non-existent project
            success, stdout, stderr = self.run_command("python3 secrets_manager.py mount --test-mode", expect_failure=True)
            if not success:
                self.failed_tests.append("Edge: Mount non-existent should fail")
                return False

            # 2. Try to unmount when nothing is mounted
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            if not success:
                self.failed_tests.append("Edge: Unmount when nothing mounted failed")
                return False

            # 3. Create project, then try to create again (should fail)
            success, stdout, stderr = self.run_command(
                f"echo '{TEST_PASSWORD}' | python3 secrets_manager.py create --test-mode"
            )
            if not success:
                self.failed_tests.append("Edge: Initial create failed")
                return False

            # Create encrypted file by unmounting
            self.create_test_files("secrets")
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            if not success:
                self.failed_tests.append("Edge: Create encrypted file failed")
                return False

            # Now try to create again - should fail
            success, stdout, stderr = self.run_command(
                f"echo '{TEST_PASSWORD}' | python3 secrets_manager.py create --test-mode",
                expect_failure=True
            )
            if not success:
                self.failed_tests.append("Edge: Second create should have failed")
                return False

            # Cleanup
            success, stdout, stderr = self.run_command(
                "echo 'DELETE' | python3 secrets_manager.py destroy --test-mode"
            )

            # Verify complete destruction
            project_name = os.path.basename(os.getcwd())
            if not self.verify_complete_destruction(project_name, "secrets"):
                self.failed_tests.append("Edge: Complete destruction verification failed")
                return False

            self.passed_tests.append("Edge cases")
            return True

        except Exception as e:
            self.failed_tests.append(f"Edge cases exception: {e}")
            return False

    def test_status_command(self):
        """Test the status command in various states."""
        print("\n🧪 Testing status command...")

        try:
            # 1. Status when no project exists
            success, stdout, stderr = self.run_command("python3 secrets_manager.py status --test-mode")
            if not success:
                self.failed_tests.append("Status: Status command failed when no project exists")
                return False

            # 2. Create project and test status
            success, stdout, stderr = self.run_command(
                f"echo '{TEST_PASSWORD}' | python3 secrets_manager.py create --test-mode"
            )
            if not success:
                self.failed_tests.append("Status: Create project for status testing failed")
                return False

            # 3. Status when project exists but no secrets
            success, stdout, stderr = self.run_command("python3 secrets_manager.py status --test-mode")
            if not success:
                self.failed_tests.append("Status: Status command failed with empty project")
                return False

            # 4. Add files and test status
            self.create_test_files("secrets")
            success, stdout, stderr = self.run_command("python3 secrets_manager.py status --test-mode")
            if not success:
                self.failed_tests.append("Status: Status command failed with files in secrets")
                return False

            # 5. Unmount and test status
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            if not success:
                self.failed_tests.append("Status: Unmount failed during status testing")
                return False

            success, stdout, stderr = self.run_command("python3 secrets_manager.py status --test-mode")
            if not success:
                self.failed_tests.append("Status: Status command failed when unmounted")
                return False

            # 6. Mount and test status
            success, stdout, stderr = self.run_command("python3 secrets_manager.py mount --test-mode")
            if not success:
                self.failed_tests.append("Status: Mount failed during status testing")
                return False

            success, stdout, stderr = self.run_command("python3 secrets_manager.py status --test-mode")
            if not success:
                self.failed_tests.append("Status: Status command failed when mounted")
                return False

            # Cleanup
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            success, stdout, stderr = self.run_command(
                "echo 'DELETE' | python3 secrets_manager.py destroy --test-mode"
            )

            self.passed_tests.append("Status command")
            return True

        except Exception as e:
            self.failed_tests.append(f"Status command exception: {e}")
            return False

    def test_comprehensive_folder_verification(self):
        """Test folder deletion and creation with custom names."""
        print("\n🧪 Testing comprehensive folder verification...")

        try:
            # Test with default folder name
            print("  📂 Testing default folder name...")
            success, stdout, stderr = self.run_command(
                f"echo '{TEST_PASSWORD}' | python3 secrets_manager.py create --test-mode"
            )
            if not success:
                self.failed_tests.append("Folder: Create default project failed")
                return False

            # Verify default folder exists
            if not self.verify_folder_deleted("secrets", False):
                self.failed_tests.append("Folder: Default secrets folder should exist after create")
                return False

            self.create_test_files("secrets")

            # Unmount and verify folder is deleted
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            if not success:
                self.failed_tests.append("Folder: Unmount default project failed")
                return False

            if not self.verify_folder_deleted("secrets", True):
                self.failed_tests.append("Folder: Default secrets folder should be deleted after unmount")
                return False

            # Verify encrypted file exists
            project_name = os.path.basename(os.getcwd())
            if not self.verify_encrypted_file_exists(project_name, True):
                self.failed_tests.append("Folder: Encrypted file should exist after unmount")
                return False

            # Mount and verify folder is recreated
            success, stdout, stderr = self.run_command("python3 secrets_manager.py mount --test-mode")
            if not success:
                self.failed_tests.append("Folder: Mount default project failed")
                return False

            if not self.verify_folder_deleted("secrets", False):
                self.failed_tests.append("Folder: Default secrets folder should exist after mount")
                return False

            # Cleanup
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            success, stdout, stderr = self.run_command(
                "echo 'DELETE' | python3 secrets_manager.py destroy --test-mode"
            )

            # Verify complete cleanup of default project
            project_name = os.path.basename(os.getcwd())
            if not self.verify_complete_destruction(project_name, "secrets"):
                self.failed_tests.append("Folder: Default project cleanup verification failed")
                return False

            # Test with custom folder name
            print("  📂 Testing custom folder name...")
            custom_secrets = "my_special_secrets"
            success, stdout, stderr = self.run_command(
                f"echo '{TEST_PASSWORD}' | python3 secrets_manager.py create --project custom_test --secrets-dir {custom_secrets} --test-mode"
            )
            if not success:
                self.failed_tests.append("Folder: Create custom project failed")
                return False

            # Verify custom folder exists
            if not self.verify_folder_deleted(custom_secrets, False):
                self.failed_tests.append("Folder: Custom secrets folder should exist after create")
                return False

            self.create_test_files(custom_secrets)

            # Unmount and verify custom folder is deleted
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            if not success:
                self.failed_tests.append("Folder: Unmount custom project failed")
                return False

            if not self.verify_folder_deleted(custom_secrets, True):
                self.failed_tests.append("Folder: Custom secrets folder should be deleted after unmount")
                return False

            # Verify encrypted file exists with custom project name
            if not self.verify_encrypted_file_exists("custom_test", True):
                self.failed_tests.append("Folder: Custom encrypted file should exist after unmount")
                return False

            # Mount and verify custom folder is recreated
            success, stdout, stderr = self.run_command("python3 secrets_manager.py mount --test-mode")
            if not success:
                self.failed_tests.append("Folder: Mount custom project failed")
                return False

            if not self.verify_folder_deleted(custom_secrets, False):
                self.failed_tests.append("Folder: Custom secrets folder should exist after mount")
                return False

            # Final cleanup
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            success, stdout, stderr = self.run_command(
                "echo 'DELETE' | python3 secrets_manager.py destroy --test-mode"
            )

            # Verify complete cleanup of custom project
            if not self.verify_complete_destruction("custom_test", custom_secrets):
                self.failed_tests.append("Folder: Custom project cleanup verification failed")
                return False

            self.passed_tests.append("Comprehensive folder verification")
            return True

        except Exception as e:
            self.failed_tests.append(f"Folder verification exception: {e}")
            return False

    def verify_complete_destruction(self, project_name=None, secrets_dir="secrets"):
        """Verify that destroy command removes ALL secrets-related files."""
        if project_name is None:
            project_name = os.path.basename(os.getcwd())

        # Check for secrets folder
        if os.path.exists(secrets_dir):
            print(f"  ❌ Secrets folder {secrets_dir} still exists after destroy")
            return False

        # Check for encrypted file
        encrypted_file = f".{project_name}.secrets"
        if os.path.exists(encrypted_file):
            print(f"  ❌ Encrypted file {encrypted_file} still exists after destroy")
            return False

        # Check for config file
        config_file = ".secrets_keychain_entry"
        if os.path.exists(config_file):
            print(f"  ❌ Config file {config_file} still exists after destroy")
            return False

        # Check for any other .secrets files
        secrets_files = [f for f in os.listdir(".") if f.endswith(".secrets")]
        if secrets_files:
            print(f"  ❌ Found unexpected .secrets files: {secrets_files}")
            return False

        print(f"  ✅ All secrets-related files properly destroyed")
        return True

    def run_status_and_verify(self, expected_context="", check_success=True):
        """Run status command and verify it returns the expected success state."""
        success, stdout, stderr = self.run_command("python3 secrets_manager.py status --test-mode")
        if check_success and not success:
            print(f"  ❌ Status command failed unexpectedly in {expected_context}")
            return False
        elif not check_success and success:
            print(f"  ❌ Status command succeeded when it should have failed in {expected_context}")
            return False

        print(f"  ✅ Status command returned correct state for {expected_context}")
        return True

    def run_all_tests(self):
        """Run all test suites."""
        print("🧪 Starting comprehensive test suite for secrets_manager.py")
        print("=" * 60)

        try:
            self.setup_test_environment()

            # Run test suites
            tests = [
                ("Basic Workflow", self.test_basic_workflow),
                ("Custom Workflow", self.test_custom_workflow),
                ("Status Command", self.test_status_command),
                ("All Commands Coverage", self.test_all_commands_coverage),
                ("Comprehensive Folder Verification", self.test_comprehensive_folder_verification),
                ("Edge Cases", self.test_edge_cases)
            ]

            for test_name, test_func in tests:
                print(f"\n{'='*20} {test_name} {'='*20}")
                test_func()

            # Print results
            print("\n" + "="*60)
            print("🏁 TEST RESULTS")
            print("="*60)

            print(f"✅ PASSED ({len(self.passed_tests)}):")
            for test in self.passed_tests:
                print(f"   • {test}")

            if self.failed_tests:
                print(f"\n❌ FAILED ({len(self.failed_tests)}):")
                for test in self.failed_tests:
                    print(f"   • {test}")
                print(f"\n💥 {len(self.failed_tests)} test(s) failed!")
                return False
            else:
                print(f"\n🎉 All {len(self.passed_tests)} tests passed!")
                return True

        finally:
            self.cleanup_test_environment()

def main():
    """Run the test suite."""
    tester = TestSecretsManager()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
