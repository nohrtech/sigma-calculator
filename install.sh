#!/bin/bash

# Exit on error
set -e

# Configuration
REPO_URL="https://github.com/nohrtech/sigma-calculator.git"
BRANCH="setup"  # Using setup branch
APP_NAME="sigma-calculator"
APP_DIR="/var/www/$APP_NAME"
PYTHON_MIN_VERSION="3.6"
FLASK_PORT="5000"
DOMAIN="localhost"

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
    build-essential \
    libxml2-dev
check_status "Installed Apache and development packages"

# Enable necessary Apache modules
a2enmod proxy_html
a2enmod proxy_http

# Install Python and other dependencies
status_message "Installing Python and other dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
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

# Upgrade pip and install dependencies
status_message "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # For production server
check_status "Installed Python dependencies"

# Create necessary directories
status_message "Creating application directories..."
mkdir -p instance
mkdir -p logs
mkdir -p "$APP_DIR/data"  # For storing uploaded files
chmod 755 instance logs "$APP_DIR/data"
check_status "Created application directories"

# Create systemd service file for Flask
status_message "Creating systemd service..."
cat > "/etc/systemd/system/$APP_NAME.service" << EOL
[Unit]
Description=NohrTech Sigma Calculator Flask App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind unix:$APP_DIR/$APP_NAME.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
EOL
check_status "Created systemd service"

# Create Apache configuration
status_message "Creating Apache configuration..."
cat > "/etc/apache2/sites-available/$APP_NAME.conf" << EOL
<VirtualHost *:80>
    ServerName $DOMAIN
    ServerAdmin webmaster@localhost
    DocumentRoot $APP_DIR

    ErrorLog \${APACHE_LOG_DIR}/$APP_NAME-error.log
    CustomLog \${APACHE_LOG_DIR}/$APP_NAME-access.log combined

    ProxyPreserveHost On
    ProxyPass / unix:$APP_DIR/$APP_NAME.sock|http://127.0.0.1/
    ProxyPassReverse / unix:$APP_DIR/$APP_NAME.sock|http://127.0.0.1/

    <Directory $APP_DIR>
        Options FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>

    <Directory $APP_DIR/static>
        Options FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>
</VirtualHost>
EOL
check_status "Created Apache configuration"

# Set up permissions
status_message "Setting up permissions..."
chown -R www-data:www-data "$APP_DIR"
chmod -R 755 "$APP_DIR"
chmod +x "$APP_DIR/nohrtech_sigma.py"
check_status "Set up permissions"

# Create symbolic link for command-line tool
status_message "Creating symbolic link..."
ln -sf "$APP_DIR/nohrtech_sigma.py" /usr/local/bin/nohrtech-sigma
check_status "Created symbolic link"

# Enable Apache modules and configure
status_message "Configuring Apache..."
a2enmod proxy
a2enmod proxy_balancer
a2enmod lbmethod_byrequests
a2ensite "$APP_NAME"
a2dissite 000-default
systemctl restart apache2
check_status "Configured Apache"

# Start and enable Flask service
status_message "Starting Flask service..."
systemctl start $APP_NAME
systemctl enable $APP_NAME
check_status "Started Flask service"

# Verify services
status_message "Verifying services..."
if ! systemctl is-active --quiet apache2; then
    echo " Error: Apache is not running"
    exit 1
fi
if ! systemctl is-active --quiet $APP_NAME; then
    echo " Error: Flask service is not running"
    exit 1
fi
check_status "Services verified"

status_message "Installation Summary"
echo " Installation completed successfully!"
echo
echo "Application Details:"
echo "- Web Interface: http://$DOMAIN"
echo "- Command-line Tool: nohrtech-sigma"
echo "- Installation Directory: $APP_DIR"
echo "- Log Files:"
echo "  * Apache: /var/log/apache2/$APP_NAME-error.log"
echo "  * Flask: $APP_DIR/logs/app.log"
echo
echo "Usage Examples:"
echo "1. Web Interface:"
echo "   Open http://$DOMAIN in your browser"
echo
echo "2. Command Line:"
echo "   nohrtech-sigma input.rnx"
echo "   nohrtech-sigma position.xyz"
echo
echo "Service Management:"
echo "- Restart Flask: sudo systemctl restart $APP_NAME"
echo "- Restart Apache: sudo systemctl restart apache2"
echo "- View Logs: tail -f /var/log/apache2/$APP_NAME-error.log"
echo
if [ -n "$backup_dir" ]; then
    echo "Backup of previous installation: $backup_dir"
fi
