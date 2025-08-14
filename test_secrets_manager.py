#!/usr/bin/env python3
"""
Human-readable test suite for secrets_manager.py

This test suite is designed to read like a story, making it easy to understand
what functionality is being tested without getting lost in implementation details.

The test commands mirror exactly what users would type on the command line,
hiding technical details like python3, --test-mode, and input piping.
"""

import os
import sys
import shutil
import tempfile
import subprocess
import platform
from pathlib import Path

# Platform detection for Windows compatibility
def is_windows():
    return platform.system() == "Windows"

# Platform-aware emoji/symbols
if is_windows():
    # Windows-compatible symbols
    OK_MARK = "[OK]"
    ERROR_MARK = "[ERROR]"
    CHECK_MARK = "[CHECK]"
    DOC_MARK = "[STORY]"
    CMD_MARK = "[CMD]"
    FILE_MARK = "[FILE]"
    FOLDER_MARK = "[FOLDER]"
    EDIT_MARK = "[EDIT]"
    HOME_MARK = "[HOME]"
    BUILD_MARK = "[BUILD]"
    STATS_MARK = "[STATS]"
    WARN_MARK = "[WARN]"
else:
    # Unicode emoji for macOS/Linux
    OK_MARK = "✅"
    ERROR_MARK = "❌"
    CHECK_MARK = "🔍"
    DOC_MARK = "📖"
    CMD_MARK = "📝"
    FILE_MARK = "📄"
    FOLDER_MARK = "📁"
    EDIT_MARK = "✏️"
    HOME_MARK = "🏠"
    BUILD_MARK = "🏗️"
    STATS_MARK = "📊"
    WARN_MARK = "⚠️"

