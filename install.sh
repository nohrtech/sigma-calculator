#!/bin/bash

# Exit on error
set -e

# Configuration
REPO_URL="https://github.com/nohrtech/sigma-calculator.git"
BRANCH="master"  # Using master branch
APP_NAME="sigma-calculator"
APP_DIR="/var/www/$APP_NAME"
PYTHON_MIN_VERSION="3.6"
FLASK_PORT="8000"
DOMAIN="localhost"

# Version management
VERSION_FILE="version.txt"
if [ -f "$VERSION_FILE" ]; then
    CURRENT_VERSION=$(cat "$VERSION_FILE")
    # Increment the last number in the version
    NEW_VERSION=$(echo "$CURRENT_VERSION" | awk -F. '{$NF = $NF + 1;} 1' | sed 's/ /./g')
    echo "$NEW_VERSION" > "$VERSION_FILE"
    INSTALL_VERSION="$NEW_VERSION"
else
    echo "1.0.0" > "$VERSION_FILE"
    INSTALL_VERSION="1.0.0"
fi

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

# Install mod_proxy_html module
apt-get install -y libapache2-mod-proxy-uwsgi || true

# Enable necessary Apache modules
a2enmod proxy
a2enmod proxy_html || true
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
git clone -b master https://github.com/nohrtech/sigma-calculator.git "$APP_DIR"
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
pip install gunicorn flask flask-session werkzeug
pip install -r requirements.txt
check_status "Installed Python dependencies"

# Create necessary directories with proper permissions
status_message "Creating application directories..."
mkdir -p instance
mkdir -p logs
mkdir -p "$APP_DIR/data"
mkdir -p "$APP_DIR/uploads"
mkdir -p "$APP_DIR/flask_session"
chmod 755 instance logs "$APP_DIR/data" "$APP_DIR/uploads" "$APP_DIR/flask_session"
chown -R www-data:www-data instance logs "$APP_DIR/data" "$APP_DIR/uploads" "$APP_DIR/flask_session"
check_status "Created application directories"

# Create log directory
mkdir -p "$APP_DIR/logs"
chown www-data:www-data "$APP_DIR/logs"

# Create WSGI file with error handling
status_message "Creating WSGI file..."
cat > "$APP_DIR/wsgi.py" << EOL
import sys
import logging

# Set up logging
logging.basicConfig(
    filename='logs/app.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)

try:
    from app import app
    logging.info("Successfully imported app")
except Exception as e:
    logging.error(f"Failed to import app: {str(e)}")
    logging.error(f"Python path: {sys.path}")
    raise

if __name__ == "__main__":
    app.run()
EOL
check_status "Created WSGI file"

# Set correct permissions
chown -R www-data:www-data "$APP_DIR/logs"
chmod -R 755 "$APP_DIR/logs"
chown www-data:www-data "$APP_DIR/wsgi.py"
chmod 644 "$APP_DIR/wsgi.py"

# Create Apache configuration
status_message "Creating Apache configuration..."
cat > "/etc/apache2/sites-available/$APP_NAME.conf" << EOL
<VirtualHost *:80>
    ServerName $DOMAIN
    ServerAdmin webmaster@localhost
    DocumentRoot $APP_DIR

    ErrorLog \${APACHE_LOG_DIR}/$APP_NAME-error.log
    CustomLog \${APACHE_LOG_DIR}/$APP_NAME-access.log combined

    <Directory $APP_DIR>
        Require all granted
    </Directory>

    ProxyRequests Off
    ProxyPreserveHost On
    
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    <Proxy *>
        Require all granted
    </Proxy>
</VirtualHost>
EOL
check_status "Created Apache configuration"

# Enable required Apache modules
status_message "Configuring Apache..."
a2enmod proxy
a2enmod proxy_http
a2enmod proxy_balancer
a2enmod lbmethod_byrequests

# Disable default site and enable our site
a2dissite 000-default
a2ensite "$APP_NAME"

# Test Apache configuration
apache2ctl configtest || {
    echo "Apache configuration test failed"
    exit 1
}

# Create systemd service file for Flask
status_message "Creating systemd service..."
cat > "/etc/systemd/system/$APP_NAME.service" << EOL
[Unit]
Description=NohrTech Sigma Calculator Flask App
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
RuntimeDirectory=gunicorn
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=$APP_DIR"
Environment="FLASK_APP=$APP_DIR/app.py"
Environment="FLASK_ENV=production"
Environment="LANG=C.UTF-8"
Environment="LC_ALL=C.UTF-8"

# Create required directories
ExecStartPre=/bin/mkdir -p $APP_DIR/logs
ExecStartPre=/bin/chown -R www-data:www-data $APP_DIR/logs
ExecStartPre=/bin/chmod 775 $APP_DIR/logs

# Start Gunicorn
ExecStart=$APP_DIR/venv/bin/gunicorn \
    --chdir $APP_DIR \
    --bind 127.0.0.1:8000 \
    --workers 1 \
    --log-level debug \
    --error-logfile $APP_DIR/logs/gunicorn-error.log \
    --access-logfile $APP_DIR/logs/gunicorn-access.log \
    --capture-output \
    app:app

# Restart settings
Restart=always
RestartSec=5

# Process management
KillMode=mixed
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
EOL

# Create a simple test Flask app
status_message "Creating test Flask app..."
cat > "$APP_DIR/app.py" << EOL
from flask import Flask
import logging
import os

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Set up logging
logging.basicConfig(
    filename='logs/app.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info('Starting application')
logger.info('Current directory: %s', os.getcwd())
logger.info('Python path: %s', os.getenv('PYTHONPATH'))

app = Flask(__name__)

@app.route('/')
def hello():
    logger.info('Handling request to /')
    return 'NohrTech Sigma Calculator is running!'

if __name__ == '__main__':
    app.run()
EOL

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -i:$port > /dev/null 2>&1; then
        echo "Port $port is already in use"
        echo "Checking processes using port $port:"
        lsof -i:$port
        return 1
    fi
    return 0
}

# Function to kill processes using a port
kill_port_processes() {
    local port=$1
    echo "Killing processes using port $port..."
    lsof -ti:$port | xargs kill -9 2>/dev/null || true
}

# Set up directories and permissions
status_message "Setting up directories..."
mkdir -p "$APP_DIR/logs"
chown -R www-data:www-data "$APP_DIR"
chmod -R 755 "$APP_DIR"
chmod -R 775 "$APP_DIR/logs"

# Install required Python packages
status_message "Installing Python packages..."
cd "$APP_DIR"
source "venv/bin/activate"
pip install --upgrade pip
pip install --no-cache-dir flask gunicorn

# Clean up any existing processes
status_message "Cleaning up existing processes..."
kill_port_processes 8000
sleep 2

# Check if port is available
if ! check_port 8000; then
    echo "Failed to free up port 8000"
    exit 1
fi

# Test gunicorn directly
status_message "Testing gunicorn directly..."
echo "Running test with gunicorn directly..."
$APP_DIR/venv/bin/gunicorn \
    --chdir $APP_DIR \
    --bind 127.0.0.1:8000 \
    --workers 1 \
    --log-level debug \
    --error-logfile $APP_DIR/logs/gunicorn-error.log \
    --access-logfile $APP_DIR/logs/gunicorn-access.log \
    --capture-output \
    app:app &

GUNICORN_PID=$!
sleep 5

# Test the direct connection
curl -s http://127.0.0.1:8000/ || {
    echo "Direct gunicorn test failed. Checking logs..."
    echo "=== Gunicorn Error Log ==="
    cat "$APP_DIR/logs/gunicorn-error.log"
    echo "=== App Log ==="
    cat "$APP_DIR/logs/app.log"
    kill -9 $GUNICORN_PID 2>/dev/null || true
    exit 1
}

