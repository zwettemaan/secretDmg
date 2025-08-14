#!/usr/bin/env php
<?php
/**
 * PHP Secrets Manager CLI Tool
 * Command-line interface equivalent to secrets_manager.py
 *
 * This is the user-facing CLI tool that provides the same functionality
 * as the Python secrets_manager.py tool, but implemented in PHP.
 */

require_once __DIR__ . '/SecretsManagerLib.php';

class SecretsManagerCLI {
    private $projectDir;
    private $projectName;
    private $secretsFile;

    public function __construct() {
        $this->projectDir = getcwd();
        $this->projectName = $this->detectProjectName();
        $this->secretsFile = $this->projectDir . '/.' . $this->projectName . '.secrets';
    }

    private function detectProjectName() {
        // First, look for existing .*.secrets files
        $files = glob($this->projectDir . '/.*.secrets');
        if (!empty($files)) {
            $filename = basename($files[0]);
            return substr($filename, 1, -8); // Remove leading '.' and trailing '.secrets'
        }

        // Fallback to directory name
        return basename($this->projectDir);
    }

    public function run($args) {
        if (count($args) < 2) {
            $this->showUsage();
            return 1;
        }

        $command = $args[1];

        // Parse global options
        $options = $this->parseOptions(array_slice($args, 2));

        switch ($command) {
            case 'create':
                return $this->createCommand($options);
            case 'mount':
                return $this->mountCommand($options);
            case 'unmount':
                return $this->unmountCommand($options);
            case 'pass':
                return $this->passCommand($options);
            case 'clear':
                return $this->clearCommand($options);
            case 'change-password':
                return $this->changePasswordCommand($options);
            case 'destroy':
                return $this->destroyCommand($options);
            case 'status':
                return $this->statusCommand($options);
            case 'read':
                return $this->readCommand($options);
            case 'list':
                return $this->listCommand($options);
            case 'exists':
                return $this->existsCommand($options);
            case 'env':
                return $this->envCommand($options);
            case 'info':
                return $this->infoCommand($options);
            case 'help':
            case '--help':
            case '-h':
                $this->showUsage();
                return 0;
            default:
                echo "❌ Unknown command: $command\n";
                $this->showUsage();
                return 1;
        }
    }

    private function parseOptions($args) {
        $options = [
            'project' => null,
            'secrets-dir' => null,
            'password' => null,
            'test-mode' => false,
            'verbose' => false,
            'files' => []
        ];

        for ($i = 0; $i < count($args); $i++) {
            $arg = $args[$i];

            if ($arg === '--project' && isset($args[$i + 1])) {
                $options['project'] = $args[++$i];
            } elseif ($arg === '--secrets-dir' && isset($args[$i + 1])) {
                $options['secrets-dir'] = $args[++$i];
            } elseif ($arg === '--password' && isset($args[$i + 1])) {
                $options['password'] = $args[++$i];
            } elseif ($arg === '--test-mode') {
                $options['test-mode'] = true;
            } elseif ($arg === '--verbose' || $arg === '-v') {
                $options['verbose'] = true;
            } elseif (!$this->startsWith($arg, '--')) {
                $options['files'][] = $arg;
            }
        }

        return $options;
    }

    private function showUsage() {
        echo "📦 Secrets Manager CLI (PHP)\n\n";
        echo "Usage: php secrets_manager.php <command> [options]\n\n";
        echo "Commands:\n";
        echo "  create                       Create secrets from current directory\n";
        echo "  mount                        Mount secrets (displays read instructions)\n";
        echo "  unmount                      Unmount secrets (no-op)\n";
        echo "  pass                         Store password in credential store\n";
        echo "  clear                        Remove stored password\n";
        echo "  change-password             Change project password\n";
        echo "  destroy                     Delete secrets file\n";
        echo "  status                      Show project status\n";
        echo "  read <file_path>            Read a specific file from secrets\n";
        echo "  list                        List all files in secrets\n";
        echo "  exists <file_path>          Check if a file exists in secrets\n";
        echo "  env [file_path]             Parse and display environment variables\n";
        echo "  info                        Show metadata about secrets package\n";
        echo "  help                        Show this help message\n\n";
        echo "Options:\n";
        echo "  --project PROJECT           Project name (only used with 'create')\n";
        echo "  --secrets-dir SECRETS_DIR   Secrets directory name (only used with 'create')\n";
        echo "  --password PASSWORD         Password (only used with 'create' and 'pass')\n";
        echo "  --test-mode                 Test mode: read passwords from stdin\n";
        echo "  --verbose, -v               Verbose logging\n\n";
        echo "Examples:\n";
        echo "  php secrets_manager.php create\n";
        echo "  php secrets_manager.php create --project myapp\n";
        echo "  php secrets_manager.php mount\n";
        echo "  php secrets_manager.php read .env\n";
        echo "  php secrets_manager.php pass --password mypass\n";
        echo "  php secrets_manager.php status\n";
    }

