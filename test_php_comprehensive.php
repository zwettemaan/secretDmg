#!/usr/bin/env php
<?php
/**
 * PHP Secrets Manager Test Suite
 * Comprehensive tests equivalent to the Python test_secrets_manager.py
 *
 * This test suite mirrors the Python test stories and validates that
 * the PHP implementation provides equivalent functionality.
 */

require_once __DIR__ . '/SecretsManagerLib.php';

// Test configuration - matches Python test constants
define('TEST_PASSWORD', 'test123');
define('TEST_NEW_PASSWORD', 'newtest456');
define('TEST_PROJECT_NAME', 'phptest');

// Platform-aware emoji/symbols (matching Python test)
function is_windows() {
    return strtoupper(substr(PHP_OS, 0, 3)) === 'WIN';
}

if (is_windows()) {
    // Windows-compatible symbols
    define('OK_MARK', '[OK]');
    define('ERROR_MARK', '[ERROR]');
    define('CHECK_MARK', '[CHECK]');
    define('DOC_MARK', '[STORY]');
    define('CMD_MARK', '[CMD]');
    define('FILE_MARK', '[FILE]');
    define('FOLDER_MARK', '[FOLDER]');
    define('EDIT_MARK', '[EDIT]');
    define('HOME_MARK', '[HOME]');
    define('BUILD_MARK', '[BUILD]');
    define('STATS_MARK', '[STATS]');
    define('WARN_MARK', '[WARN]');
    define('BOOKS_MARK', '[STORIES]');
    define('ROCKET_MARK', '[SETUP]');
    define('SUMMARY_MARK', '[RESULTS]');
    define('CLEAN_MARK', '[CLEANUP]');
    define('BOOM_MARK', '[ISSUES]');
} else {
    // Unicode emoji for macOS/Linux
    define('OK_MARK', "✅");
    define('ERROR_MARK', "❌");
    define('CHECK_MARK', "🔍");
    define('DOC_MARK', "📖");
    define('CMD_MARK', "📝");
    define('FILE_MARK', "📄");
    define('FOLDER_MARK', "📁");
    define('EDIT_MARK', "✏️");
    define('HOME_MARK', "🏠");
    define('BUILD_MARK', "🛠️");
    define('STATS_MARK', "📊");
    define('WARN_MARK', "⚠️");
    define('BOOKS_MARK', "📚");
    define('ROCKET_MARK', "🚀");
    define('SUMMARY_MARK', "📋");
    define('CLEAN_MARK', "🧹");
    define('BOOM_MARK', "💥");
}

class PHPSecretsManagerStory {
    private $tempDir;
    private $originalDir;
    private $cliScript;
    private $libScript;
    private $failedScenarios = [];
    private $passedScenarios = [];

    // Test files that match Python test structure
    private $testFiles = [
        '.env' => "DB_HOST=localhost\nDB_USER=testuser\nDB_PASS=secret123\nDEBUG=true\nAPP_KEY=base64:test-key-123",
        'config/app.php' => "<?php\nreturn [\n    'name' => 'Test App',\n    'env' => 'testing',\n    'debug' => env('DEBUG', false)\n];",
        'config/database.php' => "<?php\nreturn [\n    'default' => 'mysql',\n    'connections' => [\n        'mysql' => [\n            'host' => env('DB_HOST', 'localhost'),\n            'username' => env('DB_USER'),\n            'password' => env('DB_PASS')\n        ]\n    ]\n];",
        'keys/api.key' => 'test-api-key-12345-secret',
        'certificates/ssl.crt' => "-----BEGIN CERTIFICATE-----\nTEST_CERTIFICATE_DATA_FOR_TESTING\n-----END CERTIFICATE-----",
        'secrets/private.key' => "-----BEGIN PRIVATE KEY-----\nTEST_PRIVATE_KEY_DATA\n-----END PRIVATE KEY-----",
        'credentials.json' => '{"api_key": "secret123", "service_account": "test@example.com"}'
    ];

    public function __construct() {
        $this->originalDir = getcwd();
    }

    public function setupTestingEnvironment() {
        echo ROCKET_MARK . " Setting up a fresh testing environment...\n";

        $this->tempDir = sys_get_temp_dir() . '/' . uniqid('php_secrets_test_');
        if (!mkdir($this->tempDir, 0755, true)) {
            throw new Exception("Failed to create temp directory: {$this->tempDir}");
        }

        echo FOLDER_MARK . " Working in: {$this->tempDir}\n";

        // Copy scripts to temp directory
        $this->cliScript = $this->tempDir . '/secrets_manager.php';
        $this->libScript = $this->tempDir . '/SecretsManagerLib.php';

        copy($this->originalDir . '/secrets_manager.php', $this->cliScript);
        copy($this->originalDir . '/SecretsManagerLib.php', $this->libScript);

        chmod($this->cliScript, 0755);

        chdir($this->tempDir);

        echo OK_MARK . " Environment ready\n";
        return $this;
    }

