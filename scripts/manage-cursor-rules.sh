#!/bin/bash

# Script to manage MyCursorRules integration using Git subtree
# This ensures consistency across multiple machines and locations

set -e

# Configuration
MYCURSOR_REPO="https://github.com/ForeverNewLee/MyCursorRules.git"
SUBTREE_PREFIX="external-cursor-rules"
TARGET_DIR=".cursor/rules"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if we're in a git repository
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not in a git repository!"
        exit 1
    fi
}

# Function to add MyCursorRules as subtree
add_cursor_rules() {
    log_info "Adding MyCursorRules as subtree..."
    
    # Check if subtree already exists
    if [ -d "$SUBTREE_PREFIX" ]; then
        log_warning "Subtree directory already exists. Use 'update' or 'merge' instead."
        return 1
    fi
    
    # Add subtree
    git subtree add --prefix="$SUBTREE_PREFIX" --squash "$MYCURSOR_REPO" main
    
    log_success "MyCursorRules added as subtree to $SUBTREE_PREFIX"
}

# Function to update MyCursorRules subtree
update_cursor_rules() {
    log_info "Updating MyCursorRules subtree..."
    
    if [ ! -d "$SUBTREE_PREFIX" ]; then
        log_error "Subtree directory does not exist. Run 'add' first."
        return 1
    fi
    
    # Update subtree
    git subtree pull --prefix="$SUBTREE_PREFIX" --squash "$MYCURSOR_REPO" main
    
    log_success "MyCursorRules subtree updated"
}

# Function to backup current rules
backup_current_rules() {
    if [ -d "$TARGET_DIR" ]; then
        local backup_dir="${TARGET_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
        log_info "Backing up current rules to $backup_dir"
        cp -r "$TARGET_DIR" "$backup_dir"
        log_success "Backup created at $backup_dir"
        echo "$backup_dir"
    fi
}

# Function to merge rules (keeping both local and external)
merge_cursor_rules() {
    log_info "Merging cursor rules..."
    
    if [ ! -d "$SUBTREE_PREFIX" ]; then
        log_error "External rules not found. Run 'add' first."
        return 1
    fi
    
    # Create backup
    backup_dir=$(backup_current_rules)
    
    # Create target directory if it doesn't exist
    mkdir -p "$TARGET_DIR"
    
    # Copy external rules
    if [ -d "$SUBTREE_PREFIX/.cursor/rules" ]; then
        cp -r "$SUBTREE_PREFIX/.cursor/rules/"* "$TARGET_DIR/" 2>/dev/null || true
    elif [ -d "$SUBTREE_PREFIX" ]; then
        # If the external repo has rules directly in root
        find "$SUBTREE_PREFIX" -name "*.mdc" -exec cp {} "$TARGET_DIR/" \; 2>/dev/null || true
    fi
    
    # Merge with local rules (restore from backup if needed)
    if [ -n "$backup_dir" ] && [ -d "$backup_dir" ]; then
        log_info "Merging with existing local rules..."
        
        # Copy back local rules that don't conflict
        for local_file in "$backup_dir"/*; do
            if [ -f "$local_file" ]; then
                filename=$(basename "$local_file")
                target_file="$TARGET_DIR/$filename"
                
                if [ ! -f "$target_file" ]; then
                    # No conflict, copy local file
                    cp "$local_file" "$target_file"
                    log_info "Preserved local rule: $filename"
                else
                    # Conflict exists, create merged version
                    merge_rule_files "$local_file" "$target_file" "$target_file"
                fi
            fi
        done
    fi
    
    log_success "Rules merged successfully"
    log_info "Review the merged rules in $TARGET_DIR"
}

# Function to merge individual rule files
merge_rule_files() {
    local local_file="$1"
    local external_file="$2"
    local output_file="$3"
    
    local filename=$(basename "$local_file")
    log_info "Merging conflicting rule file: $filename"
    
    # Create a temporary merged file
    temp_file=$(mktemp)
    
    cat > "$temp_file" << EOF
# Merged Rules for $filename
# This file contains both local and external rules
# Please review and clean up as needed

# ========================================
# LOCAL RULES (from your project)
# ========================================

EOF
    
    cat "$local_file" >> "$temp_file"
    
    cat >> "$temp_file" << EOF

# ========================================
# EXTERNAL RULES (from MyCursorRules)
# ========================================

EOF
    
    cat "$external_file" >> "$temp_file"
    
    mv "$temp_file" "$output_file"
    log_warning "Merged file created with both local and external rules: $filename"
}

# Function to show status
show_status() {
    log_info "Cursor Rules Status:"
    echo ""
    
    if [ -d "$SUBTREE_PREFIX" ]; then
        log_success "✓ External rules subtree exists"
        
        # Show last update
        last_commit=$(git log --oneline -1 --grep="Squashed '$SUBTREE_PREFIX/'" 2>/dev/null || echo "Unknown")
        echo "  Last update: $last_commit"
    else
        log_warning "✗ External rules subtree not found"
    fi
    
    if [ -d "$TARGET_DIR" ]; then
        log_success "✓ Cursor rules directory exists"
        rule_count=$(find "$TARGET_DIR" -name "*.mdc" | wc -l)
        echo "  Rules count: $rule_count files"
        echo "  Files:"
        find "$TARGET_DIR" -name "*.mdc" -exec basename {} \; | sort | sed 's/^/    - /'
    else
        log_warning "✗ Cursor rules directory not found"
    fi
}

# Function to clean up
cleanup() {
    log_info "Cleaning up..."
    
    if [ -d "$SUBTREE_PREFIX" ]; then
        log_info "Removing subtree directory..."
        rm -rf "$SUBTREE_PREFIX"
        log_success "Subtree directory removed"
    fi
    
    # Remove any backup older than 7 days
    find "$(dirname "$TARGET_DIR")" -name "${TARGET_DIR##*/}_backup_*" -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null || true
    log_success "Old backups cleaned up"
}

# Function to show help
show_help() {
    cat << EOF
Usage: $0 [COMMAND]

Commands:
    add       Add MyCursorRules as subtree (first time setup)
    update    Update MyCursorRules subtree from remote
    merge     Merge external rules with local rules
    status    Show current status
    cleanup   Remove subtree directory and old backups
    help      Show this help message

Examples:
    $0 add      # First time setup
    $0 merge    # Merge external rules with local ones
    $0 update   # Update external rules
    $0 status   # Check current status

This script manages the integration of MyCursorRules repository
using Git subtree to ensure consistency across multiple machines.
EOF
}

# Main execution
main() {
    cd "$ROOT_DIR"
    check_git_repo
    
    case "${1:-help}" in
        "add")
            add_cursor_rules
            ;;
        "update")
            update_cursor_rules
            ;;
        "merge")
            merge_cursor_rules
            ;;
        "status")
            show_status
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@" 