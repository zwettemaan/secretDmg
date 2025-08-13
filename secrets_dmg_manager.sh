#!/bin/bash

# Secrets DMG Manager
# Usage: ./secrets_dmg_manager.sh [create|mount|unmount|update|status] [log_level]
#
# Log Levels: 0=SILENT, 1=ERROR, 2=WARN, 3=INFO (default), 4=DEBUG
# Set via LOG_LEVEL environment variable or as second argument
#
# To see the password
# security find-generic-password -s "secrets_dmg_password" -a "$(whoami)@$(hostname)" -w 2>/dev/null || echo "Password not found (deleted successfully)"
# To delete the password for the DMG: 
# security delete-generic-password -s "secrets_dmg_password" -a "$(whoami)@$(hostname)"
#

set -eo pipefail

# Configuration
DMG_NAME="secrets"
DMG_FILE="${DMG_NAME}.dmg"
DMG_SIZE="10m"  # Adjust as needed
VOLUME_NAME="Secrets"
MOUNT_BASE="/tmp"
SECRETS_TEMPLATE_DIR="secrets_template"  # Directory with default files to include

# Security configuration
KEYCHAIN_SERVICE="${DMG_NAME}_dmg_password"
KEYCHAIN_ACCOUNT="$(whoami)@$(hostname)"

# Log levels: 0=SILENT, 1=ERROR, 2=WARN, 3=INFO, 4=DEBUG
# Default to WARN level (2) as requested
if [[ -z "${LOG_LEVEL:-}" ]]; then
    LOG_LEVEL=2
fi

# Validate LOG_LEVEL is numeric and in range, fallback to 2
if ! [[ "$LOG_LEVEL" =~ ^[0-4]$ ]]; then
    LOG_LEVEL=2
fi

# Global variables
MOUNT_POINT=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Logging functions with level support
log_debug() {
    [[ $LOG_LEVEL -ge 4 ]] && echo "[$(date '+%Y-%m-%d %H:%M:%S')] DEBUG: $1" >&2 || true
}

log_info() {
    [[ $LOG_LEVEL -ge 3 ]] && echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1" >&2 || true
}

log_warn() {
    [[ $LOG_LEVEL -ge 2 ]] && echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARN: $1" >&2 || true
}

log_error() {
    [[ $LOG_LEVEL -ge 1 ]] && echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2 || true
}

log_entry() {
    [[ $LOG_LEVEL -ge 4 ]] && echo "[$(date '+%Y-%m-%d %H:%M:%S')] ENTRY: $1" >&2 || true
}

log_exit() {
    [[ $LOG_LEVEL -ge 4 ]] && echo "[$(date '+%Y-%m-%d %H:%M:%S')] EXIT: $1" >&2 || true
}

# Show usage help
show_help() {
    echo "Usage: $0 [create|mount|unmount|update|status|export-password|import-password] [log_level]"
    echo ''
    echo 'Commands:'
    echo '  create         - Create new encrypted DMG (if it does not exist)'
    echo '  mount          - Mount DMG and export environment variables'
    echo '  unmount        - Unmount DMG'
    echo '  update         - Mount DMG for editing, then recreate with changes'
    echo '  status         - Show current status'
    echo '  export-password - Export DMG password from keychain'
    echo '  import-password [password] - Import DMG password to keychain'
    echo ''
    echo 'Log Levels (set via LOG_LEVEL env var or 2nd argument):'
    echo '  0 = SILENT, 1 = ERROR, 2 = WARN (default), 3 = INFO, 4 = DEBUG'
    echo ''
    echo 'Examples:'
    echo '  # Export password for transport'
    echo "  $0 export-password > dmg_password.txt"
    echo ''
    echo '  # Import password on another machine'
    echo "  $0 import-password \$(cat dmg_password.txt)"
    echo '  # Or interactively:'
    echo "  $0 import-password"
    echo ''
    echo '  # Regular usage'
    echo "  $0 mount 1        # Mount with error-level logging"
    echo "  eval \$($0 mount 1)  # For build scripts"
}

