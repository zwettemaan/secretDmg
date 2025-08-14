<?php
/**
 * PHP Secrets Manager Library
 * A PHP library for selectively extracting files from the Cross-Platform Secrets Manager
 * without requiring a full mount/unmount cycle.
 *
 * Compatible with secrets created by the Python secrets_manager.py tool.
 *
 * Usage example:
 *   $manager = new SecretsManager();
 *   $envContent = $manager->readSecrets('.env');
 *   $configContent = $manager->readSecrets('config/database.php');
 */

class SecretsManager {
    private $secretsFile;
    private $projectName;
    private $password;
    private $package;
    private $key;

    /**
     * Constructor
     * @param string $projectDir Directory containing the .projectname.secrets file (default: current directory)
     * @param string $password Password for decryption (optional, will prompt if not provided)
     */
    public function __construct($projectDir = null, $password = null) {
        $this->projectName = $this->detectProjectName($projectDir ?: getcwd());
        $this->secretsFile = ($projectDir ?: getcwd()) . '/.' . $this->projectName . '.secrets';
        $this->password = $password;
        $this->package = null;
        $this->key = null;
    }

    /**
     * Detect project name from directory or existing secrets file
     */
    private function detectProjectName($projectDir) {
        // First, look for existing .*.secrets files
        $files = glob($projectDir . '/.*.secrets');
        if (!empty($files)) {
            $filename = basename($files[0]);
            return substr($filename, 1, -8); // Remove leading '.' and trailing '.secrets'
        }

        // Fallback to directory name
        return basename($projectDir);
    }

    /**
     * Load and decrypt the secrets package
     */
    private function loadPackage() {
        if ($this->package !== null) {
            return true; // Already loaded
        }

        if (!file_exists($this->secretsFile)) {
            throw new Exception("Secrets file not found: {$this->secretsFile}");
        }

        $json = file_get_contents($this->secretsFile);
        $this->package = json_decode($json, true);

        if (!$this->package || !isset($this->package['metadata']) || !isset($this->package['files'])) {
            throw new Exception("Invalid secrets file format");
        }

        // Get password if not provided
        if ($this->password === null) {
            // Try to get password from credential store first
            $this->password = $this->getStoredPassword();

            // If no stored password, fall back to prompting (CLI only)
            if ($this->password === null) {
                if (php_sapi_name() === 'cli') {
                    $this->password = $this->getPasswordInput();
                } else {
                    throw new Exception("No stored password found and interactive input not available in web context. Please provide password in constructor or ensure password is stored in credential store.");
                }
            }
        }

        // Derive encryption key
        $salt = base64_decode($this->package['metadata']['salt']);
        $this->key = $this->deriveKey($this->password, $salt);

        return true;
    }

    /**
     * Get password input from user
     */
    private function getPasswordInput() {
        if (php_sapi_name() === 'cli') {
            echo "Enter password for project '{$this->projectName}': ";
            system('stty -echo');
            $password = trim(fgets(STDIN));
            system('stty echo');
            echo "\n";
            return $password;
        } else {
            throw new Exception("Password required for web context. Please provide password in constructor.");
        }
    }

    /**
     * Get password from platform-specific credential store
     * @return string|null Password if found, null otherwise
     */
    public function getStoredPassword() {
        $serviceName = $this->getKeychainEntryName();

        try {
            $os = $this->detectOS();

            if ($os === 'darwin') {
                // macOS - use security command
                $username = $this->getCurrentUser();
                $command = sprintf(
                    'security find-generic-password -s %s -a %s -w 2>/dev/null',
                    escapeshellarg($serviceName),
                    escapeshellarg($username)
                );

                $output = shell_exec($command);
                if ($output !== null && trim($output) !== '') {
                    return trim($output);
                }

            } elseif ($os === 'windows') {
                // Windows - use PowerShell to access Windows Credential Manager
                $command = sprintf(
                    'powershell -Command "try { $cred = Get-StoredCredential -Target %s -Type Generic -ErrorAction Stop; [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($cred.Password)) } catch { exit 1 }"',
                    escapeshellarg($serviceName)
                );

                $output = shell_exec($command . ' 2>nul');
                if ($output !== null && trim($output) !== '') {
                    return trim($output);
                }

            } else {
                // Linux - use encrypted file in home directory
                $username = $this->getCurrentUser();
                $credFile = $_SERVER['HOME'] . '/.' . $serviceName;

                if (file_exists($credFile)) {
                    $data = file_get_contents($credFile);
                    if (strlen($data) > 32) {
                        $salt = substr($data, 0, 32);
                        $encryptedPassword = substr($data, 32);

                        $key = $this->deriveKey($username, $salt);
                        $decrypted = $this->decryptData($encryptedPassword, $key);

                        if ($decrypted !== false) {
                            return $decrypted;
                        }
                    }
                }
            }

        } catch (Exception $e) {
            // Silently fail and return null
            error_log("Could not retrieve stored password: " . $e->getMessage());
        }

        return null;
    }