class SecretsManagerStory:
    """A story-driven test suite that reads like natural language."""

    def __init__(self):
        self.test_dir = None
        self.script_path = None
        self.failed_scenarios = []
        self.passed_scenarios = []

    def setup_testing_environment(self):
        """Prepare a clean testing environment."""
        print("🚀 Setting up a fresh testing environment...")

        self.test_dir = tempfile.mkdtemp(prefix="secrets_test_")
        print(f"📁 Working in: {self.test_dir}")

        current_script = Path(__file__).parent / "secrets_manager.py"
        self.script_path = Path(self.test_dir) / "secrets_manager.py"
        shutil.copy2(current_script, self.script_path)
        os.chmod(self.script_path, 0o755)
        os.chdir(self.test_dir)

        print(f"{OK_MARK} Environment ready")
        return self

    def cleanup_testing_environment(self):
        """Clean up the testing environment."""
        if self.test_dir and os.path.exists(self.test_dir):
            os.chdir(os.path.dirname(self.test_dir))
            shutil.rmtree(self.test_dir)
            print(f"🧹 Cleaned up: {self.test_dir}")

        # Clean up temporary files on Windows
        if hasattr(self, '_temp_files_to_cleanup'):
            for temp_file in self._temp_files_to_cleanup:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except:
                    pass  # Ignore cleanup errors

    def run(self, command_description, command, should_succeed=True):
        """Execute a command with readable description."""
        print(f"  {CMD_MARK} {command_description}")

        # Add debugging for Windows
        if is_windows():
            print(f"  [DEBUG] Full command: {command}")

        try:
            # Add timeout to prevent hanging and handle stdin properly
            if is_windows() and '|' not in command and '<' not in command:
                # For simple commands on Windows, explicitly set stdin to DEVNULL
                result = subprocess.run(command, shell=True, capture_output=True, text=True,
                                      timeout=30, stdin=subprocess.DEVNULL)
            else:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            print(f"  {ERROR_MARK} Command timed out after 30 seconds")
            return False

        if should_succeed and result.returncode != 0:
            print(f"  {ERROR_MARK} Expected success but failed: {result.stderr}")
            return False
        elif not should_succeed and result.returncode == 0:
            print(f"  {ERROR_MARK} Expected failure but succeeded")
            return False

        success_indicator = OK_MARK if should_succeed else WARN_MARK
        action = "succeeded" if result.returncode == 0 else "failed as expected"
        print(f"  {success_indicator} {action}")
        return True

    def cmd(self, command_str, input_data=None, should_succeed=True):
        """Execute a command showing only what the user would type."""
        # Platform-aware Python executable and input commands
        python_cmd = "python" if is_windows() else "python3"

        # Build the actual command with technical details hidden
        if input_data is None:
            full_command = f"{python_cmd} {command_str} --test-mode"
        elif isinstance(input_data, list):
            # Multiple inputs (like for change-password)
            input_string = '\\n'.join(input_data)
            if is_windows():
                # Windows: Use temporary file approach to avoid piping issues
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                    f.write(input_string.replace('\\n', '\n'))
                    temp_file = f.name
                full_command = f"{python_cmd} {command_str} --test-mode < {temp_file}"
                # Clean up temp file after execution
                self._temp_files_to_cleanup = getattr(self, '_temp_files_to_cleanup', [])
                self._temp_files_to_cleanup.append(temp_file)
            else:
                full_command = f"printf '{input_string}\\n' | {python_cmd} {command_str} --test-mode"
        else:
            # Single input
            if is_windows():
                # Windows: Use echo with proper escaping
                full_command = f"echo {input_data} | {python_cmd} {command_str} --test-mode"
            else:
                full_command = f"echo '{input_data}' | {python_cmd} {command_str} --test-mode"

        return self.run(command_str, full_command, should_succeed)

    def check_that(self, description, condition):
        """Perform a readable verification."""
        print(f"  {CHECK_MARK} Checking that {description}")
        if condition:
            print(f"  {OK_MARK} Confirmed")
            return True
        else:
            print(f"  {ERROR_MARK} Not verified")
            return False

    def create_sample_secrets(self, in_folder="secrets"):
        """Create sample secret files for testing."""
        print(f"  {FILE_MARK} Creating sample secrets in {in_folder}/")
        secrets_path = Path(in_folder)
        secrets_path.mkdir(exist_ok=True)

        (secrets_path / ".env").write_text("API_KEY=secret123\nDB_PASSWORD=dbpass456\n")
        (secrets_path / "private.key").write_text("-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----\n")
        (secrets_path / "config.json").write_text('{"secret": "value", "token": "abc123"}\n')

        ssl_dir = secrets_path / "ssl"
        ssl_dir.mkdir(exist_ok=True)
        (ssl_dir / "cert.pem").write_text("-----BEGIN CERTIFICATE-----\ntest_cert\n-----END CERTIFICATE-----\n")

        return self

    def modify_sample_secrets(self, in_folder="secrets"):
        """Modify existing secret files for testing."""
        print(f"  {EDIT_MARK} Modifying secrets in {in_folder}/")
        secrets_path = Path(in_folder)
        (secrets_path / ".env").write_text("API_KEY=updated_secret\nDB_PASSWORD=new_password\n")
        (secrets_path / "new_secret.txt").write_text("This is a new secret file\n")
        return self

    def folder_exists(self, folder_name):
        """Check if a folder exists."""
        return lambda: os.path.exists(folder_name)

    def folder_missing(self, folder_name):
        """Check if a folder is missing."""
        return lambda: not os.path.exists(folder_name)

    def encrypted_file_exists(self, project_name):
        """Check if encrypted file exists."""
        return lambda: os.path.exists(f".{project_name}.secrets")

    def encrypted_file_missing(self, project_name):
        """Check if encrypted file is missing."""
        return lambda: not os.path.exists(f".{project_name}.secrets")

    def files_have_expected_content(self, in_folder="secrets"):
        """Verify files contain expected content."""
        def check():
            try:
                secrets_path = Path(in_folder)
                env_content = (secrets_path / ".env").read_text()
                return "API_KEY=" in env_content and "DB_PASSWORD=" in env_content
            except:
                return False
        return check

    def files_have_modified_content(self, in_folder="secrets"):
        """Verify files contain modified content."""
        def check():
            try:
                secrets_path = Path(in_folder)
                env_content = (secrets_path / ".env").read_text()
                new_file_exists = (secrets_path / "new_secret.txt").exists()
                return "updated_secret" in env_content and new_file_exists
            except:
                return False
        return check

    def no_secrets_files_remain(self, project_name, secrets_folder="secrets"):
        """Verify complete cleanup after destroy."""
        def check():
            folder_gone = not os.path.exists(secrets_folder)
            encrypted_gone = not os.path.exists(f".{project_name}.secrets")
            keychain_gone = not os.path.exists(".secrets_keychain_entry")
            other_secrets_gone = len([f for f in os.listdir(".") if f.endswith(".secrets")]) == 0
            return folder_gone and encrypted_gone and keychain_gone and other_secrets_gone
        return check

    def scenario_passes(self, scenario_name):
        """Mark a scenario as passed."""
        self.passed_scenarios.append(scenario_name)
        print(f"{OK_MARK} Scenario passed: {scenario_name}")

    def scenario_fails(self, scenario_name, reason=""):
        """Mark a scenario as failed."""
        self.failed_scenarios.append(f"{scenario_name}: {reason}" if reason else scenario_name)
        print(f"{ERROR_MARK} Scenario failed: {scenario_name}")

    def tell_the_basic_user_story(self):
        """The main user journey through creating, using, and destroying secrets."""
        print(f"\n{DOC_MARK} Testing the basic user story...")

        all_steps_passed = True
        project_name = os.path.basename(os.getcwd())

        try:
            # Chapter 1: Creating secrets
            if not self.cmd("secrets_manager.py create", "test123"):
                all_steps_passed = False

            if not self.check_that("secrets folder is created", self.folder_exists("secrets")):
                all_steps_passed = False

            self.create_sample_secrets()

            # Chapter 2: Securing secrets
            if not self.cmd("secrets_manager.py unmount"):
                all_steps_passed = False

            if not self.check_that("secrets folder is hidden", self.folder_missing("secrets")):
                all_steps_passed = False

            if not self.check_that("encrypted file is created", self.encrypted_file_exists(project_name)):
                all_steps_passed = False

            # Chapter 3: Accessing secrets again
            if not self.cmd("secrets_manager.py mount"):
                all_steps_passed = False

            if not self.check_that("secrets folder reappears", self.folder_exists("secrets")):
                all_steps_passed = False

            if not self.check_that("files have original content", self.files_have_expected_content()):
                all_steps_passed = False

            # Chapter 4: Modifying secrets
            self.modify_sample_secrets()

            if not self.cmd("secrets_manager.py unmount"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py mount"):
                all_steps_passed = False

            if not self.check_that("modifications are preserved", self.files_have_modified_content()):
                all_steps_passed = False

            # Chapter 5: Password management
            if not self.cmd("secrets_manager.py clear"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py unmount", should_succeed=False):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py pass", "test123"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py mount"):
                all_steps_passed = False

            # Chapter 6: Clean destruction
            if not self.cmd("secrets_manager.py unmount"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py destroy", "DELETE"):
                all_steps_passed = False

            if not self.check_that("all secrets are completely removed", self.no_secrets_files_remain(project_name)):
                all_steps_passed = False

            if all_steps_passed:
                self.scenario_passes("Basic user story")
            else:
                self.scenario_fails("Basic user story", "One or more steps failed")

        except Exception as e:
            self.scenario_fails("Basic user story", f"Exception: {e}")
            all_steps_passed = False

        return all_steps_passed

    def tell_the_custom_configuration_story(self):
        """User story with custom project names and folder locations."""
        print(f"\n{DOC_MARK} Testing custom configuration story...")

        all_steps_passed = True
        custom_project = "my_secret_project"
        custom_folder = ".private_files"

        try:
            # User wants custom names for their project
            if not self.cmd("secrets_manager.py create --project my_secret_project --secrets-dir .private_files", "test123"):
                all_steps_passed = False

            if not self.check_that(f"custom folder '{custom_folder}' is created", self.folder_exists(custom_folder)):
                all_steps_passed = False

            self.create_sample_secrets(custom_folder)

            if not self.cmd("secrets_manager.py unmount"):
                all_steps_passed = False

            if not self.check_that(f"custom folder '{custom_folder}' is hidden", self.folder_missing(custom_folder)):
                all_steps_passed = False

            if not self.check_that(f"custom encrypted file is created", self.encrypted_file_exists(custom_project)):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py mount"):
                all_steps_passed = False

            if not self.check_that(f"custom folder '{custom_folder}' reappears", self.folder_exists(custom_folder)):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py change-password", ["newpass456", "newpass456"]):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py unmount"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py mount"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py unmount"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py destroy", "DELETE"):
                all_steps_passed = False

            if not self.check_that("all custom files are removed", self.no_secrets_files_remain(custom_project, custom_folder)):
                all_steps_passed = False

            if all_steps_passed:
                self.scenario_passes("Custom configuration story")
            else:
                self.scenario_fails("Custom configuration story", "One or more steps failed")

        except Exception as e:
            self.scenario_fails("Custom configuration story", f"Exception: {e}")
            all_steps_passed = False

        return all_steps_passed

    def tell_the_status_monitoring_story(self):
        """User story about checking vault status at various points."""
        print(f"\n{DOC_MARK} Testing status monitoring story...")

        all_steps_passed = True

        try:
            # User checks status when nothing exists
            if not self.cmd("secrets_manager.py status"):
                all_steps_passed = False

            # User creates vault and checks status
            if not self.cmd("secrets_manager.py create", "test123"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py status"):
                all_steps_passed = False

            self.create_sample_secrets()

            # User secures vault and checks status
            if not self.cmd("secrets_manager.py unmount"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py status"):
                all_steps_passed = False

            # User accesses vault and checks status
            if not self.cmd("secrets_manager.py mount"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py status"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py unmount"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py destroy", "DELETE"):
                all_steps_passed = False

            if all_steps_passed:
                self.scenario_passes("Status monitoring story")
            else:
                self.scenario_fails("Status monitoring story", "One or more steps failed")

        except Exception as e:
            self.scenario_fails("Status monitoring story", f"Exception: {e}")
            all_steps_passed = False

        return all_steps_passed

    def tell_the_error_handling_story(self):
        """User story about what happens when things go wrong."""
        print(f"\n{DOC_MARK} Testing error handling story...")

        all_steps_passed = True

        try:
            # User tries to access non-existent vault
            if not self.cmd("secrets_manager.py mount", should_succeed=False):
                all_steps_passed = False

            # User tries to unmount when nothing is mounted
            if not self.cmd("secrets_manager.py unmount"):
                all_steps_passed = False

            # User creates vault successfully
            if not self.cmd("secrets_manager.py create", "test123"):
                all_steps_passed = False

            self.create_sample_secrets()

            if not self.cmd("secrets_manager.py unmount"):
                all_steps_passed = False

            # User tries to create vault again (should fail)
            if not self.cmd("secrets_manager.py create", "test123", should_succeed=False):
                all_steps_passed = False

            project_name = os.path.basename(os.getcwd())
            if not self.cmd("secrets_manager.py destroy", "DELETE"):
                all_steps_passed = False

            if all_steps_passed:
                self.scenario_passes("Error handling story")
            else:
                self.scenario_fails("Error handling story", "One or more steps failed")

        except Exception as e:
            self.scenario_fails("Error handling story", f"Exception: {e}")
            all_steps_passed = False

        return all_steps_passed

    def tell_the_comprehensive_command_story(self):
        """Verify every single command works in isolation."""
        print(f"\n{DOC_MARK} Testing comprehensive command coverage...")

        all_steps_passed = True
        project_name = os.path.basename(os.getcwd())

        try:
            if not self.cmd("secrets_manager.py status"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py create", "test123"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py status"):
                all_steps_passed = False

            self.create_sample_secrets()

            if not self.cmd("secrets_manager.py unmount"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py status"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py mount"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py clear"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py pass", "test123"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py unmount"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py change-password", ["newpass456", "newpass456"]):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py destroy", "DELETE"):
                all_steps_passed = False

            if not self.check_that("everything is cleaned up", self.no_secrets_files_remain(project_name)):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py status"):
                all_steps_passed = False

            if all_steps_passed:
                self.scenario_passes("Comprehensive command coverage")
            else:
                self.scenario_fails("Comprehensive command coverage", "One or more commands failed")

        except Exception as e:
            self.scenario_fails("Comprehensive command coverage", f"Exception: {e}")
            all_steps_passed = False

        return all_steps_passed

    def tell_the_folder_verification_story(self):
        """Test with various folder names and configurations."""
        print(f"\n{DOC_MARK} Testing folder management story...")

        all_steps_passed = True

        try:
            print(f"  {HOME_MARK} Testing default folder behavior...")
            project_name = os.path.basename(os.getcwd())

            if not self.cmd("secrets_manager.py create", "test123"):
                all_steps_passed = False

            if not self.check_that("default secrets folder exists", self.folder_exists("secrets")):
                all_steps_passed = False

            self.create_sample_secrets()

            if not self.cmd("secrets_manager.py unmount"):
                all_steps_passed = False

            if not self.check_that("default folder disappears", self.folder_missing("secrets")):
                all_steps_passed = False

            if not self.check_that("default encrypted file appears", self.encrypted_file_exists(project_name)):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py mount"):
                all_steps_passed = False

            if not self.check_that("default folder reappears", self.folder_exists("secrets")):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py unmount"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py destroy", "DELETE"):
                all_steps_passed = False

            if not self.check_that("default files are gone", self.no_secrets_files_remain(project_name)):
                all_steps_passed = False

            print(f"  {BUILD_MARK} Testing custom folder behavior...")
            custom_project = "test_custom"
            custom_folder = "my_special_secrets"

            if not self.cmd(f"secrets_manager.py create --project {custom_project} --secrets-dir {custom_folder}", "test123"):
                all_steps_passed = False

            if not self.check_that(f"custom folder '{custom_folder}' exists", self.folder_exists(custom_folder)):
                all_steps_passed = False

            self.create_sample_secrets(custom_folder)

            if not self.cmd("secrets_manager.py unmount"):
                all_steps_passed = False

            if not self.check_that(f"custom folder '{custom_folder}' disappears", self.folder_missing(custom_folder)):
                all_steps_passed = False

            if not self.check_that("custom encrypted file appears", self.encrypted_file_exists(custom_project)):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py mount"):
                all_steps_passed = False

            if not self.check_that(f"custom folder '{custom_folder}' reappears", self.folder_exists(custom_folder)):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py unmount"):
                all_steps_passed = False

            if not self.cmd("secrets_manager.py destroy", "DELETE"):
                all_steps_passed = False

            if not self.check_that("custom files are gone", self.no_secrets_files_remain(custom_project, custom_folder)):
                all_steps_passed = False

            if all_steps_passed:
                self.scenario_passes("Folder management story")
            else:
                self.scenario_fails("Folder management story", "One or more folder operations failed")

        except Exception as e:
            self.scenario_fails("Folder management story", f"Exception: {e}")
            all_steps_passed = False

        return all_steps_passed

    def tell_all_stories(self):
        """Run through all the user stories."""
        print("📚 Telling all the secrets manager stories...")
        print("=" * 60)

        try:
            self.setup_testing_environment()

            stories = [
                ("Basic User Journey", self.tell_the_basic_user_story),
                ("Custom Configuration", self.tell_the_custom_configuration_story),
                ("Status Monitoring", self.tell_the_status_monitoring_story),
                ("Error Handling", self.tell_the_error_handling_story),
                ("Comprehensive Command Coverage", self.tell_the_comprehensive_command_story),
                ("Folder Management", self.tell_the_folder_verification_story),
            ]

            for story_name, story_func in stories:
                print(f"\n{'='*20} {story_name} {'='*20}")
                story_func()

            # Show results
            print("\n" + "="*60)
            print("📋 STORY RESULTS")
            print("="*60)

            print(f"✅ SUCCESSFUL STORIES ({len(self.passed_scenarios)}):")
            for scenario in self.passed_scenarios:
                print(f"   📖 {scenario}")

            if self.failed_scenarios:
                print(f"\n❌ FAILED STORIES ({len(self.failed_scenarios)}):")
                for scenario in self.failed_scenarios:
                    print(f"   📖 {scenario}")
                print(f"\n💥 {len(self.failed_scenarios)} story/stories had issues!")
                return False
            else:
                print(f"\n🎉 All {len(self.passed_scenarios)} stories completed successfully!")
                return True

        finally:
            self.cleanup_testing_environment()

def main():
    """Tell all the secrets manager stories."""
    storyteller = SecretsManagerStory()
    success = storyteller.tell_all_stories()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