# Kill test process and ensure it's gone
echo "Cleaning up test process..."
kill -9 $GUNICORN_PID 2>/dev/null || true
kill_port_processes 8000
sleep 2

# Verify port is free
if ! check_port 8000; then
    echo "Failed to free up port 8000 after test"
    exit 1
fi

# Restart services
status_message "Restarting services..."
systemctl daemon-reload
systemctl stop apache2 || true
systemctl stop $APP_NAME || true
sleep 2

# Start and verify Flask service
echo "Starting Flask service..."
systemctl start $APP_NAME
sleep 5

# Show detailed status and logs
echo "=== Systemd Service Status ==="
systemctl status $APP_NAME --no-pager
echo "=== Journal Log ==="
journalctl -u $APP_NAME --no-pager -n 50
echo "=== Gunicorn Error Log ==="
cat "$APP_DIR/logs/gunicorn-error.log"
echo "=== App Log ==="
cat "$APP_DIR/logs/app.log"

# Test Flask service
echo "Testing Flask service..."
for i in {1..10}; do
    if curl -s http://127.0.0.1:8000/ > /dev/null; then
        echo "Flask service is running"
        break
    fi
    echo "Waiting... ($i/10)"
    sleep 1
done

# Start Apache
systemctl start apache2 || {
    echo "Failed to start Apache. Checking logs..."
    cat "/var/log/apache2/$APP_NAME-error.log"
    exit 1
}

# Verify services are running
echo "Verifying services..."
if ! systemctl is-active --quiet $APP_NAME; then
    echo "Error: Flask service is not running"
    systemctl status $APP_NAME
    exit 1
fi

if ! systemctl is-active --quiet apache2; then
    echo "Error: Apache is not running"
    systemctl status apache2
    exit 1
fi

# Test connection
echo "Testing connection..."
curl -v http://127.0.0.1:8000/ || {
    echo "Error: Could not connect to Flask service"
    systemctl status $APP_NAME
    exit 1
}

status_message "Installation Summary"
echo " Installation completed successfully!"
echo " Version: $INSTALL_VERSION"
echo
echo "Application Details:"
echo "- Web Interface: http://$DOMAIN"
echo "- Command-line Tool: nohrtech-sigma"
echo "- Installation Directory: $APP_DIR"
echo "- Version: $INSTALL_VERSION"
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