# Create a new DMG with minimal, consistent metadata
create_dmg() {
    local retVal=1
    log_entry "create_dmg"
    
    while true; do
        if [[ -f "$DMG_FILE" ]]; then
            log_error "DMG already exists: $DMG_FILE"
            break
        fi
        
        # Generate or get password for DMG encryption
        local dmg_password
        if ! dmg_password=$(security find-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" -w 2>/dev/null); then
            log_info "No existing password found, creating new one..."
            # Generate secure random password
            dmg_password=$(openssl rand -base64 32)
            # Store in keychain
            if ! security add-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" -w "$dmg_password"; then
                log_error "Failed to store password in keychain"
                break
            fi
            log_info "Password stored in keychain for service: $KEYCHAIN_SERVICE"
        else
            log_info "Using existing password from keychain"
        fi
        
        # Create temporary directory for DMG contents
        local temp_dir=$(mktemp -d)
        if [[ $? -ne 0 ]]; then
            log_error "Failed to create temporary directory"
            break
        fi
        
        # Copy template files if they exist
        if [[ -d "$SECRETS_TEMPLATE_DIR" ]]; then
            log_info "Copying template files from $SECRETS_TEMPLATE_DIR"
            if ! cp -R "$SECRETS_TEMPLATE_DIR"/* "$temp_dir/" 2>/dev/null; then
                log_warn "No template files found or copy failed, creating empty DMG"
            fi
        else
            log_info "No template directory found, creating empty DMG"
            echo '# Encrypted Secrets Storage' > "$temp_dir/README.txt"
            echo '# Place your signing certificates and related files here' >> "$temp_dir/README.txt"
        fi
        
        # Normalize timestamps to minimize git pollution
        find "$temp_dir" -exec touch -t 202301010000 {} \;
        
        # Create encrypted DMG
        log_info "Creating encrypted DMG: $DMG_FILE"
        if echo "$dmg_password" | hdiutil create \
            -srcfolder "$temp_dir" \
            -format UDZO \
            -encryption AES-256 \
            -stdinpass \
            -volname "$VOLUME_NAME" \
            -size "$DMG_SIZE" \
            -ov \
            -quiet \
            "$DMG_FILE"; then
            
            log_info "Encrypted DMG created successfully: $DMG_FILE"
            retVal=0
        else
            log_error "Failed to create encrypted DMG"
        fi
        
        # Cleanup
        rm -rf "$temp_dir"
        break
    done
    
    log_exit "create_dmg"
    return $retVal
}

# Find all mount points for our DMG file
find_dmg_mounts() {
    local dmg_path
    dmg_path=$(realpath "$DMG_FILE" 2>/dev/null) || dmg_path="$PWD/$DMG_FILE"
    
    # Get mount points for our specific DMG file
    hdiutil info | awk -v dmg="$dmg_path" '
    /^====/ { in_section = 1; mount_point = ""; next }
    in_section && /image-path/ && $3 == dmg { found_dmg = 1 }
    in_section && found_dmg && /mount-point/ { print $3; found_dmg = 0 }
    /^$/ { in_section = 0; found_dmg = 0 }
    '
}

# Unmount the DMG  
unmount_dmg() {
    local retVal=1
    log_entry "unmount_dmg"
    
    local full_dmg_path="$(realpath "$DMG_FILE")"
    log_debug "Looking for mounts of: $full_dmg_path"
    
    # Find mount points for this specific DMG only
    local mount_points=$(hdiutil info | awk -v target="$full_dmg_path" '
    /image-path.*:/ && $0 ~ target { found_image = 1; next }
    found_image && $NF ~ /^\/private\/tmp/ { print $NF; found_image = 0 }
    found_image && /^====/ { found_image = 0 }
    ')
    
    if [[ -z "$mount_points" ]]; then
        log_info "No mounted DMG found"
        retVal=0
    else
        echo "$mount_points" | while read mount_point; do
            if [[ -n "$mount_point" ]]; then
                log_info "Unmounting: $mount_point"
                hdiutil detach "$mount_point" -force
            fi
        done
        retVal=0
    fi
    
    log_exit "unmount_dmg"
    return $retVal
}

# Export password from keychain
export_password() {
    local retVal=1
    log_entry "export_password"
    
    while true; do
        local dmg_password
        if dmg_password=$(security find-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" -w 2>/dev/null); then
            echo "$dmg_password"
            log_info "Password exported successfully"
            retVal=0
        else
            log_error "Password not found in keychain for service: $KEYCHAIN_SERVICE"
            log_info "Run '$0 create' first to generate a password"
        fi
        break
    done
    
    log_exit "export_password"
    return $retVal
}

# Import password to keychain
import_password() {
    local retVal=1
    local password="$1"
    log_entry "import_password"
    
    while true; do
        if [[ -z "$password" ]]; then
            log_info "Enter password for DMG:"
            read -s password
            echo
        fi
        
        if [[ -z "$password" ]]; then
            log_error "No password provided"
            break
        fi
        
        # Remove existing password if it exists
        security delete-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" 2>/dev/null || true
        
        # Add new password
        if security add-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" -w "$password"; then
            log_info "Password imported successfully to keychain"
            retVal=0
        else
            log_error "Failed to store password in keychain"
        fi
        break
    done
    
    log_exit "import_password"
    return $retVal
}

# Mount the DMG
mount_dmg() {
    local retVal=1
    log_entry "mount_dmg"
    
    while true; do
        if [[ ! -f "$DMG_FILE" ]]; then
            log_error "DMG file not found: $DMG_FILE"
            break
        fi
        
        # Get password from keychain
        local dmg_password
        if ! dmg_password=$(security find-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" -w 2>/dev/null); then
            log_error "Password not found in keychain. DMG may not be encrypted or keychain access denied."
            break
        fi
        
        # Clean up any existing mounts first
        log_info "Cleaning up existing mounts..."
        unmount_dmg >/dev/null 2>&1
        
        # Use stable mount point based on project directory
        local project_name=$(basename "$(pwd)")
        MOUNT_POINT="${MOUNT_BASE}/${DMG_NAME}_${project_name}"
        
        # Remove any stale mount directory and create fresh
        if [[ -d "$MOUNT_POINT" ]]; then
            rmdir "$MOUNT_POINT" 2>/dev/null || true
        fi
        mkdir -p "$MOUNT_POINT"
        
        # Mount the encrypted DMG
        log_info "Mounting encrypted DMG to: $MOUNT_POINT"
        if echo "$dmg_password" | hdiutil attach "$DMG_FILE" -stdinpass -mountpoint "$MOUNT_POINT" -quiet; then
            echo "export SECRETS_MOUNT='$MOUNT_POINT'"
            echo "export SECRETS_PATH='$MOUNT_POINT'"
            log_info "Encrypted DMG mounted successfully"
            retVal=0
        else
            log_error "Failed to mount encrypted DMG"
            rmdir "$MOUNT_POINT" 2>/dev/null || true
        fi
        break
    done
    
    log_exit "mount_dmg"
    return $retVal
}

# Update DMG contents while preserving minimal metadata changes
update_dmg() {
    local retVal=1
    log_entry "update_dmg"
    
    while true; do
        if [[ ! -f "$DMG_FILE" ]]; then
            log_error "DMG file not found: $DMG_FILE"
            break
        fi
        
        # Mount for update
        if ! mount_dmg >/dev/null 2>&1; then
            log_error "Failed to mount DMG for update"
            break
        fi
        
        log_info "DMG mounted for update at: $MOUNT_POINT"
        log_info "Make your changes to files in: $MOUNT_POINT"
        log_info "Press Enter when done to create updated DMG..."
        read -r
        
        # Create backup
        local backup_file="${DMG_FILE}.backup.$(date +%s)"
        if ! cp "$DMG_FILE" "$backup_file"; then
            log_error "Failed to create backup"
            unmount_dmg >/dev/null 2>&1
            break
        fi
        
        # Create temporary directory for new DMG contents
        local temp_dir=$(mktemp -d)
        if [[ $? -ne 0 ]]; then
            log_error "Failed to create temporary directory"
            unmount_dmg >/dev/null 2>&1
            break
        fi
        
        # Copy updated contents
        if ! cp -R "$MOUNT_POINT"/* "$temp_dir/" 2>/dev/null; then
            log_error "Failed to copy updated contents"
            rm -rf "$temp_dir"
            unmount_dmg >/dev/null 2>&1
            break
        fi
        
        # Normalize timestamps to minimize git changes
        find "$temp_dir" -exec touch -t 202301010000 {} \;
        
        # Unmount old DMG
        if ! unmount_dmg >/dev/null 2>&1; then
            log_error "Failed to unmount DMG"
            rm -rf "$temp_dir"
            break
        fi
        
        # Remove old DMG and create new one
        rm "$DMG_FILE"
        
        if hdiutil create \
            -srcfolder "$temp_dir" \
            -format UDZO \
            -volname "$VOLUME_NAME" \
            -size "$DMG_SIZE" \
            -ov \
            -quiet \
            "$DMG_FILE"; then
            
            log_info "DMG updated successfully"
            rm "$backup_file"
            retVal=0
        else
            log_error "Failed to create updated DMG, restoring backup"
            mv "$backup_file" "$DMG_FILE"
        fi
        
        # Cleanup
        rm -rf "$temp_dir"
        break
    done
    
    log_exit "update_dmg"
    return $retVal
}

# Show status
show_status() {
    local retVal=0
    log_entry "show_status"
    
    echo "=== Secrets DMG Status ==="
    
    if [[ -f "$DMG_FILE" ]]; then
        echo "DMG File: $DMG_FILE ($(ls -lh "$DMG_FILE" | awk '{print $5}'))"
        echo "Modified: $(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$DMG_FILE")"
    else
        echo 'DMG File: Not found'
        echo "Run $0 create to create it"
    fi
    
    # Check if mounted
    local mounted_path=$(hdiutil info | grep -A 5 "$VOLUME_NAME" | grep "mount-point" | awk '{print $3}' | head -1)
    if [[ -n "$mounted_path" ]]; then
        echo "Status: Mounted at $mounted_path"
        echo "Contents:"
        ls -la "$mounted_path" 2>/dev/null || echo "  (Cannot list contents)"
    else
        echo "Status: Not mounted"
    fi
    
    log_exit "show_status"
    return $retVal
}

# Main function
main() {
    local retVal=1
    
    # If no arguments provided, show help
    if [[ $# -eq 0 ]]; then
        show_help
        return 0
    fi
    
    local action="$1"
    
    # Handle log level as second argument
    if [[ $# -ge 2 && "$2" =~ ^[0-4]$ ]]; then
        LOG_LEVEL="$2"
    fi
    
    log_entry "main($action)"
    log_debug "DMG_FILE=$DMG_FILE, LOG_LEVEL=$LOG_LEVEL"
    
    case "$action" in
        "create")
            if create_dmg; then
                retVal=0
            fi
            ;;
        "mount")
            if mount_dmg; then
                retVal=0
            fi
            ;;
        "unmount")
            if unmount_dmg; then
                retVal=0
            fi
            ;;
        "update")
            if update_dmg; then
                retVal=0
            fi
            ;;
        "status")
            if show_status; then
                retVal=0
            fi
            ;;
        "export-password")
            if export_password; then
                retVal=0
            fi
            ;;
        "import-password")
            if import_password "$2"; then
                retVal=0
            fi
            ;;
        "help"|"--help"|"-h")
            show_help
            retVal=0
            ;;
        *)
            echo "Error: Unknown command '$action'"
            echo "Run '$0' for usage information."
            retVal=1
            ;;
    esac
    
    log_exit "main"
    return $retVal
}

# Run main function
main "$@"