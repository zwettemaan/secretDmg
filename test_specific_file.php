<?php
require_once 'SecretsManagerLib.php';

// Test reading a specific file - this was the original user request
$manager = new SecretsManager();

echo "🎯 Testing selective file extraction\n";
echo "====================================\n\n";

// Extract just the .env file
try {
    $envContent = $manager->readSecrets('.env');
    echo "📄 Contents of .env file:\n";
    echo $envContent . "\n\n";

    // Parse the .env content
    $envVars = $manager->parseEnvContent($envContent);
    echo "🔑 Parsed environment variables:\n";
    foreach ($envVars as $key => $value) {
        echo "   $key = $value\n";
    }
    echo "\n";

} catch (Exception $e) {
    echo "❌ Error reading .env file: " . $e->getMessage() . "\n";
}

// Extract just the config.txt file
try {
    $configContent = $manager->readSecrets('config.txt');
    echo "📄 Contents of config.txt file:\n";
    echo $configContent . "\n\n";

} catch (Exception $e) {
    echo "❌ Error reading config.txt file: " . $e->getMessage() . "\n";
}

echo "✅ Selective extraction test completed!\n";
?>
