<?php
/**
 * Test script for PHP Secrets Manager
 * This script tests the PHP implementation against the Python secrets manager
 */

require_once 'secrets_manager.php';

// Test mode constants (matching Python test)
define('TEST_PASSWORD', 'test123');

function runTests() {
    echo "PHP Secrets Manager Test Suite\n";
    echo "==============================\n";
    echo "Testing PHP implementation compatibility with Python secrets manager\n";
    echo "Will try credential store first, fallback to test password if needed\n\n";

    $tests = [];
    $passed = 0;
    $failed = 0;

    // Test 1: Check if secrets file exists
    echo "Test 1: Checking for secrets file...\n";
    $projectName = basename(getcwd());
    $secretsFile = ".{$projectName}.secrets";

    if (file_exists($secretsFile)) {
        echo "✓ Found secrets file: $secretsFile\n";
        $tests['secrets_file_exists'] = true;
        $passed++;
    } else {
        echo "✗ Secrets file not found: $secretsFile\n";
        echo "  Run 'python secrets_manager.py create' and add some files first\n";
        $tests['secrets_file_exists'] = false;
        $failed++;
        return [$passed, $failed];
    }

    echo "\n";

    try {
        // Test 2: Create SecretsManager instance with test password
        echo "Test 2: Creating SecretsManager instance...\n";

        // Use test password directly (like Python test mode)
        $manager = new SecretsManager(null, TEST_PASSWORD);
        echo "✓ SecretsManager created successfully with test password\n";
        $tests['manager_creation'] = true;
        $passed++;

        // Test 2b: Check credential store separately (optional)
        echo "  - Testing credential store access (optional)...\n";
        try {
            $credStoreManager = new SecretsManager(null, null); // Try credential store only
            $metadata = $credStoreManager->getMetadata();
            if ($metadata !== false) {
                echo "  ✓ Credential store is also working\n";
                $tests['credential_store'] = true;
            } else {
                echo "  - Credential store not available (using test password)\n";
                $tests['credential_store'] = 'not_available';
            }
        } catch (Exception $e) {
            echo "  - Credential store not available (using test password)\n";
            $tests['credential_store'] = 'not_available';
        }
        $passed++;

        // Test 3: Get metadata
        echo "\nTest 3: Reading metadata...\n";
        $metadata = $manager->getMetadata();
        if ($metadata !== false) {
            echo "✓ Metadata read successfully\n";
            echo "  Project: " . $metadata['project'] . "\n";
            echo "  Version: " . $metadata['version'] . "\n";
            echo "  Created: " . $metadata['created'] . "\n";
            $tests['metadata'] = true;
            $passed++;
        } else {
            echo "✗ Failed to read metadata\n";
            $tests['metadata'] = false;
            $failed++;
        }

        // Test 4: List files
        echo "\nTest 4: Listing files...\n";
        $files = $manager->listFiles();
        if (!empty($files)) {
            echo "✓ Found " . count($files) . " files:\n";
            foreach ($files as $file) {
                echo "  - $file\n";
            }
            $tests['list_files'] = true;
            $passed++;
        } else {
            echo "✗ No files found or failed to list files\n";
            $tests['list_files'] = false;
            $failed++;
        }

        // Test 5: Test file existence check
        echo "\nTest 5: Testing file existence checks...\n";
        $testFile = $files[0] ?? '.env'; // Use first file or default to .env
        if ($manager->fileExists($testFile)) {
            echo "✓ File exists check works for: $testFile\n";
            $tests['file_exists'] = true;
            $passed++;
        } else {
            echo "✗ File exists check failed for: $testFile\n";
            $tests['file_exists'] = false;
            $failed++;
        }

        // Test 6: Read a specific file
        echo "\nTest 6: Reading specific file content...\n";
        $content = $manager->readSecrets($testFile);
        if ($content !== false) {
            $size = strlen($content);
            echo "✓ Successfully read $testFile ($size bytes)\n";

            // Show preview for text files
            if (mb_check_encoding($content, 'UTF-8')) {
                $preview = substr($content, 0, 100);
                echo "  Preview: " . str_replace("\n", "\\n", $preview) .
                     (strlen($content) > 100 ? "..." : "") . "\n";
            } else {
                echo "  Content appears to be binary data\n";
            }
            $tests['read_file'] = true;
            $passed++;
        } else {
            echo "✗ Failed to read file: $testFile\n";
            $tests['read_file'] = false;
            $failed++;
        }

        // Test 7: Test convenience function
        echo "\nTest 7: Testing convenience function...\n";

        // Use test password directly for convenience functions
        $content2 = read_secrets($testFile, null, TEST_PASSWORD);

        if ($content2 !== false && $content2 === $content) {
            echo "✓ Convenience function works and returns same content\n";
            $tests['convenience_function'] = true;
            $passed++;
        } else {
            echo "✗ Convenience function failed or returned different content\n";
            $tests['convenience_function'] = false;
            $failed++;
        }

        // Test 8: Test .env parsing (if .env file exists)
        echo "\nTest 8: Testing .env file parsing...\n";
        if ($manager->fileExists('.env')) {
            $envContent = $manager->readSecrets('.env');
            if ($envContent !== false) {
                $envVars = SecretsManager::parseEnvContent($envContent);
                if (!empty($envVars)) {
                    echo "✓ .env file parsed successfully (" . count($envVars) . " variables)\n";
                    foreach (array_slice($envVars, 0, 3) as $key => $value) {
                        echo "  $key = " . substr($value, 0, 20) .
                             (strlen($value) > 20 ? "..." : "") . "\n";
                    }
                    $tests['env_parsing'] = true;
                    $passed++;
                } else {
                    echo "✗ .env file parsed but no variables found\n";
                    $tests['env_parsing'] = false;
                    $failed++;
                }
            } else {
                echo "✗ Failed to read .env file\n";
                $tests['env_parsing'] = false;
                $failed++;
            }
        } else {
            echo "- No .env file found, skipping test\n";
            $tests['env_parsing'] = 'skipped';
        }

        // Test 9: Test readEnvFile method
        echo "\nTest 9: Testing readEnvFile method...\n";
        if ($manager->fileExists('.env')) {
            $envVars2 = $manager->readEnvFile('.env');
            if ($envVars2 !== false) {
                echo "✓ readEnvFile method works\n";
                $tests['read_env_file'] = true;
                $passed++;
            } else {
                echo "✗ readEnvFile method failed\n";
                $tests['read_env_file'] = false;
                $failed++;
            }
        } else {
            echo "- No .env file found, skipping test\n";
            $tests['read_env_file'] = 'skipped';
        }

        // Test 10: Test read_env_secrets convenience function
        echo "\nTest 10: Testing read_env_secrets convenience function...\n";
        if ($manager->fileExists('.env')) {
            // Use test password directly for convenience function
            $envVars3 = read_env_secrets('.env', null, TEST_PASSWORD);

            if ($envVars3 !== false) {
                echo "✓ read_env_secrets convenience function works\n";
                echo "🔑 Found " . count($envVars3) . " environment variables\n";
                $tests['read_env_secrets_function'] = true;
                $passed++;
            } else {
                echo "✗ read_env_secrets convenience function failed\n";
                $tests['read_env_secrets_function'] = false;
                $failed++;
            }
        } else {
            echo "- No .env file found, skipping test\n";
            $tests['read_env_secrets_function'] = 'skipped';
        }

    } catch (Exception $e) {
        echo "✗ Exception occurred: " . $e->getMessage() . "\n";
        $failed++;
    }

    return [$passed, $failed, $tests];
}

// Run the tests
list($passed, $failed, $tests) = runTests();

echo "\n";
echo "Test Results Summary\n";
echo "===================\n";
echo "Passed: $passed\n";
echo "Failed: $failed\n";
echo "Total:  " . ($passed + $failed) . "\n";

if ($failed === 0) {
    echo "\n🎉 All tests passed! The PHP Secrets Manager is working correctly.\n";
    exit(0);
} else {
    echo "\n❌ Some tests failed. Please check the implementation.\n";
    exit(1);
}
?>