    private function createCommand($options) {
        $projectName = $options['project'] ?: $this->projectName;
        $secretsDir = $options['secrets-dir'] ?: 'secrets';
        $password = $options['password'];

        echo "🚀 Using project: $projectName\n";

        $secretsFile = $this->projectDir . '/.' . $projectName . '.secrets';

        // Check if encrypted file already exists
        if (file_exists($secretsFile)) {
            echo "❌ $secretsFile already exists!\n";
            echo "💡 Use 'mount' to decrypt existing secrets, or delete the file first\n";
            return 1;
        }

        // Check if secrets folder already exists
        if (is_dir($secretsDir)) {
            echo "✅ Found existing $secretsDir/ folder\n";

            if ($options['test-mode']) {
                $response = 'y';
                echo "Encrypt existing folder contents? (y/n): y\n";
            } else {
                echo "Encrypt existing folder contents? (y/n): ";
                $response = trim(fgets(STDIN));
            }

            if (strtolower($response) !== 'y' && strtolower($response) !== 'yes') {
                echo "❌ Cannot create - secrets folder exists but not encrypting\n";
                return 1;
            }

            echo "❌ Encrypting existing folder not yet implemented in PHP version.\n";
            echo "💡 Use the Python version for this: python secrets_manager.py create\n";
            return 1;
        }

        // Create new empty secrets folder
        try {
            echo "📁 Creating empty $secretsDir/ folder...\n";

            if (!mkdir($secretsDir, 0755, true)) {
                throw new Exception("Failed to create directory: $secretsDir");
            }

            // Get password for future use
            if (!$password) {
                if ($options['test-mode']) {
                    $password = 'test123';
                    echo "Enter password for this project: test123\n";
                } else {
                    echo "Enter password for this project: ";
                    system('stty -echo');
                    $password = trim(fgets(STDIN));
                    system('stty echo');
                    echo "\n";
                }

                if (!$password) {
                    echo "❌ Password required for project setup\n";
                    rmdir($secretsDir);
                    return 1;
                }
            }

            // Store password in credential store
            if ($this->storePassword($projectName, $password)) {
                echo "🔑 Password stored in credential store\n";
            } else {
                echo "⚠️  Warning: Could not store password in credential store\n";
            }

            // Add to .gitignore
            $this->addToGitignore($secretsDir . '/');

            // Create helpful README
            $readmePath = $secretsDir . '/README.txt';
            $readmeContent = "Put your secret files here:\n";
            $readmeContent .= "- .env files\n";
            $readmeContent .= "- SSL certificates (.pem, .key)\n";
            $readmeContent .= "- API keys\n";
            $readmeContent .= "- Database passwords\n";
            $readmeContent .= "- Any other sensitive files\n\n";
            $readmeContent .= "When done, run: php secrets_manager.php unmount\n";

            if (file_put_contents($readmePath, $readmeContent) === false) {
                throw new Exception("Failed to create README.txt");
            }

            // Save project configuration
            $this->saveProjectConfig($projectName, $secretsDir);

            echo "✅ Created empty $secretsDir/ folder\n";
            echo "✅ Added $secretsDir/ to .gitignore\n";
            echo "💡 Add your secret files to $secretsDir/ then run:\n";
            echo "   php secrets_manager.php unmount\n";

            return 0;

        } catch (Exception $e) {
            echo "❌ Failed to create secrets folder: " . $e->getMessage() . "\n";
            return 1;
        }
    }

    private function mountCommand($options) {
        try {
            $manager = new SecretsManager($this->projectDir, $options['password']);
            $files = $manager->listFiles();

            if (empty($files)) {
                echo "❌ No secrets found to mount\n";
                return 1;
            }

            echo "📁 Secrets mounted (read-only access via PHP library)\n";
            echo "📂 Available files:\n";
            foreach ($files as $file) {
                echo "  📄 $file\n";
            }
            echo "💡 Use 'php secrets_manager.php read <file>' to access files\n";

            return 0;

        } catch (Exception $e) {
            echo "❌ Error mounting secrets: " . $e->getMessage() . "\n";
            return 1;
        }
    }

