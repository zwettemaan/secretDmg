#!/usr/bin/env php
<?php
/**
 * PHP Secrets Manager Test Suite
 * Tests the PHP SecretsManager library using a temporary test environment,
 * equivalent to the Python test_secrets_manager.py approach.
 */

require_once __DIR__ . '/SecretsManagerLib.php';

// Test configuration
define('TEST_PASSWORD', 'test123');
define('TEST_PROJECT_NAME', 'phptest');

class PHPSecretsManagerTest {
    private $tempDir;
    private $originalDir;
    private $testFiles = [
        '.env' => "DB_HOST=localhost\nDB_USER=testuser\nDB_PASS=secret123\nDEBUG=true",
        'config/app.php' => "<?php\nreturn [\n    'name' => 'Test App',\n    'env' => 'testing'\n];",
        'config/database.php' => "<?php\nreturn [\n    'default' => 'mysql',\n    'connections' => [\n        'mysql' => [\n            'host' => env('DB_HOST'),\n            'username' => env('DB_USER')\n        ]\n    ]\n];",
        'keys/api.key' => 'test-api-key-12345',
        'certificates/ssl.crt' => "-----BEGIN CERTIFICATE-----\nTEST_CERTIFICATE_DATA\n-----END CERTIFICATE-----"
    ];

    public function __construct() {
        $this->originalDir = getcwd();
    }

    private function createTempDirectory() {
        $tempDir = sys_get_temp_dir() . '/' . uniqid('php_secrets_test_');
        if (!mkdir($tempDir, 0755, true)) {
            throw new Exception("Failed to create temp directory: $tempDir");
        }
        $this->tempDir = $tempDir;
        echo "📂 Created temp test directory: $tempDir\n";
        return $tempDir;
    }

    private function createTestFiles() {
        foreach ($this->testFiles as $relativePath => $content) {
            $fullPath = $this->tempDir . '/' . $relativePath;
            $dir = dirname($fullPath);

            // Create directory structure
            if (!is_dir($dir)) {
                if (!mkdir($dir, 0755, true)) {
                    throw new Exception("Failed to create directory: $dir");
                }
            }

            // Write file
            if (file_put_contents($fullPath, $content) === false) {
                throw new Exception("Failed to write test file: $fullPath");
            }
        }
        echo "📄 Created " . count($this->testFiles) . " test files\n";
    }

    private function createMockSecretsFile() {
        echo "� Creating mock secrets file (compatible with Python format)...\n";

        // Generate salt and derive key (same method as Python tool)
        $salt = random_bytes(32);
        $key = hash_pbkdf2('sha256', TEST_PASSWORD, $salt, 100000, 32, true);

        // Encrypt each test file
        $encryptedFiles = [];
        foreach ($this->testFiles as $relativePath => $content) {
            $encryptedContent = $this->encryptData($content, $key);
            $encryptedFiles[$relativePath] = [
                'content' => base64_encode($encryptedContent),
                'size' => strlen($content)
            ];
        }

        // Create secrets package in Python-compatible format
        $package = [
            'metadata' => [
                'version' => '1.0',
                'created' => date('Y-m-d H:i:s'),
                'file_count' => count($this->testFiles),
                'salt' => base64_encode($salt)
            ],
            'files' => $encryptedFiles
        ];

        // Write secrets file
        $secretsFile = $this->tempDir . '/.' . TEST_PROJECT_NAME . '.secrets';
        $json = json_encode($package, JSON_PRETTY_PRINT);

        if (file_put_contents($secretsFile, $json) === false) {
            throw new Exception("Failed to write secrets file: $secretsFile");
        }

        echo "✅ Mock secrets file created: $secretsFile\n";
        return $secretsFile;
    }

    private function encryptData($data, $key) {
        // Generate random IV
        $iv = random_bytes(16);

        // Extend key to match data length
        $dataLen = strlen($data);
        $keyLen = strlen($key);
        $keyExtended = str_repeat($key, ceil($dataLen / $keyLen));
        $keyExtended = substr($keyExtended, 0, $dataLen);

        // XOR encryption (same as Python implementation)
        $encrypted = '';
        $ivLen = strlen($iv);
        for ($i = 0; $i < $dataLen; $i++) {
            $encrypted .= chr(
                ord($data[$i]) ^
                ord($keyExtended[$i]) ^
                ord($iv[$i % $ivLen])
            );
        }

        // Return IV + encrypted data
        return $iv . $encrypted;
    }

    private function getLastExitCode() {
        return (int)shell_exec('echo $?');
    }

