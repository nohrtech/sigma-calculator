#!/bin/bash

# Exit on error
set -e

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root (using sudo)"
    exit 1
fi

# Configuration
APP_DIR="/var/www/sigma-calculator"
APACHE_ERROR_LOG="/var/log/apache2/sigma-calculator-error.log"
BACKUP_DIR="/var/www/sigma-calculator-backup"
REPO_URL="https://github.com/nohrtech/sigma-calculator.git"

# Function to display status messages
status_message() {
    echo "----------------------------------------"
    echo "$1"
    echo "----------------------------------------"
}

# Function to check if a command succeeded
check_status() {
    if [ $? -eq 0 ]; then
        echo "✓ Success: $1"
    else
        echo "✗ Error: $1"
        exit 1
    fi
}

# Create backup
status_message "Creating backup..."
timestamp=$(date +%Y%m%d_%H%M%S)
backup_path="$BACKUP_DIR/$timestamp"
mkdir -p "$backup_path"
cp -r "$APP_DIR"/* "$backup_path/"
check_status "Backup created at $backup_path"

# Navigate to application directory
status_message "Navigating to application directory..."
cd "$APP_DIR"
check_status "Changed directory to $APP_DIR"

# Initialize Git if needed
if [ ! -d ".git" ]; then
    status_message "Initializing Git repository..."
    git init
    check_status "Initialized Git repository"
    
    # Add remote repository
    git remote add origin "$REPO_URL"
    check_status "Added remote repository"
    
    # Set branch to main/master
    git checkout -b master
    check_status "Created master branch"
fi

# Check if remote exists, add if not
if ! git remote get-url origin >/dev/null 2>&1; then
    git remote add origin "$REPO_URL"
    check_status "Added remote repository"
fi

# Reset any local changes and update remote
status_message "Resetting local changes..."
git fetch origin master
git reset --hard origin/master
check_status "Reset to remote version"

# Fetch latest changes
status_message "Fetching latest changes..."
git fetch origin master
check_status "Fetched latest changes"

# Get current version
current_version=$(git rev-parse HEAD)
echo "Current version: $current_version"

# Get latest version
latest_version=$(git rev-parse origin/master)
echo "Latest version: $latest_version"

if [ "$current_version" == "$latest_version" ]; then
    status_message "Already up to date!"
    exit 0
fi

# Pull latest changes
status_message "Pulling latest changes..."
git pull origin master
check_status "Pulled latest changes"

# Update permissions
status_message "Updating file permissions..."
chown -R www-data:www-data "$APP_DIR"
chmod -R 755 "$APP_DIR"
check_status "Updated file permissions"

# Restart Apache
status_message "Restarting Apache..."
systemctl restart apache2
check_status "Restarted Apache"

# Check Apache status
status_message "Checking Apache status..."
apache_status=$(systemctl is-active apache2)
if [ "$apache_status" = "active" ]; then
    echo "✓ Apache is running"
else
    echo "✗ Warning: Apache is not running!"
    systemctl status apache2
    exit 1
fi

# Check for errors in log
status_message "Checking error log..."
if [ -f "$APACHE_ERROR_LOG" ]; then
    errors=$(tail -n 50 "$APACHE_ERROR_LOG" | grep -i "error\|exception" || true)
    if [ ! -z "$errors" ]; then
        echo "⚠ Warning: Found errors in log:"
        echo "$errors"
    else
        echo "✓ No recent errors found in log"
    fi
else
    echo "! Warning: Error log file not found"
fi

# Print summary
status_message "Update Summary"
echo "Previous version: $current_version"
echo "Current version:  $(git rev-parse HEAD)"
echo "Backup location:  $backup_path"
echo
echo "✓ Update completed successfully!"
echo "To rollback, run: cp -r $backup_path/* $APP_DIR/ && systemctl restart apache2"