    private function unmountCommand($options) {
        // Check if there's anything to unmount (like Python version)
        if (!is_dir('secrets')) {
            echo "ℹ️  No secrets folder to unmount\n";
            return 0;  // Success, like Python version
        }

        // Standard unmount: encrypt secrets directory
        return $this->performUnmount($options);
    }

    private function performUnmount($options) {
        if (!is_dir('secrets')) {
            echo "❌ No secrets/ directory found
";
            echo "� Run 'php secrets_manager.php create' first
";
            return 1;
        }

        // Count files in secrets directory
        $files = $this->getFilesRecursively('secrets');
        $files = array_filter($files, function($file) {
            return basename($file) !== 'secrets_manager.hash';
        });

        if (empty($files)) {
            echo "❌ No files found in secrets/ directory
";
            echo "💡 Add some files to secrets/ first
";
            return 1;
        }

        echo "🔒 Encrypting " . count($files) . " files...
";

        // Get password
        $password = null;
        if ($options['test-mode']) {
            $password = 'test123';
        } else {
            // Try to get stored password first
            $manager = new SecretsManager($this->projectDir);
            $password = $manager->getStoredPassword();

            if (!$password) {
                echo "Enter password to encrypt secrets: ";
                system('stty -echo');
                $password = trim(fgets(STDIN));
                system('stty echo');
                echo "
";
            }
        }

        if (!$password) {
            echo "❌ Password required to encrypt secrets
";
            return 1;
        }

        try {
            if ($this->encryptSecretsFolder($password, $files)) {
                echo "✅ Secrets encrypted to {$this->secretsFile}
";

                // Remove secrets directory
                $this->removeDirectory('secrets');
                echo "✅ Secrets unmounted\n\n";

                echo "💡 The encrypted file is safe to commit to git:
";
                echo "   git add {$this->secretsFile}
";
                echo "   git commit -m 'Update encrypted secrets'
";

                return 0;
            } else {
                echo "❌ Failed to encrypt secrets
";
                return 1;
            }

        } catch (Exception $e) {
            echo "❌ Error encrypting secrets: " . $e->getMessage() . "
";
            return 1;
        }
    }

    private function passCommand($options) {
        if (!$options['password']) {
            if ($options['test-mode']) {
                // In test mode, read from stdin
                $options['password'] = trim(fgets(STDIN));
            } else {
                echo "Enter password to store: ";
                system('stty -echo');
                $password = trim(fgets(STDIN));
                system('stty echo');
                echo "\n";
                $options['password'] = $password;
            }
        }

        if (!$options['password']) {
            echo "❌ Password required\n";
            return 1;
        }

        try {
            $serviceName = "secretdmg-{$this->projectName}";
            $success = $this->storePassword($serviceName, $options['password']);

            if ($success) {
                echo "✅ Password stored successfully\n";
                return 0;
            } else {
                echo "❌ Failed to store password\n";
                return 1;
            }

        } catch (Exception $e) {
            echo "❌ Error storing password: " . $e->getMessage() . "\n";
            return 1;
        }
    }

    private function clearCommand($options) {
        try {
            $serviceName = "secretdmg-{$this->projectName}";
            $success = $this->removeStoredPassword($serviceName);

            if ($success) {
                echo "✅ Stored password cleared\n";
                return 0;
            } else {
                echo "❌ No stored password found to clear\n";
                return 1;
            }

        } catch (Exception $e) {
            echo "❌ Error clearing password: " . $e->getMessage() . "\n";
            return 1;
        }
    }

    private function changePasswordCommand($options) {
        echo "❌ Change password command not implemented in PHP version.\n";
        echo "💡 Use the Python version: python secrets_manager.py change-password\n";
        return 1;
    }

