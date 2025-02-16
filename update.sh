#!/bin/bash

# Exit on error
set -e

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root (using sudo)"
    exit 1
fi

# Configuration
APP_NAME="sigma-calculator"
APP_DIR="/var/www/$APP_NAME"
BACKUP_DIR="/var/www/$APP_NAME-backup"
REPO_URL="https://github.com/nohrtech/sigma-calculator.git"
BRANCH="setup"  # Using setup branch
PYTHON_MIN_VERSION="3.6"

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

# Check Python version
status_message "Checking Python version..."
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [ "$(printf '%s\n' "$PYTHON_MIN_VERSION" "$python_version" | sort -V | head -n1)" != "$PYTHON_MIN_VERSION" ]; then
    echo "✗ Error: Python $PYTHON_MIN_VERSION or higher is required (found $python_version)"
    exit 1
fi
check_status "Python version check passed"

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
    
    # Set branch to setup
    git checkout -b "$BRANCH"
    check_status "Created $BRANCH branch"
fi

# Check if remote exists, add if not
if ! git remote get-url origin >/dev/null 2>&1; then
    git remote add origin "$REPO_URL"
    check_status "Added remote repository"
fi

# Reset any local changes and update remote
status_message "Resetting local changes..."
git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"
check_status "Reset to remote version"

# Fetch latest changes
status_message "Fetching latest changes..."
git fetch origin "$BRANCH"
check_status "Fetched latest changes"

# Get current version
current_version=$(git rev-parse HEAD)
echo "Current version: $current_version"

# Get latest version
latest_version=$(git rev-parse "origin/$BRANCH")
echo "Latest version: $latest_version"

if [ "$current_version" == "$latest_version" ]; then
    status_message "Already up to date!"
    exit 0
fi

# Update to latest version
status_message "Updating to latest version..."
git pull origin "$BRANCH"
check_status "Updated to latest version"

# Update Python dependencies
status_message "Updating Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --upgrade
check_status "Updated Python dependencies"

# Update permissions
status_message "Updating permissions..."
chown -R www-data:www-data "$APP_DIR"
chmod -R 755 "$APP_DIR"
chmod +x "$APP_DIR/nohrtech_sigma.py"
check_status "Updated permissions"

# Restart services
status_message "Restarting services..."
systemctl restart $APP_NAME
systemctl restart apache2
check_status "Restarted services"

# Verify services
status_message "Verifying services..."
if ! systemctl is-active --quiet apache2; then
    echo "✗ Error: Apache is not running"
    exit 1
fi
if ! systemctl is-active --quiet $APP_NAME; then
    echo "✗ Error: Flask service is not running"
    exit 1
fi
check_status "Services verified"

status_message "Update Summary"
echo "✓ Update completed successfully!"
echo
echo "Updated from version: ${current_version:0:7}"
echo "           to version: ${latest_version:0:7}"
echo
echo "Services Status:"
echo "- Apache: Running"
echo "- Flask: Running"
echo
echo "Backup Location:"
echo "$backup_path"
echo
echo "To verify the update:"
echo "1. Check web interface: http://localhost"
echo "2. Test command-line: nohrtech-sigma --help"
echo "3. View logs: tail -f /var/log/apache2/$APP_NAME-error.log"
