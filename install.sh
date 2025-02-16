#!/bin/bash

# Exit on error
set -e

# Configuration
REPO_URL="https://github.com/nohrtech/sigma-calculator.git"
BRANCH="main"
APP_NAME="sigma-calculator"
APP_DIR="/var/www/$APP_NAME"
PYTHON_MIN_VERSION="3.6"
VENV_PYTHON_VERSION="3.11"  # Specific version for virtual environment

# Function to display status messages
status_message() {
    echo "----------------------------------------"
    echo "$1"
    echo "----------------------------------------"
}

# Function to check if a command succeeded
check_status() {
    if [ $? -eq 0 ]; then
        echo " Success: $1"
    else
        echo " Error: $1"
        exit 1
    fi
}

status_message "Starting NohrTech Sigma Calculator installation..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo " Error: Please run this script as root (using sudo)"
    exit 1
fi

# Check Python version
status_message "Checking Python version..."
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [ "$(printf '%s\n' "$PYTHON_MIN_VERSION" "$python_version" | sort -V | head -n1)" != "$PYTHON_MIN_VERSION" ]; then
    echo " Error: Python $PYTHON_MIN_VERSION or higher is required (found $python_version)"
    exit 1
fi
check_status "Python version check passed"

# Update package list and upgrade existing packages
status_message "Updating system packages..."
apt-get update
check_status "Updated package list"
apt-get upgrade -y
check_status "Upgraded existing packages"

# Install Apache and development packages
status_message "Installing Apache and development packages..."
apt-get install -y \
    apache2 \
    apache2-dev \
    apache2-utils \
    build-essential
check_status "Installed Apache and development packages"

# Install Python and other dependencies
status_message "Installing Python and other dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libapache2-mod-wsgi-py3 \
    git
check_status "Installed Python and other dependencies"

# Create backup of existing installation if it exists
if [ -d "$APP_DIR" ]; then
    status_message "Creating backup of existing installation..."
    backup_dir="$APP_DIR-backup-$(date +%Y%m%d_%H%M%S)"
    mv "$APP_DIR" "$backup_dir"
    check_status "Created backup at $backup_dir"
fi

# Clone repository
status_message "Cloning repository..."
git clone -b "$BRANCH" "$REPO_URL" "$APP_DIR"
check_status "Cloned repository"

# Navigate to application directory
cd "$APP_DIR"
check_status "Changed to application directory"

# Create virtual environment
status_message "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
check_status "Created and activated virtual environment"

# Upgrade pip
status_message "Upgrading pip..."
pip install --upgrade pip
check_status "Upgraded pip"

# Install Python dependencies
status_message "Installing Python dependencies..."
pip install -r requirements.txt
check_status "Installed Python dependencies"

# Create data directories
status_message "Creating data directories..."
mkdir -p data/uploads
mkdir -p data/results
chmod 755 data/uploads data/results
check_status "Created data directories"

# Create Apache configuration file
status_message "Creating Apache configuration..."
cat > "/etc/apache2/sites-available/$APP_NAME.conf" << EOL
<VirtualHost *:80>
    ServerName localhost
    
    WSGIDaemonProcess $APP_NAME python-path=$APP_DIR:$APP_DIR/venv/lib/python$VENV_PYTHON_VERSION/site-packages
    WSGIProcessGroup $APP_NAME
    WSGIScriptAlias / $APP_DIR/nohrtech_sigma.py

    <Directory $APP_DIR>
        Require all granted
        <Files nohrtech_sigma.py>
            Require all granted
        </Files>
    </Directory>

    ErrorLog \${APACHE_LOG_DIR}/$APP_NAME-error.log
    CustomLog \${APACHE_LOG_DIR}/$APP_NAME-access.log combined
</VirtualHost>
EOL
check_status "Created Apache configuration"

# Set up permissions
status_message "Setting up permissions..."
chown -R www-data:www-data "$APP_DIR"
chmod -R 755 "$APP_DIR"
chmod +x "$APP_DIR/nohrtech_sigma.py"
check_status "Set up permissions"

# Verify script functionality
status_message "Verifying script functionality..."
if ! python3 "$APP_DIR/nohrtech_sigma.py" --help >/dev/null 2>&1; then
    echo " Error: Script verification failed"
    exit 1
fi
check_status "Script verification passed"

# Enable the site and required modules
status_message "Enabling Apache configuration..."
a2ensite "$APP_NAME"
a2enmod wsgi
a2dissite 000-default
systemctl restart apache2
check_status "Enabled Apache configuration"

status_message "Installation Summary"
echo " Installation completed successfully!"
echo
echo "Application Details:"
echo "- Location: $APP_DIR"
echo "- Web URL: http://localhost"
echo "- Error Log: /var/log/apache2/$APP_NAME-error.log"
echo "- Access Log: /var/log/apache2/$APP_NAME-access.log"
echo
echo "To update the application:"
echo "1. cd $APP_DIR"
echo "2. sudo ./update.sh"
echo
echo "To test the installation:"
echo "python3 $APP_DIR/nohrtech_sigma.py --help"
echo
if [ -n "$backup_dir" ]; then
    echo "Backup of previous installation: $backup_dir"
fi