    private function destroyCommand($options) {
        try {
            if (file_exists($this->secretsFile)) {
                if (!$options['test-mode']) {
                    echo "⚠️  This will permanently delete all secrets for project '{$this->projectName}'\n";
                    echo "Type 'yes' to confirm: ";
                    $confirmation = trim(fgets(STDIN));
                    if ($confirmation !== 'yes') {
                        echo "❌ Operation cancelled\n";
                        return 1;
                    }
                }

                unlink($this->secretsFile);
                echo "✅ Secrets destroyed permanently\n";

                // Also clear stored password
                $serviceName = "secretdmg-{$this->projectName}";
                $this->removeStoredPassword($serviceName);

                return 0;
            } else {
                echo "❌ No secrets file found: {$this->secretsFile}\n";
                return 1;
            }

        } catch (Exception $e) {
            echo "❌ Error destroying secrets: " . $e->getMessage() . "\n";
            return 1;
        }
    }

    private function statusCommand($options) {
        try {
            echo "📊 Project Status: {$this->projectName}\n";
            echo "📁 Project directory: {$this->projectDir}\n";
            echo "📄 Secrets file: {$this->secretsFile}\n";

            if (!file_exists($this->secretsFile)) {
                echo "❌ Status: No secrets found\n";
                echo "💡 No secrets found. Create secrets using: python secrets_manager.py create\n";
                return 1;
            }

            $manager = new SecretsManager($this->projectDir);
            $metadata = $manager->getMetadata();
            $files = $manager->listFiles();

            echo "✅ Status: Secrets available\n";

            if ($metadata && isset($metadata['created'])) {
                echo "📅 Created: {$metadata['created']}\n";
            }
            if ($metadata && isset($metadata['version'])) {
                echo "🔢 Version: {$metadata['version']}\n";
            }

            echo "📊 Total files: " . count($files) . "\n";

            // Check if password is stored
            $serviceName = "secretdmg-{$this->projectName}";
            $hasStoredPassword = $this->hasStoredPassword($serviceName);

            if ($hasStoredPassword) {
                echo "🔑 Password: Stored in credential store\n";
            } else {
                echo "🔑 Password: Not stored (will prompt when needed)\n";
            }

            return 0;

        } catch (Exception $e) {
            echo "❌ Error checking status: " . $e->getMessage() . "\n";
            return 1;
        }
    }

    private function readCommand($options) {
        if (empty($options['files'])) {
            echo "❌ File path required for read command\n";
            echo "Usage: php secrets_manager.php read <file_path>\n";
            return 1;
        }

        $filePath = $options['files'][0];

        try {
            $password = $options['password'];
            if (!$password && $options['test-mode']) {
                $password = 'test123';
            }

            $manager = new SecretsManager($this->projectDir, $password);
            $content = $manager->readSecrets($filePath);

            if ($content === false) {
                echo "❌ File not found in secrets: $filePath\n";
                return 1;
            }

            echo $content;
            return 0;

        } catch (Exception $e) {
            echo "❌ Error: " . $e->getMessage() . "\n";
            return 1;
        }
    }

    private function listCommand($options) {
        try {
            $password = $options['password'];
            if (!$password && $options['test-mode']) {
                $password = 'test123';
            }

            $manager = new SecretsManager($this->projectDir, $password);
            $files = $manager->listFiles();

            if (empty($files)) {
                echo "📂 No files found in secrets\n";
                return 0;
            }

            echo "📂 Files in secrets package:\n";
            foreach ($files as $file) {
                echo "  📄 $file\n";
            }

            return 0;

        } catch (Exception $e) {
            echo "❌ Error: " . $e->getMessage() . "\n";
            return 1;
        }
    }

    private function existsCommand($options) {
        if (empty($options['files'])) {
            echo "❌ File path required for exists command\n";
            echo "Usage: php secrets_manager.php exists <file_path>\n";
            return 1;
        }

        $filePath = $options['files'][0];

        try {
            $manager = new SecretsManager($this->projectDir, $options['password']);
            $exists = $manager->fileExists($filePath);

            if ($exists) {
                echo "✅ File exists in secrets: $filePath\n";
                return 0;
            } else {
                echo "❌ File not found in secrets: $filePath\n";
                return 1;
            }

        } catch (Exception $e) {
            echo "❌ Error: " . $e->getMessage() . "\n";
            return 1;
        }
    }

