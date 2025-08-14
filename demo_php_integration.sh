#!/bin/bash

# PHP Integration Demo Script
# This script demonstrates the complete workflow:
# 1. Python creates and encrypts secrets
# 2. PHP reads and displays the secrets
# 3. Cleanup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Demo configuration
DEMO_DIR="php_demo_temp"
DEMO_PROJECT="PHPDemoProject"
DEMO_PASSWORD="demo123"
SCRIPT_DIR="$(pwd)"  # Store the original script directory

echo -e "${BLUE}🚀 PHP Secrets Manager Integration Demo${NC}"
echo -e "${BLUE}=====================================${NC}"
echo

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up demo files...${NC}"

    # Always go back to script directory first
    cd "$SCRIPT_DIR"

    # Clean up keychain entry if the config file exists
    if [ -d "$DEMO_DIR" ] && [ -f "$DEMO_DIR/.secrets_keychain_entry" ]; then
        KEYCHAIN_ENTRY=$(head -n 1 "$DEMO_DIR/.secrets_keychain_entry" 2>/dev/null)
        if [ -n "$KEYCHAIN_ENTRY" ]; then
            echo -e "${YELLOW}🔑 Removing keychain entry: $KEYCHAIN_ENTRY${NC}"
            security delete-generic-password -s "$KEYCHAIN_ENTRY" -a "$(whoami)" >/dev/null 2>&1 || true
            echo -e "${GREEN}✅ Removed keychain entry${NC}"
        fi
    fi

    # Remove demo directory
    if [ -d "$DEMO_DIR" ]; then
        echo -e "${YELLOW}📁 Removing demo directory: $DEMO_DIR${NC}"
        rm -rf "$DEMO_DIR"
        echo -e "${GREEN}✅ Removed demo directory${NC}"
    fi

    echo -e "${GREEN}✅ Demo cleanup completed${NC}"
}

# Set up cleanup trap
trap cleanup EXIT

echo -e "${BLUE}📁 Step 1: Setting up demo directory${NC}"
echo "Creating temporary demo directory: $DEMO_DIR"

# Create demo directory
mkdir -p "$DEMO_DIR"
cd "$DEMO_DIR"

# Copy necessary files to demo directory
cp ../secrets_manager.py .
cp ../SecretsManagerLib.php .

echo -e "${GREEN}✅ Demo directory created${NC}"
echo

echo -e "${BLUE}🔧 Step 2: Creating sample secret files${NC}"
echo "Setting up secrets with Python tool..."

# Create secrets using Python tool with test mode
echo "Creating secrets directory and adding sample files..."
python3 secrets_manager.py create --test-mode --project="$DEMO_PROJECT" --password="$DEMO_PASSWORD" > /dev/null

echo "Adding sample secret files..."

# Create sample .env file
cat > secrets/.env << EOF
# Database Configuration
DB_HOST=demo.example.com
DB_PORT=5432
DB_NAME=demo_app
DB_USER=demo_user
DB_PASS=super_secret_password_123

# API Keys
STRIPE_SECRET_KEY=sk_test_demo_key_123456789
SENDGRID_API_KEY=SG.demo_key.abc123def456
JWT_SECRET=your_super_secret_jwt_key_here

# External Services
REDIS_URL=redis://localhost:6379/0
ELASTICSEARCH_URL=http://localhost:9200
EOF

# Create sample config file
cat > secrets/database_config.json << EOF
{
  "database": {
    "primary": {
      "host": "primary-db.example.com",
      "port": 5432,
      "ssl": true,
      "pool_size": 10
    },
    "replica": {
      "host": "replica-db.example.com",
      "port": 5432,
      "ssl": true,
      "readonly": true
    }
  },
  "cache": {
    "redis": {
      "host": "cache.example.com",
      "port": 6379,
      "password": "cache_secret_123"
    }
  }
}
EOF

# Create sample certificate file
cat > secrets/ssl_certificate.pem << EOF
-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKoK/heBjcOuMA0GCSqGSIb3DQEBBQUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
aWRnaXRzIFB0eSBMdGQwHhcNMTcwODI4MDk0MzEwWhcNMTgwODI4MDk0MzEwWjBF
MQswCQYDVQQGEwJBVTETMBEGA1UECAwKU29tZS1TdGF0ZTEhMB8GA1UECgwYSW50
ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB
CgKCAQEAwMo
-----END CERTIFICATE-----
EOF

# Create API documentation
cat > secrets/api_docs.md << EOF
# API Documentation

## Authentication
- Use Bearer token: \`Bearer sk_test_demo_key_123456789\`
- Token expires every 24 hours

## Endpoints
- \`POST /api/v1/auth\` - Authentication
- \`GET /api/v1/users\` - List users
- \`POST /api/v1/users\` - Create user

## Rate Limits
- 1000 requests per hour per API key
- 100 requests per minute per IP

## Error Codes
- 401: Unauthorized
- 403: Forbidden
- 429: Rate limit exceeded
EOF

echo -e "${GREEN}✅ Sample secret files created${NC}"
echo

echo -e "${BLUE}🔒 Step 3: Encrypting secrets with Python${NC}"
echo "Packaging secrets into encrypted file..."

# Encrypt the secrets
python3 secrets_manager.py unmount > /dev/null

echo -e "${GREEN}✅ Secrets encrypted and packaged${NC}"
echo

echo -e "${BLUE}📝 Step 4: Setting up PHP demo script${NC}"

# Copy the standalone PHP example instead of creating duplicate code
cp ../php_example.php .

echo -e "${GREEN}✅ PHP demo script ready${NC}"
echo

echo -e "${BLUE}🚀 Step 5: Running PHP integration demo${NC}"
echo "Executing PHP script to read secrets..."
echo

# Run the PHP demo
php php_example.php

echo
echo -e "${BLUE}📋 Step 6: Demo Summary${NC}"
echo "========================"
echo -e "${GREEN}✅ Python tool successfully created and encrypted secrets${NC}"
echo -e "${GREEN}✅ PHP library successfully read all secret types:${NC}"
echo -e "   • Environment variables (.env)"
echo -e "   • JSON configuration files"
echo -e "   • SSL certificates (PEM files)"
echo -e "   • Markdown documentation"
echo -e "${GREEN}✅ Automatic credential store integration working${NC}"
echo -e "${GREEN}✅ No manual password entry required${NC}"
echo

echo -e "${YELLOW}🔧 Technical Details:${NC}"
echo -e "   • Secrets file: .${DEMO_PROJECT}.secrets"
echo -e "   • Keychain entry: Read from .secrets_keychain_entry"
echo -e "   • Encryption: XOR + PBKDF2 (compatible with Python)"
echo -e "   • Platform: macOS Keychain integration"

# Cleanup will happen automatically via trap
