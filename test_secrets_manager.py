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

            # 2. Add test files
            self.create_test_files("secrets")

            # 3. Unmount (encrypt)
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            if not success:
                self.failed_tests.append("Basic: Unmount failed")
                return False

            # 4. Verify secrets folder is gone and encrypted file exists
            if os.path.exists("secrets"):
                self.failed_tests.append("Basic: Secrets folder still exists after unmount")
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

            # 12. Unmount (should fail due to no password)
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            if not os.path.exists("secrets"):
                # If secrets folder was removed, mount should fail
                success, stdout, stderr = self.run_command("python3 secrets_manager.py mount --test-mode", expect_failure=True)
                if not success:
                    self.failed_tests.append("Basic: Mount should have failed without password")
                    return False

            # 13. Reinstate password
            success, stdout, stderr = self.run_command(
                f"echo '{TEST_PASSWORD}' | python3 secrets_manager.py pass --test-mode"
            )
            if not success:
                self.failed_tests.append("Basic: Reinstate password failed")
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

            # 17. Verify everything is cleaned up
            if os.path.exists("secrets") or os.path.exists(".secrets_keychain_entry"):
                self.failed_tests.append("Basic: Project not fully destroyed")
                return False

            encrypted_files = [f for f in os.listdir(".") if f.endswith(".secrets")]
            if encrypted_files:
                self.failed_tests.append("Basic: Encrypted files not removed by destroy")
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

            # 2. Add test files
            self.create_test_files(CUSTOM_SECRETS_DIR)

            # 3. Unmount (should auto-detect project and secrets dir)
            success, stdout, stderr = self.run_command("python3 secrets_manager.py unmount --test-mode")
            if not success:
                self.failed_tests.append("Custom: Unmount failed")
                return False

            # 4. Verify encrypted file uses custom project name
            encrypted_file = f".{CUSTOM_PROJECT}.secrets"
            if not os.path.exists(encrypted_file):
                self.failed_tests.append(f"Custom: Encrypted file {encrypted_file} not found")
                return False

            # 5. Mount (should auto-detect)
            success, stdout, stderr = self.run_command("python3 secrets_manager.py mount --test-mode")
            if not success:
                self.failed_tests.append("Custom: Mount failed")
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

            self.passed_tests.append("Edge cases")
            return True

        except Exception as e:
            self.failed_tests.append(f"Edge cases exception: {e}")
            return False

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