    private function envCommand($options) {
        $envFile = empty($options['files']) ? '.env' : $options['files'][0];

        try {
            $manager = new SecretsManager($this->projectDir, $options['password']);
            $envVars = $manager->readEnvFile($envFile);

            if ($envVars === false) {
                echo "❌ Environment file not found in secrets: $envFile\n";
                return 1;
            }

            if (empty($envVars)) {
                echo "📄 Environment file is empty: $envFile\n";
                return 0;
            }

            echo "🌍 Environment variables from $envFile:\n";
            foreach ($envVars as $key => $value) {
                // Hide sensitive values
                if (stripos($key, 'password') !== false ||
                    stripos($key, 'secret') !== false ||
                    stripos($key, 'key') !== false ||
                    stripos($key, 'token') !== false) {
                    echo "  $key=***HIDDEN***\n";
                } else {
                    echo "  $key=$value\n";
                }
            }

            return 0;

        } catch (Exception $e) {
            echo "❌ Error: " . $e->getMessage() . "\n";
            return 1;
        }
    }

    private function infoCommand($options) {
        try {
            $manager = new SecretsManager($this->projectDir, $options['password']);
            $metadata = $manager->getMetadata();

            if ($metadata === false) {
                echo "❌ Could not retrieve metadata\n";
                return 1;
            }

            echo "📊 Secrets Package Information:\n";
            echo "  📦 Project: {$this->projectName}\n";
            echo "  📁 Secrets file: {$this->secretsFile}\n";

            if (isset($metadata['created'])) {
                echo "  📅 Created: {$metadata['created']}\n";
            }
            if (isset($metadata['version'])) {
                echo "  🔢 Version: {$metadata['version']}\n";
            }
            if (isset($metadata['file_count'])) {
                echo "  📄 File count: {$metadata['file_count']}\n";
            }

            $files = $manager->listFiles();
            echo "  📊 Total files: " . count($files) . "\n";

            return 0;

        } catch (Exception $e) {
            echo "❌ Error: " . $e->getMessage() . "\n";
            return 1;
        }
    }

    /**
     * Store password in platform-specific credential store
     */
    private function storePassword($serviceName, $password) {
        try {
            $os = $this->detectOS();

            if ($os === 'darwin') {
                // macOS - use security command, with fallback to file storage
                $username = $this->getCurrentUser();

                // First try to delete existing entry (ignore errors)
                $deleteCommand = sprintf(
                    'security delete-generic-password -s %s -a %s 2>/dev/null',
                    escapeshellarg($serviceName),
                    escapeshellarg($username)
                );
                shell_exec($deleteCommand);

                // Now add the new entry
                $command = sprintf(
                    'security add-generic-password -s %s -a %s -w %s 2>/dev/null',
                    escapeshellarg($serviceName),
                    escapeshellarg($username),
                    escapeshellarg($password)
                );

                $output = shell_exec($command);
                $exitCode = $this->getCommandExitCode();

                if ($exitCode === 0) {
                    return true;
                }

                // Fallback to file storage on macOS if keychain fails
                return $this->storePasswordInFile($serviceName, $password);

            } elseif ($os === 'windows') {
                // Windows - simplified credential storage
                $command = sprintf(
                    'cmdkey /generic:%s /user:%s /pass:%s 2>nul',
                    escapeshellarg($serviceName),
                    escapeshellarg($this->getCurrentUser()),
                    escapeshellarg($password)
                );

                $result = shell_exec($command);
                $exitCode = $this->getCommandExitCode();

                if ($exitCode === 0) {
                    return true;
                }

                // Fallback to file storage on Windows if cmdkey fails
                return $this->storePasswordInFile($serviceName, $password);

            } else {
                // Linux - always use file storage
                return $this->storePasswordInFile($serviceName, $password);
            }

        } catch (Exception $e) {
            // Always fallback to file storage if anything fails
            return $this->storePasswordInFile($serviceName, $password);
        }
    }

    private function storePasswordInFile($serviceName, $password) {
        try {
            $username = $this->getCurrentUser();
            $credFile = $_SERVER['HOME'] . '/.' . $serviceName;

            $salt = random_bytes(32);
            $key = $this->deriveKey($username, $salt);
            $encryptedPassword = $this->encryptData($password, $key);

            $success = file_put_contents($credFile, $salt . $encryptedPassword) !== false;
            if ($success) {
                chmod($credFile, 0600); // Secure permissions
            }
            return $success;
        } catch (Exception $e) {
            return false;
        }
    }