    /**
     * Get the keychain entry name (compatible with Python implementation)
     * @return string
     */
    private function getKeychainEntryName() {
        // Read from .secrets_keychain_entry file like Python implementation
        $configFile = '.secrets_keychain_entry';
        if (file_exists($configFile)) {
            $lines = file($configFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
            if (!empty($lines)) {
                return trim($lines[0]); // First line is the keychain entry name
            }
        }

        // Fallback to default naming convention
        return "secretdmg-{$this->projectName}";
    }

    /**
     * Detect the operating system
     * @return string 'darwin', 'windows', or 'linux'
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
     * @return string
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
     * Derive encryption key from password using PBKDF2 (compatible with Python implementation)
     */
    private function deriveKey($password, $salt) {
        return hash_pbkdf2('sha256', $password, $salt, 100000, 32, true);
    }

    /**
     * Decrypt data (compatible with Python XOR implementation)
     */
    private function decryptData($encryptedData, $key) {
        if (strlen($encryptedData) < 16) {
            return false;
        }

        $iv = substr($encryptedData, 0, 16);
        $encrypted = substr($encryptedData, 16);

        $decrypted = '';
        $keyLen = strlen($key);
        $ivLen = strlen($iv);
        $encryptedLen = strlen($encrypted);

        // Extend key to match data length
        $keyExtended = str_repeat($key, ceil($encryptedLen / $keyLen));
        $keyExtended = substr($keyExtended, 0, $encryptedLen);

        for ($i = 0; $i < $encryptedLen; $i++) {
            $decrypted .= chr(
                ord($encrypted[$i]) ^
                ord($keyExtended[$i]) ^
                ord($iv[$i % $ivLen])
            );
        }

        return $decrypted;
    }

    /**
     * Read and decrypt a specific file from the secrets
     * @param string $relativePath Relative path to the file within the secrets directory
     * @return string|false File content as string, or false if file not found or decryption failed
     */
    public function readSecrets($relativePath) {
        try {
            $this->loadPackage();

            // Normalize path separators for cross-platform compatibility
            $relativePath = str_replace('\\', '/', $relativePath);

            if (!isset($this->package['files'][$relativePath])) {
                return false; // File not found
            }

            $fileInfo = $this->package['files'][$relativePath];
            $encryptedContent = base64_decode($fileInfo['content']);

            $decryptedContent = $this->decryptData($encryptedContent, $this->key);

            if ($decryptedContent === false) {
                throw new Exception("Failed to decrypt file: {$relativePath}");
            }

            return $decryptedContent;

        } catch (Exception $e) {
            error_log("SecretsManager Error: " . $e->getMessage());
            return false;
        }
    }

    /**
     * List all available files in the secrets
     * @return array Array of relative file paths
     */
    public function listFiles() {
        try {
            $this->loadPackage();
            return array_keys($this->package['files']);
        } catch (Exception $e) {
            error_log("SecretsManager Error: " . $e->getMessage());
            return [];
        }
    }

    /**
     * Check if a specific file exists in the secrets
     * @param string $relativePath Relative path to check
     * @return bool True if file exists, false otherwise
     */
    public function fileExists($relativePath) {
        try {
            $this->loadPackage();
            $relativePath = str_replace('\\', '/', $relativePath);
            return isset($this->package['files'][$relativePath]);
        } catch (Exception $e) {
            return false;
        }
    }

    /**
     * Get metadata about the secrets package
     * @return array|false Metadata array or false on error
     */
    public function getMetadata() {
        try {
            $this->loadPackage();
            return $this->package['metadata'];
        } catch (Exception $e) {
            error_log("SecretsManager Error: " . $e->getMessage());
            return false;
        }
    }

    /**
     * Parse a .env file content and return as associative array
     * @param string $content The .env file content
     * @return array Associative array of environment variables
     */
    public static function parseEnvContent($content) {
        $lines = explode("\n", $content);
        $env = [];

        foreach ($lines as $line) {
            $line = trim($line);

            // Skip empty lines and comments
            if (empty($line) || $line[0] === '#') {
                continue;
            }

            // Parse KEY=VALUE
            $parts = explode('=', $line, 2);
            if (count($parts) === 2) {
                $key = trim($parts[0]);
                $value = trim($parts[1]);

                // Remove quotes if present
                if (($value[0] === '"' && $value[-1] === '"') ||
                    ($value[0] === "'" && $value[-1] === "'")) {
                    $value = substr($value, 1, -1);
                }

                $env[$key] = $value;
            }
        }

        return $env;
    }

    /**
     * Read and parse a .env file from secrets
     * @param string $envFile Relative path to .env file (default: '.env')
     * @return array|false Associative array of environment variables or false on error
     */
    public function readEnvFile($envFile = '.env') {
        $content = $this->readSecrets($envFile);
        if ($content === false) {
            return false;
        }

        return self::parseEnvContent($content);
    }
}

/**
 * Convenience function for quick access
 * @param string $relativePath Relative path to the file within secrets
 * @param string $projectDir Project directory (optional)
 * @param string $password Password (optional, will prompt if not provided)
 * @return string|false File content or false on error
 */
function read_secrets($relativePath, $projectDir = null, $password = null) {
    $manager = new SecretsManager($projectDir, $password);
    return $manager->readSecrets($relativePath);
}

/**
 * Convenience function for reading .env files
 * @param string $envFile Relative path to .env file (default: '.env')
 * @param string $projectDir Project directory (optional)
 * @param string $password Password (optional, will prompt if not provided)
 * @return array|false Environment variables array or false on error
 */
function read_env_secrets($envFile = '.env', $projectDir = null, $password = null) {
    $manager = new SecretsManager($projectDir, $password);
    return $manager->readEnvFile($envFile);
}