    private function testPHPLibrary() {
        echo "🧪 Testing PHP SecretsManager library...\n";

        // Test 1: Initialize SecretsManager
        $manager = new SecretsManager($this->tempDir, TEST_PASSWORD);
        echo "✅ SecretsManager initialized\n";

        // Test 2: List files
        $files = $manager->listFiles();
        if (count($files) !== count($this->testFiles)) {
            throw new Exception("Expected " . count($this->testFiles) . " files, got " . count($files));
        }
        echo "✅ Listed " . count($files) . " files correctly\n";

        // Test 3: Read each test file
        foreach ($this->testFiles as $relativePath => $expectedContent) {
            $actualContent = $manager->readSecrets($relativePath);
            if ($actualContent === false) {
                throw new Exception("Failed to read file: $relativePath");
            }
            if ($actualContent !== $expectedContent) {
                throw new Exception("Content mismatch for file: $relativePath");
            }
            echo "✅ Read file correctly: $relativePath\n";
        }

        // Test 4: Test file existence
        foreach (array_keys($this->testFiles) as $relativePath) {
            if (!$manager->fileExists($relativePath)) {
                throw new Exception("File should exist: $relativePath");
            }
        }

        if ($manager->fileExists('nonexistent.txt')) {
            throw new Exception("Non-existent file should not exist");
        }
        echo "✅ File existence checks passed\n";

        // Test 5: Test .env parsing
        $envVars = $manager->readEnvFile('.env');
        $expectedEnvVars = [
            'DB_HOST' => 'localhost',
            'DB_USER' => 'testuser',
            'DB_PASS' => 'secret123',
            'DEBUG' => 'true'
        ];

        if ($envVars !== $expectedEnvVars) {
            throw new Exception("Environment variables parsing failed");
        }
        echo "✅ Environment file parsing passed\n";

        // Test 6: Test metadata
        $metadata = $manager->getMetadata();
        if (!$metadata || !isset($metadata['salt'])) {
            throw new Exception("Metadata retrieval failed");
        }
        echo "✅ Metadata retrieval passed\n";

        echo "🎉 All PHP library tests passed!\n";
    }

    private function testCLITool() {
        echo "🖥️ Testing PHP CLI tool...\n";

        // Test CLI commands
        $cliScript = $this->originalDir . '/secrets_manager.php';
        if (!file_exists($cliScript)) {
            throw new Exception("PHP CLI script not found");
        }

        // Copy CLI script to temp directory (so it finds the secrets file)
        copy($cliScript, $this->tempDir . '/secrets_manager.php');
        copy($this->originalDir . '/SecretsManagerLib.php', $this->tempDir . '/SecretsManagerLib.php');

        // Change to temp directory for CLI tests
        $oldCwd = getcwd();
        chdir($this->tempDir);

        try {
            // Test list command
            $command = sprintf('echo %s | php secrets_manager.php list 2>&1', escapeshellarg(TEST_PASSWORD));
            $output = shell_exec($command);

            if (strpos($output, '.env') === false) {
                throw new Exception("CLI list command failed. Output: $output");
            }
            echo "✅ CLI list command passed\n";

            // Test read command
            $command = sprintf('echo %s | php secrets_manager.php read .env 2>&1', escapeshellarg(TEST_PASSWORD));
            $output = shell_exec($command);

            if (strpos($output, 'DB_HOST=localhost') === false) {
                throw new Exception("CLI read command failed. Output: $output");
            }
            echo "✅ CLI read command passed\n";

            // Test exists command
            $command = sprintf('echo %s | php secrets_manager.php exists .env 2>&1', escapeshellarg(TEST_PASSWORD));
            $output = shell_exec($command);

            if (strpos($output, 'File exists') === false) {
                throw new Exception("CLI exists command failed. Output: $output");
            }
            echo "✅ CLI exists command passed\n";

            echo "🎉 All CLI tests passed!\n";

        } finally {
            // Always restore original directory
            chdir($oldCwd);
        }
    }

    private function cleanup() {
        // Change back to original directory
        chdir($this->originalDir);

        // Remove temp directory
        if ($this->tempDir && is_dir($this->tempDir)) {
            $this->removeDirectory($this->tempDir);
            echo "🧹 Cleaned up temp directory\n";
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

    public function run() {
        try {
            echo "🚀 Starting PHP Secrets Manager Test Suite\n";
            echo "==========================================\n\n";

            // Setup
            $this->createTempDirectory();
            $this->createTestFiles();
            $this->createMockSecretsFile();

            // Run tests
            $this->testPHPLibrary();
            $this->testCLITool();

            echo "\n🎉 All tests passed successfully!\n";

        } catch (Exception $e) {
            echo "\n❌ Test failed: " . $e->getMessage() . "\n";
            return 1;
        } finally {
            $this->cleanup();
        }

        return 0;
    }
}

// Run tests if this script is executed directly
if (php_sapi_name() === 'cli' && basename(__FILE__) === basename($_SERVER['argv'][0])) {
    $test = new PHPSecretsManagerTest();
    $exitCode = $test->run();
    exit($exitCode);
}