    private function getCommandExitCode() {
        // Get the exit code of the last command
        $exitCode = 0;
        exec('echo $?', $output, $exitCode);
        return $exitCode;
                return $success;
            }

        } catch (Exception $e) {
            error_log("Could not store password: " . $e->getMessage());
            return false;
        }
    }

    /**
     * Remove stored password from credential store
     */
    private function removeStoredPassword($serviceName) {
        try {
            $os = $this->detectOS();

            if ($os === 'darwin') {
                // macOS - use security command
                $username = $this->getCurrentUser();
                $command = sprintf(
                    'security delete-generic-password -s %s -a %s 2>/dev/null',
                    escapeshellarg($serviceName),
                    escapeshellarg($username)
                );

                $result = shell_exec($command);
                return $result !== null;

            } elseif ($os === 'windows') {
                // Windows - use PowerShell to remove from Credential Manager
                $command = sprintf(
                    'powershell -Command "try { cmdkey /delete:%s } catch { exit 1 }"',
                    escapeshellarg($serviceName)
                );

                $result = shell_exec($command . ' 2>nul');
                return $result !== null;

            } else {
                // Linux - remove encrypted file
                $credFile = $_SERVER['HOME'] . '/.' . $serviceName;

                if (file_exists($credFile)) {
                    return unlink($credFile);
                }
                return false;
            }

        } catch (Exception $e) {
            error_log("Could not remove stored password: " . $e->getMessage());
            return false;
        }
    }

    /**
     * Check if password is stored
     */
    private function hasStoredPassword($serviceName) {
        try {
            $os = $this->detectOS();

            if ($os === 'darwin') {
                // macOS - use security command
                $username = $this->getCurrentUser();
                $command = sprintf(
                    'security find-generic-password -s %s -a %s 2>/dev/null',
                    escapeshellarg($serviceName),
                    escapeshellarg($username)
                );

                $result = shell_exec($command);
                return $result !== null && trim($result) !== '';

            } elseif ($os === 'windows') {
                // Windows - use PowerShell to check Credential Manager
                $command = sprintf(
                    'powershell -Command "try { cmdkey /list:%s | Out-Null; $true } catch { $false }"',
                    escapeshellarg($serviceName)
                );

                $result = shell_exec($command . ' 2>nul');
                return trim($result) === 'True';

            } else {
                // Linux - check for encrypted file
                $credFile = $_SERVER['HOME'] . '/.' . $serviceName;
                return file_exists($credFile);
            }

        } catch (Exception $e) {
            return false;
        }
    }

    /**
     * Detect the operating system
     */
    private function detectOS() {
        $os = strtolower(PHP_OS);

        if (strpos($os, 'darwin') !== false) {
            return 'darwin';
        } elseif (strpos($os, 'win') !== false) {
            return 'windows';
        } else {
            return 'linux';
        }
    }

    /**
     * Get current username
     */
    private function getCurrentUser() {
        if (isset($_SERVER['USER'])) {
            return $_SERVER['USER'];
        } elseif (isset($_SERVER['USERNAME'])) {
            return $_SERVER['USERNAME'];
        } elseif (function_exists('posix_getpwuid') && function_exists('posix_geteuid')) {
            $user = posix_getpwuid(posix_geteuid());
            return $user['name'];
        } else {
            return get_current_user();
        }
    }

    /**
     * Derive encryption key from password using PBKDF2
     */
    private function deriveKey($password, $salt) {
        return hash_pbkdf2('sha256', $password, $salt, 100000, 32, true);
    }

    /**
     * Encrypt data for credential storage
     */
    private function encryptData($data, $key) {
        $iv = random_bytes(16);
        $encrypted = '';
        $keyLen = strlen($key);
        $ivLen = strlen($iv);
        $dataLen = strlen($data);

        // Extend key to match data length
        $keyExtended = str_repeat($key, ceil($dataLen / $keyLen));
        $keyExtended = substr($keyExtended, 0, $dataLen);

        for ($i = 0; $i < $dataLen; $i++) {
            $encrypted .= chr(
                ord($data[$i]) ^
                ord($keyExtended[$i]) ^
                ord($iv[$i % $ivLen])
            );
        }

        return $iv . $encrypted;
    }

    /**
     * PHP 7 compatible str_starts_with
     */
    private function startsWith($haystack, $needle) {
        return substr($haystack, 0, strlen($needle)) === $needle;
    }

    /**
     * Add entry to .gitignore if it doesn't exist
     */
    private function addToGitignore($entry) {
        $gitignoreFile = '.gitignore';
        $entry = trim($entry);

        // Read existing .gitignore
        $existingContent = '';
        if (file_exists($gitignoreFile)) {
            $existingContent = file_get_contents($gitignoreFile);
        }

        // Check if entry already exists
        $lines = explode("\n", $existingContent);
        foreach ($lines as $line) {
            if (trim($line) === $entry) {
                return; // Already exists
            }
        }

        // Add entry
        $newContent = $existingContent;
        if (!empty($newContent) && !$this->endsWith($newContent, "\n")) {
            $newContent .= "\n";
        }
        $newContent .= $entry . "\n";

        file_put_contents($gitignoreFile, $newContent);
    }

    /**
     * Save project configuration to file
     */
    private function saveProjectConfig($projectName, $secretsDir) {
        $configFile = '.secrets_keychain_entry';
        $content = "secretdmg-$projectName\n$projectName\n$secretsDir\n";
        file_put_contents($configFile, $content);
    }

    /**
     * PHP 7 compatible str_ends_with
     */
    private function endsWith($haystack, $needle) {
        $length = strlen($needle);
        if ($length == 0) {
            return true;
        }
        return (substr($haystack, -$length) === $needle);
    }

    /**
     * Get all files recursively from a directory
     */
    private function getFilesRecursively($dir) {
        $files = [];
        $iterator = new RecursiveIteratorIterator(
            new RecursiveDirectoryIterator($dir, RecursiveDirectoryIterator::SKIP_DOTS)
        );

        foreach ($iterator as $file) {
            if ($file->isFile()) {
                $files[] = $file->getPathname();
            }
        }

        return $files;
    }

    /**
     * Encrypt the secrets folder into a .secrets file
     */
    private function encryptSecretsFolder($password, $files) {
        // Generate salt and derive key
        $salt = random_bytes(32);
        $key = $this->deriveKey($password, $salt);

        // Create metadata
        $metadata = [
            "version" => "1.0.4",
            "project" => $this->projectName,
            "created" => date('c'),
            "salt" => base64_encode($salt)
        ];

        // Encrypt all files
        $fileData = [];

        foreach ($files as $filePath) {
            $relativePath = str_replace('secrets/', '', $filePath);
            $relativePath = str_replace('secrets\\', '', $relativePath); // Windows
            $relativePath = str_replace('\\', '/', $relativePath); // Normalize separators

            $content = file_get_contents($filePath);
            if ($content === false) {
                throw new Exception("Failed to read file: $filePath");
            }

            // Encrypt file content
            $encryptedContent = $this->encryptFileData($content, $key);

            $fileData[$relativePath] = [
                "content" => base64_encode($encryptedContent),
                "permissions" => "644"
            ];

            echo "  ✔ $relativePath\n";
        }

        // Create the secrets package
        $package = [
            "metadata" => $metadata,
            "files" => $fileData
        ];

        // Write encrypted file
        $json = json_encode($package, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
        if (file_put_contents($this->secretsFile, $json) === false) {
            throw new Exception("Failed to write secrets file: {$this->secretsFile}");
        }

        return true;
    }

    /**
     * Encrypt file data (compatible with Python XOR implementation)
     */
    private function encryptFileData($data, $key) {
        $iv = random_bytes(16);
        $encrypted = '';
        $keyLen = strlen($key);
        $ivLen = strlen($iv);
        $dataLen = strlen($data);

        // Extend key to match data length
        $keyExtended = str_repeat($key, ceil($dataLen / $keyLen));
        $keyExtended = substr($keyExtended, 0, $dataLen);

        for ($i = 0; $i < $dataLen; $i++) {
            $encrypted .= chr(
                ord($data[$i]) ^
                ord($keyExtended[$i]) ^
                ord($iv[$i % $ivLen])
            );
        }

        return $iv . $encrypted;
    }

    /**
     * Remove directory recursively
     */
    private function removeDirectory($dir) {
        if (is_dir($dir)) {
            $files = array_diff(scandir($dir), ['.', '..']);
            foreach ($files as $file) {
                $path = $dir . '/' . $file;
                if (is_dir($path)) {
                    $this->removeDirectory($path);
                } else {
                    unlink($path);
                }
            }
            rmdir($dir);
        }
    }
}

// CLI entry point
if (php_sapi_name() === 'cli') {
    $cli = new SecretsManagerCLI();
    $exitCode = $cli->run($argv);
    exit($exitCode);
} else {
    echo "This script is intended to be run from the command line.\n";
    exit(1);
}