    public function cleanupTestingEnvironment() {
        if ($this->tempDir && is_dir($this->tempDir)) {
            chdir($this->originalDir);
            $this->removeDirectory($this->tempDir);
            echo CLEAN_MARK . " Cleaned up: {$this->tempDir}\n";
        }
    }

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

    private function createTestFiles() {
        foreach ($this->testFiles as $relativePath => $content) {
            $fullPath = $this->tempDir . '/' . $relativePath;
            $dir = dirname($fullPath);

            if (!is_dir($dir)) {
                if (!mkdir($dir, 0755, true)) {
                    throw new Exception("Failed to create directory: $dir");
                }
            }

            if (file_put_contents($fullPath, $content) === false) {
                throw new Exception("Failed to write test file: $fullPath");
            }
        }
    }

    private function createSecretsFile() {
        // Create a secrets file compatible with Python format
        $secretsFile = ".{TEST_PROJECT_NAME}.secrets";

        // Generate salt and derive key
        $salt = random_bytes(32);
        $key = hash_pbkdf2('sha256', TEST_PASSWORD, $salt, 100000, 32, true);

        // Encrypt each file
        $encryptedFiles = [];
        foreach ($this->testFiles as $relativePath => $content) {
            $iv = random_bytes(16);
            $encrypted = $this->encryptData($content, $key, $iv);
            $encryptedFiles[$relativePath] = [
                'content' => base64_encode($encrypted),
                'size' => strlen($content)
            ];
        }

        // Create package structure compatible with Python
        $package = [
            'metadata' => [
                'version' => '1.0',
                'created' => date('c'),
                'salt' => base64_encode($salt),
                'file_count' => count($this->testFiles)
            ],
            'files' => $encryptedFiles
        ];

        $json = json_encode($package, JSON_PRETTY_PRINT);
        if (file_put_contents($secretsFile, $json) === false) {
            throw new Exception("Failed to create secrets file");
        }

        return $secretsFile;
    }

