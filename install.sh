#!/bin/bash

# Exit on error
set -e

echo "Starting NohrTech Sigma Calculator installation..."

# Update package list and upgrade existing packages
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Apache and development packages first
echo "Installing Apache and development packages..."
sudo apt-get install -y \
    apache2 \
    apache2-dev \
    apache2-utils \
    build-essential

# Install Python and other dependencies
echo "Installing Python and other dependencies..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libapache2-mod-wsgi-py3 \
    git

# Check if we're in the project directory, if not clone it
if [ ! -f "requirements.txt" ]; then
    echo "Cloning repository..."
    git clone https://github.com/nohrtech/sigma-calculator.git
    cd sigma-calculator
fi

# Create virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create upload directory
echo "Creating upload directory..."
mkdir -p uploads
chmod 755 uploads

# Create instance directory for Flask session
echo "Creating Flask instance directory..."
mkdir -p instance
chmod 755 instance

# Create WSGI file
echo "Creating WSGI file..."
cat > wsgi.py << 'EOL'
import sys
import os

# Add application directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import Flask app
from app import app as application
EOL

# Create Apache configuration file
echo "Creating Apache configuration..."
sudo tee /etc/apache2/sites-available/sigma-calculator.conf << 'EOL'
<VirtualHost *:80>
    ServerName localhost
    
    WSGIDaemonProcess sigma-calculator python-path=/var/www/sigma-calculator:/var/www/sigma-calculator/venv/lib/python3.11/site-packages
    WSGIProcessGroup sigma-calculator
    WSGIScriptAlias / /var/www/sigma-calculator/wsgi.py

    <Directory /var/www/sigma-calculator>
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/sigma-calculator-error.log
    CustomLog ${APACHE_LOG_DIR}/sigma-calculator-access.log combined
</VirtualHost>
EOL

# Set up application in Apache directory
echo "Setting up application in Apache directory..."
sudo mkdir -p /var/www/sigma-calculator
sudo cp -r * /var/www/sigma-calculator/
sudo chown -R www-data:www-data /var/www/sigma-calculator
sudo chmod -R 755 /var/www/sigma-calculator

# Enable the site and required modules
echo "Enabling Apache configuration..."
sudo a2ensite sigma-calculator
sudo a2enmod wsgi
sudo a2dissite 000-default
sudo systemctl restart apache2

echo "Installation complete!"
echo
echo "The application should now be running at: http://localhost"
echo "If you need to make changes, the application files are in /var/www/sigma-calculator"
echo "Apache logs are in /var/log/apache2/sigma-calculator-{error,access}.log"
echo
echo "To update the application:"
echo "1. cd /var/www/sigma-calculator"
echo "2. sudo git pull"
echo "3. sudo systemctl restart apache2"
