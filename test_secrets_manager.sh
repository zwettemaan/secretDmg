#!/bin/bash
#
# Cross-platform test runner for test_secrets_manager.py
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
    echo -e "${RED}❌ Error: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  Warning: $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  Info: $1${NC}"
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

# Main execution logic
main() {
    # Get the directory where this script is located
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    TEST_SCRIPT_PY="$SCRIPT_DIR/test_secrets_manager.py"

    # Check if test_secrets_manager.py exists
    if [[ ! -f "$TEST_SCRIPT_PY" ]]; then
        print_error "test_secrets_manager.py not found in $SCRIPT_DIR"
        echo "Please ensure test_secrets_manager.py is in the same directory as this script."
        exit 1
    fi

    # Find compatible Python
    PYTHON_CMD=$(find_python)

    if [[ -z "$PYTHON_CMD" ]]; then
        print_error "No compatible Python installation found!"
        echo "Please install Python 3.6+ and try again."
        echo "See: https://www.python.org/downloads/"
        exit 1
    fi

    # Show success message with version info
    PYTHON_VERSION=$(get_python_version "$PYTHON_CMD")
    print_success "Using $PYTHON_CMD (version $PYTHON_VERSION)"
    print_info "Running comprehensive test suite..."
    echo

    # Execute test_secrets_manager.py with all arguments
    exec "$PYTHON_CMD" "$TEST_SCRIPT_PY" "$@"
}

# Help message
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Secrets Manager Test Runner - Cross-Platform Wrapper Script"
    echo
    echo "This script automatically detects your Python installation and runs the test suite"
    echo
    echo "Usage: $0 [test options...]"
    echo
    echo "Examples:"
    echo "  $0                           # Run all tests"
    echo "  $0 --verbose                 # Run tests with verbose output"
    echo "  $0 --help                    # Show this help"
    echo
    exit 0
fi

# Run main function
main "$@"