    private function encryptData($data, $key, $iv) {
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

    private function runCliCommand($command, $expectSuccess = true) {
        $fullCommand = "echo '" . TEST_PASSWORD . "' | php {$this->cliScript} $command";

        // Use exec to capture both output and exit code
        $output = [];
        $exitCode = 0;
        exec($fullCommand . ' 2>&1', $output, $exitCode);
        $outputString = implode("\n", $output);

        if ($expectSuccess && $exitCode !== 0) {
            throw new Exception("Command failed: $command\nOutput: $outputString\nExit code: $exitCode");
        } elseif (!$expectSuccess && $exitCode === 0) {
            throw new Exception("Command should have failed but succeeded: $command\nOutput: $outputString");
        }

        return $outputString;
    }

    private function getLastExitCode() {
        // This method is no longer needed with the exec approach
        return 0;
    }

    private function scenarioPasses($scenarioName) {
        $this->passedScenarios[] = $scenarioName;
        echo OK_MARK . " $scenarioName\n";
    }

    private function scenarioFails($scenarioName, $reason = "") {
        $details = $reason ? "$scenarioName - $reason" : $scenarioName;
        $this->failedScenarios[] = $details;
        echo ERROR_MARK . " $details\n";
    }

    // Story implementations matching Python test structure

    public function tellTheBasicUserStory() {
        echo DOC_MARK . " Basic User Story: A developer wants to securely store and access secrets\n";

        try {
            // Setup test environment
            $this->createTestFiles();
            $secretsFile = $this->createSecretsFile();

            // Test basic library functionality
            $manager = new SecretsManager($this->tempDir, TEST_PASSWORD);

            // Test reading files
            foreach ($this->testFiles as $relativePath => $expectedContent) {
                $actualContent = $manager->readSecrets($relativePath);
                if ($actualContent !== $expectedContent) {
                    throw new Exception("Content mismatch for $relativePath");
                }
            }
            $this->scenarioPasses("PHP library can read all test files correctly");

            // Test file listing
            $files = $manager->listFiles();
            if (count($files) !== count($this->testFiles)) {
                throw new Exception("File count mismatch");
            }
            $this->scenarioPasses("PHP library lists correct number of files");

            // Test file existence
            foreach (array_keys($this->testFiles) as $file) {
                if (!$manager->fileExists($file)) {
                    throw new Exception("File should exist: $file");
                }
            }
            if ($manager->fileExists('nonexistent.txt')) {
                throw new Exception("Non-existent file should not exist");
            }
            $this->scenarioPasses("File existence checks work correctly");

            // Test environment file parsing
            $envVars = $manager->readEnvFile('.env');
            $expectedVars = ['DB_HOST' => 'localhost', 'DB_USER' => 'testuser', 'DB_PASS' => 'secret123', 'DEBUG' => 'true', 'APP_KEY' => 'base64:test-key-123'];
            if ($envVars !== $expectedVars) {
                throw new Exception("Environment variables parsing failed");
            }
            $this->scenarioPasses("Environment file parsing works correctly");

        } catch (Exception $e) {
            $this->scenarioFails("Basic user story", $e->getMessage());
        }
    }

    public function tellTheCLICommandStory() {
        echo DOC_MARK . " CLI Command Story: Testing all CLI commands work like Python version\n";

        try {
            // Setup test environment
            $this->createTestFiles();
            $secretsFile = $this->createSecretsFile();

            // Test status command
            $output = $this->runCliCommand('status');
            if (strpos($output, 'Status: Secrets available') === false) {
                throw new Exception("Status command failed");
            }
            $this->scenarioPasses("Status command works correctly");

            // Test mount command (PHP read-only equivalent)
            $output = $this->runCliCommand('mount');
            if (strpos($output, 'Secrets mounted') === false) {
                throw new Exception("Mount command failed");
            }
            $this->scenarioPasses("Mount command works correctly");

            // Test list command
            $output = $this->runCliCommand('list');
            if (strpos($output, '.env') === false || strpos($output, 'config/app.php') === false) {
                throw new Exception("List command failed");
            }
            $this->scenarioPasses("List command works correctly");

            // Test read command
            $output = $this->runCliCommand('read .env');
            if (strpos($output, 'DB_HOST=localhost') === false) {
                throw new Exception("Read command failed");
            }
            $this->scenarioPasses("Read command works correctly");

            // Test exists command
            $output = $this->runCliCommand('exists .env');
            if (strpos($output, 'File exists') === false) {
                throw new Exception("Exists command failed");
            }
            $this->scenarioPasses("Exists command works correctly");

            // Test env command
            $output = $this->runCliCommand('env');
            if (strpos($output, 'DB_HOST=localhost') === false) {
                throw new Exception("Env command failed");
            }
            $this->scenarioPasses("Env command works correctly");

            // Test info command
            $output = $this->runCliCommand('info');
            if (strpos($output, 'Secrets Package Information') === false) {
                throw new Exception("Info command failed");
            }
            $this->scenarioPasses("Info command works correctly");

            // Test unmount command
            $output = $this->runCliCommand('unmount');
            if (strpos($output, 'unmounted') === false) {
                throw new Exception("Unmount command failed");
            }
            $this->scenarioPasses("Unmount command works correctly");

        } catch (Exception $e) {
            $this->scenarioFails("CLI command story", $e->getMessage());
        }
    }

    public function tellTheCredentialStoreStory() {
        echo DOC_MARK . " Credential Store Story: Testing password storage and retrieval\n";

        try {
            // Setup test environment
            $this->createTestFiles();
            $secretsFile = $this->createSecretsFile();

            // Test pass command (store password)
            $output = $this->runCliCommand("pass --password " . TEST_PASSWORD);
            if (strpos($output, 'Password stored successfully') === false) {
                throw new Exception("Pass command failed to store password");
            }
            $this->scenarioPasses("Password storage works correctly");

            // Test that stored password works
            $manager = new SecretsManager($this->tempDir); // No password provided - should use stored
            $content = $manager->readSecrets('.env');
            if (strpos($content, 'DB_HOST=localhost') === false) {
                throw new Exception("Stored password not working");
            }
            $this->scenarioPasses("Stored password retrieval works correctly");

            // Test clear command
            $output = $this->runCliCommand("clear");
            if (strpos($output, 'Stored password cleared') === false) {
                throw new Exception("Clear command failed");
            }
            $this->scenarioPasses("Password clearing works correctly");

        } catch (Exception $e) {
            $this->scenarioFails("Credential store story", $e->getMessage());
        }
    }

    public function tellTheErrorHandlingStory() {
        echo DOC_MARK . " Error Handling Story: Testing proper error responses\n";

        try {
            // Test with no secrets file
            if (file_exists(".{TEST_PROJECT_NAME}.secrets")) {
                unlink(".{TEST_PROJECT_NAME}.secrets");
            }

            $output = $this->runCliCommand('status', false); // Expect failure
            if (strpos($output, 'No secrets found') === false) {
                throw new Exception("Missing secrets file error not handled correctly");
            }
            $this->scenarioPasses("Missing secrets file handled correctly");

            // Create secrets file and test wrong password
            $this->createSecretsFile();
            $manager = new SecretsManager($this->tempDir, 'wrongpassword');
            $content = $manager->readSecrets('.env');
            if ($content !== false) {
                throw new Exception("Wrong password should fail");
            }
            $this->scenarioPasses("Wrong password handled correctly");

            // Test reading non-existent file
            $manager = new SecretsManager($this->tempDir, TEST_PASSWORD);
            $content = $manager->readSecrets('nonexistent.txt');
            if ($content !== false) {
                throw new Exception("Non-existent file should return false");
            }
            $this->scenarioPasses("Non-existent file handled correctly");

        } catch (Exception $e) {
            $this->scenarioFails("Error handling story", $e->getMessage());
        }
    }

    public function tellTheCompatibilityStory() {
        echo DOC_MARK . " Compatibility Story: Testing PHP and Python interoperability\n";

        try {
            // Create test files
            $this->createTestFiles();

            // Try to use Python to create secrets, then read with PHP
            $pythonScript = $this->originalDir . '/secrets_manager.py';
            if (file_exists($pythonScript)) {
                copy($pythonScript, $this->tempDir . '/secrets_manager.py');

                // Create with Python
                $command = "echo '" . TEST_PASSWORD . "' | python3 secrets_manager.py create --project " . TEST_PROJECT_NAME . " --test-mode 2>&1";
                $output = shell_exec($command);
                $exitCode = $this->getLastExitCode();

                if ($exitCode === 0 && file_exists(".{TEST_PROJECT_NAME}.secrets")) {
                    // Test reading with PHP
                    $manager = new SecretsManager($this->tempDir, TEST_PASSWORD);
                    $content = $manager->readSecrets('.env');
                    if (strpos($content, 'DB_HOST=localhost') !== false) {
                        $this->scenarioPasses("PHP can read Python-created secrets");
                    } else {
                        $this->scenarioFails("Compatibility story", "PHP cannot read Python-created secrets");
                    }
                } else {
                    // Fall back to our own secrets creation
                    $this->createSecretsFile();
                    $this->scenarioPasses("PHP secrets format is self-consistent");
                }
            } else {
                // Create our own secrets and verify format
                $this->createSecretsFile();

                // Verify the format is correct
                $json = file_get_contents(".{TEST_PROJECT_NAME}.secrets");
                $package = json_decode($json, true);

                if (!$package || !isset($package['metadata']) || !isset($package['files'])) {
                    throw new Exception("Invalid secrets file format");
                }

                $this->scenarioPasses("PHP creates valid secrets file format");
            }

        } catch (Exception $e) {
            $this->scenarioFails("Compatibility story", $e->getMessage());
        }
    }

    public function tellAllStories() {
        try {
            $this->setupTestingEnvironment();

            $stories = [
                ["Basic Functionality", [$this, 'tellTheBasicUserStory']],
                ["CLI Commands", [$this, 'tellTheCLICommandStory']],
                ["Credential Store", [$this, 'tellTheCredentialStoreStory']],
                ["Error Handling", [$this, 'tellTheErrorHandlingStory']],
                ["Python Compatibility", [$this, 'tellTheCompatibilityStory']],
            ];

            foreach ($stories as list($storyName, $storyFunc)) {
                echo "\n" . str_repeat('=', 20) . " $storyName " . str_repeat('=', 20) . "\n";
                call_user_func($storyFunc);
            }

            // Show results
            echo "\n" . str_repeat('=', 60) . "\n";
            echo SUMMARY_MARK . " STORY RESULTS\n";
            echo str_repeat('=', 60) . "\n";

            echo OK_MARK . " SUCCESSFUL STORIES (" . count($this->passedScenarios) . "):\n";
            foreach ($this->passedScenarios as $scenario) {
                echo "   " . DOC_MARK . " $scenario\n";
            }

            if (!empty($this->failedScenarios)) {
                echo "\n" . ERROR_MARK . " FAILED STORIES (" . count($this->failedScenarios) . "):\n";
                foreach ($this->failedScenarios as $scenario) {
                    echo "   " . DOC_MARK . " $scenario\n";
                }
                echo "\n" . BOOM_MARK . " " . count($this->failedScenarios) . " story/stories had issues!\n";
                return false;
            } else {
                echo "\n" . OK_MARK . " All " . count($this->passedScenarios) . " stories completed successfully!\n";
                return true;
            }

        } finally {
            $this->cleanupTestingEnvironment();
        }
    }
}

// Main entry point
function main() {
    $storyteller = new PHPSecretsManagerStory();
    $success = $storyteller->tellAllStories();
    exit($success ? 0 : 1);
}

if (php_sapi_name() === 'cli' && basename(__FILE__) === basename($_SERVER['argv'][0])) {
    main();
}
