#!/bin/bash

# Rpi-On-The-Fly Installer
# Downloads and installs the GPIO-controlled WiFi hotspot script as a systemd service

set -e

echo "=== Rpi-On-The-Fly Installer ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: This script must be run as root"
    echo "Please run: sudo bash install.sh"
    exit 1
fi

echo "Installing pyhotspot.py and systemd service..."

# Create install directory
INSTALL_DIR="/opt/rpi-hotspot"
SCRIPT_PATH="$INSTALL_DIR/pyhotspot.py"
SERVICE_FILE="/etc/systemd/system/pyhotspot.service"

# Update system and install dependencies
echo "Updating system and installing dependencies..."
apt update
apt install -y python3-rpi.gpio python3-pip git curl

echo "Installing Python LED library..."
pip3 install rpi-ws281x --break-system-packages 2>/dev/null || pip3 install rpi-ws281x

# Create directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Backup existing installation if present
if [ -f "$SCRIPT_PATH" ]; then
    echo "Backing up existing installation..."
    cp "$SCRIPT_PATH" "$SCRIPT_PATH.backup.$(date +%s)"
fi

# Download the Python script directly
echo "Downloading pyhotspot.py..."
curl -f -s -o pyhotspot.py https://raw.githubusercontent.com/Timon-sys/Rpi-On-The-Fly/main/pyhotspot.py

# Verify download succeeded
if [ ! -f "$SCRIPT_PATH" ] || [ ! -s "$SCRIPT_PATH" ]; then
    echo "ERROR: Failed to download script!"
    exit 1
fi

# Make executable and fix permissions
chmod +x pyhotspot.py
chown root:root pyhotspot.py

echo ""
echo "=== Configuration ==="
echo "The script has been downloaded to: $SCRIPT_PATH"
echo "You MUST edit the configuration at the top of the script before starting the service."
echo ""
read -p "Do you want to edit the configuration now? (y/n) [y]: " EDIT_NOW
EDIT_NOW=${EDIT_NOW:-y}

if [[ $EDIT_NOW == "y" ]]; then
    # Use nano if available, otherwise vi
    if command -v nano &> /dev/null; then
        nano "$SCRIPT_PATH"
    else
        vi "$SCRIPT_PATH"
    fi
    echo ""
    read -p "Configuration saved. Continue with installation? (y/n) [y]: " CONTINUE
    CONTINUE=${CONTINUE:-y}
    if [[ $CONTINUE != "y" ]]; then
        echo "Installation cancelled. Run this script again when ready."
        exit 0
    fi
fi

# Create systemd service file
echo "Creating systemd service..."
cat > "$SERVICE_FILE" << 'EOF'
[Unit]
Description=Pi Hotspot Switch Service
After=network-online.target NetworkManager.service
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
ExecStart=/usr/bin/python3 /opt/rpi-hotspot/pyhotspot.py
WorkingDirectory=/opt/rpi-hotspot
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
KillMode=process
TimeoutStopSec=30

# Environment variables
Environment=PYTHONUNBUFFERED=1

# Security settings
PrivateTmp=yes
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/opt/rpi-hotspot /var/log /run

[Install]
WantedBy=multi-user.target
EOF

# Set service permissions
chmod 644 "$SERVICE_FILE"

# Reload systemd and enable service
echo "Configuring systemd service..."
systemctl daemon-reload
systemctl enable pyhotspot.service



# Start the service
echo "Starting service..."
systemctl start pyhotspot.service
sleep 2

echo ""
echo "=== Installation Complete! ==="
echo ""

# Check if service actually started
if systemctl is-active --quiet pyhotspot.service; then
    echo "✓ Service is running successfully"
    echo ""
    systemctl status pyhotspot.service --no-pager -l
else
    echo "✗ WARNING: Service failed to start!"
    echo "Check the logs with: sudo journalctl -u pyhotspot.service -n 50"
    echo ""
fi

echo ""
echo "Key Information:"
echo "- Script location: $SCRIPT_PATH"
echo "- Service name: pyhotspot.service"
echo "- Edit configuration: sudo nano $SCRIPT_PATH"
echo ""
echo "Commands:"
echo "  sudo systemctl status pyhotspot.service"
echo "  sudo systemctl stop pyhotspot.service"
echo "  sudo systemctl start pyhotspot.service"
echo "  sudo systemctl restart pyhotspot.service"
echo "  sudo journalctl -u pyhotspot.service -f  (follow logs)"
echo ""
echo "Test GPIO: sudo python3 $SCRIPT_PATH test"
echo ""
echo "IMPORTANT: After editing the configuration, restart the service with:"
echo "  sudo systemctl restart pyhotspot.service"
echo ""
echo "Reboot to test autostart: sudo reboot"
echo ""