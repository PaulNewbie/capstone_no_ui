#!/bin/bash
# dashboard/install.sh - Install MotorPass Dashboard

echo "======================================"
echo "🚗 MOTORPASS DASHBOARD INSTALLER"
echo "======================================"

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "⚠️  Please don't run as root (sudo)"
   echo "   Run as: ./install.sh"
   exit 1
fi

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python
echo "🐍 Checking Python installation..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "✅ $PYTHON_VERSION"
else
    echo "❌ Python 3 not found!"
    exit 1
fi

# Check pip
echo "📦 Checking pip..."
if command_exists pip3; then
    echo "✅ pip3 found"
else
    echo "❌ pip3 not found!"
    echo "   Installing pip3..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
fi

# Install Python dependencies
echo ""
echo "📚 Installing Python dependencies..."
pip3 install flask==2.3.2
pip3 install flask-cors==4.0.0
pip3 install netifaces==0.11.0

# Create templates directory if not exists
echo ""
echo "📁 Creating directory structure..."
DASHBOARD_DIR="$(dirname "$0")"
mkdir -p "$DASHBOARD_DIR/templates"
mkdir -p "$DASHBOARD_DIR/static"

# Test database connection
echo ""
echo "🔍 Testing database connection..."
python3 "$DASHBOARD_DIR/test_connection.py"

# Create systemd service
echo ""
echo "🔧 Creating systemd service..."
read -p "Do you want to create auto-start service? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    MOTORPASS_PATH=$(dirname "$DASHBOARD_DIR")
    SERVICE_FILE="/tmp/motorpass-dashboard.service"
    
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=MotorPass Dashboard Web Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$MOTORPASS_PATH
ExecStart=/usr/bin/python3 $DASHBOARD_DIR/start_dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    echo "📝 Service file created"
    echo "   To install service, run:"
    echo "   sudo cp $SERVICE_FILE /etc/systemd/system/"
    echo "   sudo systemctl daemon-reload"
    echo "   sudo systemctl enable motorpass-dashboard"
    echo "   sudo systemctl start motorpass-dashboard"
fi

# Get network info
echo ""
echo "🌐 Network Information:"
hostname -I | awk '{print "   IP Address: " $1}'

# Final instructions
echo ""
echo "======================================"
echo "✅ INSTALLATION COMPLETE!"
echo "======================================"
echo ""
echo "To start the dashboard:"
echo "   python3 $DASHBOARD_DIR/start_dashboard.py"
echo ""
echo "To access from admin laptop:"
echo "   http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "Default credentials:"
echo "   Username: admin"
echo "   Password: motorpass123"
echo ""
echo "⚠️  Remember to change the default password!"
echo "======================================="