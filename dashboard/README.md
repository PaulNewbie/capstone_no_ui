# MotorPass Admin Dashboard

A local network web dashboard for monitoring MotorPass system in real-time.

## Features

- **Real-time Statistics**: View current people inside (students/guests)
- **Today's Summary**: See time in/out counts for the day
- **Live Updates**: Auto-refresh every 5 seconds
- **Time Records**: Browse and filter all time records
- **Reports**: Generate daily reports
- **Secure Access**: Password-protected admin access

## Setup Instructions

### 1. Install Required Packages

```bash
# Install Flask and dependencies
pip install flask flask-cors

# Optional: For better network detection
pip install netifaces
```

### 2. Directory Structure

Create the following structure in your MotorPass directory:
```
MotorPass/
├── dashboard/
│   ├── app.py              # Main Flask application
│   ├── start_dashboard.py  # Startup script
│   ├── templates/          # HTML templates
│   │   ├── base.html
│   │   ├── login.html
│   │   └── dashboard.html
│   └── README.md          # This file
├── database/              # Your existing database
├── main.py               # Your existing main app
└── ...
```

### 3. Configure Dashboard

Edit `dashboard/app.py` to change:
- Default admin password (line 15)
- Secret key (line 11)

### 4. Network Setup

Ensure your Raspberry Pi is connected to the school network:
- Via Ethernet cable (recommended for stability)
- Via WiFi

### 5. Start the Dashboard

```bash
# Navigate to MotorPass directory
cd /path/to/MotorPass

# Run the dashboard
python dashboard/start_dashboard.py
```

## Accessing the Dashboard

1. **Find your Raspberry Pi's IP address**:
   - The startup script will display it
   - Or run: `hostname -I`

2. **From Admin's Laptop**:
   - Open web browser
   - Go to: `http://<raspberry-pi-ip>:5000`
   - Example: `http://192.168.1.100:5000`

3. **Login**:
   - Username: `admin`
   - Password: `motorpass123` (change this!)

## Auto-Start Dashboard

To run dashboard automatically when Pi starts:

### Option 1: Using systemd (Recommended)

1. Create service file:
```bash
sudo nano /etc/systemd/system/motorpass-dashboard.service
```

2. Add content:
```ini
[Unit]
Description=MotorPass Dashboard
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/MotorPass
ExecStart=/usr/bin/python3 /home/pi/MotorPass/dashboard/start_dashboard.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Enable service:
```bash
sudo systemctl enable motorpass-dashboard.service
sudo systemctl start motorpass-dashboard.service
```

### Option 2: Using crontab

```bash
# Edit crontab
crontab -e

# Add line:
@reboot sleep 30 && cd /home/pi/MotorPass && python3 dashboard/start_dashboard.py
```

## Security Notes

1. **Change Default Password**: 
   - Edit `ADMIN_PASSWORD_HASH` in `app.py`
   - Use: `hashlib.sha256('your-new-password'.encode()).hexdigest()`

2. **Network Security**:
   - Dashboard only accessible within school network
   - Consider using VPN for remote access
   - Use HTTPS in production (with self-signed certificate)

3. **Firewall** (optional):
   ```bash
   # Allow only from admin's laptop IP
   sudo ufw allow from 192.168.1.50 to any port 5000
   ```

## Troubleshooting

### Dashboard not accessible:
1. Check if service is running: `ps aux | grep dashboard`
2. Check network: `ping <pi-ip>` from admin laptop
3. Check firewall: `sudo ufw status`
4. Check port: `sudo netstat -tlnp | grep 5000`

### Database errors:
1. Ensure main MotorPass system has initialized database
2. Check file permissions on database files

### Slow performance:
1. Reduce update interval in dashboard.html
2. Limit number of records shown
3. Use Ethernet instead of WiFi

## Dashboard Pages

### 1. **Dashboard** (`/`)
- Real-time statistics
- People currently inside
- Recent activities
- Today's summary

### 2. **Time Records** (`/time-records`)
- Browse all time records
- Filter by date range
- Filter by person type
- Export functionality (future)

### 3. **Reports** (`/reports`)
- Generate daily reports
- View historical reports
- Statistics and trends

### 4. **Settings** (`/settings`)
- System information
- Database statistics
- Configuration options

## API Endpoints

For custom integrations:

- `GET /api/dashboard-data` - Get current statistics
- `GET /api/recent-activities` - Get recent time records
- `GET /api/time-records` - Get filtered records
- `GET /api/generate-report` - Generate reports
- `GET /api/system-info` - Get system information

## Future Enhancements

- [ ] WebSocket for real-time updates
- [ ] Email alerts for specific events
- [ ] Export reports to PDF/Excel
- [ ] Multiple admin accounts
- [ ] Mobile-responsive improvements
- [ ] Charts and graphs
- [ ] Backup scheduling

## Support

For issues or questions:
1. Check the logs: `sudo journalctl -u motorpass-dashboard`
2. Check Flask logs in terminal
3. Verify database connectivity
4. Ensure network connectivity between Pi and admin laptop