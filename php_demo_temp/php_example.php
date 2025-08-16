<?php
/**
 * PHP Secrets Manager Demo
 *
 * This demonstrates how to use SecretsManagerLib.php to read secrets
 * created by the Python secrets_manager.py tool.
 */

require_once 'SecretsManagerLib.php';

echo "🔐 PHP Secrets Reader Demo\n";
echo "==========================\n\n";

try {
    // Initialize the secrets manager
    // It will automatically detect the project and retrieve the password from keychain
    $manager = new SecretsManager();

    // Check if secrets exist before proceeding
    $files = $manager->listFiles();
    
    if (empty($files)) {
        echo "❌ No secrets found!\n\n";
        echo "📋 This demo requires an encrypted secrets file to exist.\n";
        echo "   Instead of running this script directly, please use:\n\n";
        
        if (PHP_OS_FAMILY === 'Windows' || strpos(strtolower(PHP_OS), 'cygwin') !== false) {
            echo "   🪟 Windows: demo_php_integration.bat\n";
        } else {
            echo "   🐧 Linux/Mac: ./demo_php_integration.sh\n";
        }
        
        echo "\n� The demo script will:\n";
        echo "   1. Create sample secrets using Python\n";
        echo "   2. Run this PHP example with real data\n";
        echo "   3. Clean up afterward\n\n";
        echo "🔧 Alternatively, create your own secrets:\n";
        echo "   python secrets_manager.py create\n";
        echo "   # Add files to secrets/ folder\n";
        echo "   python secrets_manager.py unmount\n";
        echo "   php php_example.php\n\n";
        exit(1);
    }

    // List all available secret files
    echo "📦 Available secret files:\n";
    foreach ($files as $file) {
        echo "   📄 $file\n";
    }
    echo "\n";

    // Demo 1: Read and parse .env file
    echo "🌍 Demo 1: Environment Variables\n";
    echo "--------------------------------\n";
    $envContent = $manager->readSecrets('.env');
    $envVars = $manager->parseEnvContent($envContent);
    foreach ($envVars as $key => $value) {
        // Mask sensitive values for display
        if (strpos(strtolower($key), 'pass') !== false ||
            strpos(strtolower($key), 'secret') !== false ||
            strpos(strtolower($key), 'key') !== false) {
            $value = str_repeat('*', strlen($value));
        }
        echo "   $key = $value\n";
    }
    echo "\n";

    // Demo 2: Read JSON configuration
    echo "⚙️  Demo 2: Database Configuration\n";
    echo "---------------------------------\n";
    $configContent = $manager->readSecrets('database_config.json');
    $config = json_decode($configContent, true);
    
    if (json_last_error() !== JSON_ERROR_NONE) {
        echo "   Error parsing JSON: " . json_last_error_msg() . "\n";
    } else {
        // Check for expected structure and provide fallbacks
        $primaryHost = isset($config['database']['primary']['host']) ? $config['database']['primary']['host'] : 'unknown';
        $primaryPort = isset($config['database']['primary']['port']) ? $config['database']['primary']['port'] : 'unknown';
        $replicaHost = isset($config['database']['replica']['host']) ? $config['database']['replica']['host'] : 'unknown';
        $replicaPort = isset($config['database']['replica']['port']) ? $config['database']['replica']['port'] : 'unknown';
        $cacheHost = isset($config['cache']['redis']['host']) ? $config['cache']['redis']['host'] : 'unknown';
        $cachePort = isset($config['cache']['redis']['port']) ? $config['cache']['redis']['port'] : 'unknown';
        
        echo "   Primary DB: {$primaryHost}:{$primaryPort}\n";
        echo "   Replica DB: {$replicaHost}:{$replicaPort}\n";
        echo "   Cache: {$cacheHost}:{$cachePort}\n";
    }
    echo "\n";

    // Demo 3: Read certificate file
    echo "🔐 Demo 3: SSL Certificate\n";
    echo "--------------------------\n";
    $certContent = $manager->readSecrets('ssl_certificate.pem');
    $lines = explode("\n", $certContent);
    echo "   Certificate: {$lines[0]}\n";
    echo "   Length: " . strlen($certContent) . " bytes\n";
    echo "\n";

    // Demo 4: Read documentation
    echo "📚 Demo 4: API Documentation\n";
    echo "----------------------------\n";
    $docsContent = $manager->readSecrets('api_docs.md');
    $lines = explode("\n", $docsContent);
    echo "   Title: " . trim($lines[0], '# ') . "\n";
    echo "   Sections: " . count(array_filter($lines, function($line) { return strpos($line, '##') === 0; })) . "\n";
    echo "   Length: " . strlen($docsContent) . " bytes\n";
    echo "\n";

    // Demo 5: Show metadata
    echo "📊 Demo 5: Secrets Metadata\n";
    echo "---------------------------\n";
    $metadata = $manager->getMetadata();
    echo "   Created: {$metadata['created']}\n";
    echo "   Version: {$metadata['version']}\n";
    echo "   Total files: " . count($files) . "\n";
    echo "\n";

    echo "✅ PHP Integration Demo completed successfully!\n";
    echo "\n";
    echo "💡 Key Features Demonstrated:\n";
    echo "   ✓ Automatic password retrieval from keychain\n";
    echo "   ✓ Selective file extraction\n";
    echo "   ✓ Environment variable parsing\n";
    echo "   ✓ JSON configuration reading\n";
    echo "   ✓ Binary/text file handling\n";
    echo "   ✓ Metadata access\n";
    echo "\n";

    // Common integration patterns:
    echo "🔧 Common Integration Patterns:\n";
    echo "===============================\n";
    echo "\n";

    echo "// 1. Laravel .env loading:\n";
    echo "\$envVars = \$manager->readEnvFile('.env');\n";
    echo "foreach (\$envVars as \$key => \$value) {\n";
    echo "    putenv(\"\$key=\$value\");\n";
    echo "}\n\n";

    echo "// 2. Read database config:\n";
    echo "\$dbConfig = \$manager->readSecrets('config/database.json');\n";
    echo "\$config = json_decode(\$dbConfig, true);\n\n";

    echo "// 3. Read SSL certificate:\n";
    echo "\$cert = \$manager->readSecrets('ssl/certificate.pem');\n";
    echo "file_put_contents('/tmp/cert.pem', \$cert);\n\n";

} catch (Exception $e) {
    echo "❌ Error: " . $e->getMessage() . "\n";
    exit(1);
}
?>
