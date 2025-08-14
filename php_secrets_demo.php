<?php
/**
 * PHP Secrets Demo
 *
 * This demo shows how to use the SecretsManagerLib to read secrets
 * that were created using the Python secrets_manager.py tool.
 *
 * Usage:
 * 1. First create secrets using Python: python secrets_manager.py create
 * 2. Add your secret files to the secrets/ directory
 * 3. Encrypt them: python secrets_manager.py unmount
 * 4. Run this PHP demo to read the encrypted secrets
 */

require_once 'SecretsManagerLib.php';

echo "🔐 PHP Secrets Manager Demo\n";
echo "============================\n\n";

try {
    // Initialize the secrets manager
    // It will auto-detect the project name from existing .*.secrets files
    $manager = new SecretsManager();

    echo "📦 Project detected: " . basename(getcwd()) . "\n";

    // List all available files
    echo "\n📂 Available secret files:\n";
    $files = $manager->listFiles();

    if (empty($files)) {
        echo "   (no files found)\n";
        echo "   💡 Create secrets first using: python secrets_manager.py create\n";
        exit(1);
    }

    foreach ($files as $file) {
        echo "   📄 $file\n";
    }

    // Demonstrate reading a .env file if it exists
    if ($manager->fileExists('.env')) {
        echo "\n🌍 Reading .env file:\n";
        $envContent = $manager->readSecrets('.env');

        if ($envContent !== false) {
            // Parse and display environment variables (hiding sensitive ones)
            $envVars = SecretsManager::parseEnvContent($envContent);
            foreach ($envVars as $key => $value) {
                if (stripos($key, 'password') !== false ||
                    stripos($key, 'secret') !== false ||
                    stripos($key, 'key') !== false ||
                    stripos($key, 'token') !== false) {
                    echo "   $key=***HIDDEN***\n";
                } else {
                    echo "   $key=$value\n";
                }
            }
        }
    }

    // Demonstrate reading any other file
    if (count($files) > 1 || !$manager->fileExists('.env')) {
        $firstFile = $files[0];
        if ($firstFile !== '.env') {
            echo "\n📄 Reading $firstFile:\n";
            $content = $manager->readSecrets($firstFile);
            if ($content !== false) {
                // Only show first few lines for security
                $lines = explode("\n", $content);
                $preview = array_slice($lines, 0, 3);
                foreach ($preview as $line) {
                    echo "   " . substr($line, 0, 50) . (strlen($line) > 50 ? "..." : "") . "\n";
                }
                if (count($lines) > 3) {
                    echo "   ... (" . (count($lines) - 3) . " more lines)\n";
                }
            }
        }
    }

    // Show metadata
    $metadata = $manager->getMetadata();
    if ($metadata) {
        echo "\n📊 Secrets Metadata:\n";
        if (isset($metadata['created'])) {
            echo "   📅 Created: " . $metadata['created'] . "\n";
        }
        if (isset($metadata['version'])) {
            echo "   🔢 Version: " . $metadata['version'] . "\n";
        }
        echo "   📄 Total files: " . count($files) . "\n";
    }

    echo "\n✅ Demo completed successfully!\n";

} catch (Exception $e) {
    echo "❌ Error: " . $e->getMessage() . "\n";
    echo "\n💡 Make sure you've created secrets first:\n";
    echo "   1. python secrets_manager.py create\n";
    echo "   2. Add files to secrets/ directory\n";
    echo "   3. python secrets_manager.py unmount\n";
    echo "   4. Run this demo again\n";
    exit(1);
}

echo "\n💡 Integration Examples:\n";
echo "========================\n";
echo "// Laravel .env loading:\n";
echo "\$envVars = \$manager->readEnvFile('.env');\n";
echo "foreach (\$envVars as \$key => \$value) {\n";
echo "    putenv(\"\$key=\$value\");\n";
echo "}\n\n";

echo "// Read database config:\n";
echo "\$dbConfig = \$manager->readSecrets('config/database.json');\n";
echo "\$config = json_decode(\$dbConfig, true);\n\n";

echo "// Read SSL certificate:\n";
echo "\$cert = \$manager->readSecrets('ssl/certificate.pem');\n";
echo "file_put_contents('/tmp/cert.pem', \$cert);\n";
?>
