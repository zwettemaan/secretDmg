#!/bin/bash
#
# Cross-platform wrapper script for secrets_manager.py
# Automatically detects Python executable and provides helpful error messages
#

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_error() {
    echo -e "${RED}Error: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}Warning: $1${NC}"
}

print_info() {
    echo -e "${BLUE}Info: $1${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get Python version
get_python_version() {
    local python_cmd="$1"
    if command_exists "$python_cmd"; then
        local version=$($python_cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
        echo "$version"
    else
        echo ""
    fi
}

# Function to check Python version compatibility
is_python_compatible() {
    local version="$1"
    if [[ -n "$version" ]]; then
        local major=$(echo "$version" | cut -d. -f1)
        local minor=$(echo "$version" | cut -d. -f2)
        if [[ $major -gt 3 ]] || [[ $major -eq 3 && $minor -ge 6 ]]; then
            return 0
        fi
    fi
    return 1
}

# Function to find the best Python executable
find_python() {
    local python_candidates=("python3" "python" "python3.12" "python3.11" "python3.10" "python3.9" "python3.8" "python3.7" "python3.6")

    for cmd in "${python_candidates[@]}"; do
        if command_exists "$cmd"; then
            local version=$(get_python_version "$cmd")
            if is_python_compatible "$version"; then
                echo "$cmd"
                return 0
            else
                print_warning "Found $cmd (version $version) but requires Python 3.6+"
            fi
        fi
    done

    return 1
}

# Function to provide installation guidance
provide_installation_guidance() {
    echo
    print_error "No compatible Python installation found!"
    echo
    echo "The secrets manager requires Python 3.6 or later. Here's how to install it:"
    echo

    # Detect OS and provide specific guidance
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        echo "macOS Installation Options:"
        echo "  1. Homebrew (recommended):"
        echo "     brew install python3"
        echo
        echo "  2. Official installer:"
        echo "     Download from https://www.python.org/downloads/"
        echo
        echo "  3. Xcode Command Line Tools:"
        echo "     xcode-select --install"

    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        echo "Linux Installation Options:"
        if command_exists apt-get; then
            echo "  Ubuntu/Debian:"
            echo "    sudo apt-get update && sudo apt-get install python3 python3-pip"
        elif command_exists yum; then
            echo "  CentOS/RHEL:"
            echo "    sudo yum install python3 python3-pip"
        elif command_exists dnf; then
            echo "  Fedora:"
            echo "    sudo dnf install python3 python3-pip"
        elif command_exists pacman; then
            echo "  Arch Linux:"
            echo "    sudo pacman -S python python-pip"
        else
            echo "  Use your distribution's package manager to install python3"
        fi

    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        # Windows (Git Bash/Cygwin)
        echo "Windows Installation Options:"
        echo "  1. Official installer (recommended):"
        echo "     Download from https://www.python.org/downloads/"
        echo "     Make sure to check 'Add Python to PATH' during installation"
        echo
        echo "  2. Microsoft Store:"
        echo "     Search for 'Python 3' in Microsoft Store"
        echo
        echo "  3. Chocolatey:"
        echo "     choco install python3"

    else
        echo "General Installation:"
        echo "  Download Python from https://www.python.org/downloads/"
    fi

    echo
    echo "After installation, restart your terminal and try running this script again."
    echo
}

# Main execution logic
main() {
    # Get the directory where this script is located
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    SECRETS_MANAGER_PY="$SCRIPT_DIR/secrets_manager.py"

    # Check if secrets_manager.py exists
    if [[ ! -f "$SECRETS_MANAGER_PY" ]]; then
        print_error "secrets_manager.py not found in $SCRIPT_DIR"
        echo "Please ensure secrets_manager.py is in the same directory as this script."
        exit 1
    fi

    # Find compatible Python
    PYTHON_CMD=$(find_python)

    if [[ -z "$PYTHON_CMD" ]]; then
        provide_installation_guidance
        exit 1
    fi

    # Show success message with version info
    PYTHON_VERSION=$(get_python_version "$PYTHON_CMD")
    print_success "Using $PYTHON_CMD (version $PYTHON_VERSION)"

    # Execute secrets_manager.py with all arguments
    exec "$PYTHON_CMD" "$SECRETS_MANAGER_PY" "$@"
}

# Help message
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Secrets Manager - Cross-Platform Wrapper Script"
    echo
    echo "This script automatically detects your Python installation and runs secrets_manager.py"
    echo
    echo "Usage: $0 [secrets_manager.py arguments...]"
    echo
    echo "Examples:"
    echo "  $0 create                    # Create new secrets project"
    echo "  $0 mount                     # Decrypt secrets for editing"
    echo "  $0 unmount                   # Encrypt secrets for storage"
    echo "  $0 status                    # Show current status"
    echo "  $0 --help                    # Show this help"
    echo
    echo "For secrets_manager.py help: $0 --help-secrets"
    exit 0
fi

# Pass --help-secrets to the actual script
if [[ "$1" == "--help-secrets" ]]; then
    shift
    set -- "--help" "$@"
fi

# Run main function
main "$@"
