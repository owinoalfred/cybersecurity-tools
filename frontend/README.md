# 🛡️ Cybersecurity Tools Dashboard

Professional web-based interface for cybersecurity tools using Streamlit.

## 🌟 Features

### 🎨 Modern UI/UX
- **Cybersecurity Theme** - Dark interface with green accent colors
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Real-time Updates** - Live status indicators and progress bars
- **Interactive Charts** - Plotly-powered visualizations

### 🔧 Tool Integration
- **Hash Cracker** - Advanced hash cracking with multiple algorithms
- **Password Checker** - Strength analysis with breach detection
- **Port Scanner** - High-performance network scanning
- **Web Scanner** - OWASP-compliant vulnerability detection
- **Intrusion Detection** - Real-time network monitoring
- **Packet Sniffer** - Deep packet inspection and analysis

### 📊 Analytics & Reporting
- **Performance Metrics** - Success rates and runtime statistics
- **Threat Visualization** - Interactive charts and graphs
- **Export Options** - JSON, CSV, and text formats
- **Scan History** - Complete audit trail

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Administrator privileges (for network tools)
- Internet connection (for dependency installation)

### Installation

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch dashboard:**
   ```bash
   streamlit run dashboard.py
   ```

### Alternative Launch Methods

**Windows Batch File:**
```batch
launch_dashboard.bat
```

**PowerShell (Cross-platform):**
```powershell
.\launch_dashboard.ps1
```

## 🖥️ Dashboard Interface

### 🏠 Overview Page
- System status indicators
- Quick action buttons
- Performance summaries
- Recent activity feed

### 🔐 Password Tools
- **Hash Cracker Interface**
  - Multiple hash type support
  - Custom wordlist options
  - Real-time cracking progress
  
- **Password Checker Interface**
  - Strength analysis scoring
  - Breach database checking
  - NIST compliance validation

### 🌐 Network Tools
- **Port Scanner Interface**
  - Target host selection
  - Scan type configuration
  - Thread and timeout settings
  - Real-time scan progress
  
- **IDS Interface**
  - Network interface selection
  - Detection mode configuration
  - Real-time alert monitoring

### 🕷️ Web Security
- **Web Scanner Interface**
  - URL target input
  - Scan depth configuration
  - OWASP vulnerability detection
  - Real-time progress tracking

### 📡 Monitoring Tools
- **Packet Sniffer Interface**
  - Network interface selection
  - Protocol filtering options
  - Real-time packet capture
  - Export to PCAP format

### 📊 Reports & Analytics
- **Performance Charts**
  - Tool success rates
  - Runtime statistics
  - Threat detection metrics
  
- **Scan History**
  - Complete audit trail
  - Exportable results
  - Search and filter options

## ⚙️ Configuration

### Dashboard Settings
Edit `config.json` to customize:
- Dashboard title and theme
- Security settings
- Tool configurations
- Logging preferences
- Export options

### Example Configuration
```json
{
    "dashboard": {
        "title": "CyberSec Tools Dashboard",
        "theme": "cybersecurity",
        "port": 8501
    },
    "security": {
        "timeout_seconds": 60,
        "max_concurrent_scans": 3
    },
    "tools": {
        "hash_cracker": {
            "enabled": true,
            "max_attempts": 1000000
        }
    }
}
```

## 🔒 Security Features

### Input Validation
- Sanitized user inputs
- Command injection prevention
- File access restrictions
- Network target validation

### Admin Privilege Management
- Automatic privilege detection
- Secure tool execution
- Permission-based feature access
- Cross-platform compatibility

### Audit Logging
- Complete activity logging
- Security event tracking
- Export compliance
- Forensic capabilities

## 🎯 Tool Usage Examples

### Quick Port Scan
1. Navigate to Port Scanner
2. Enter target IP: `192.168.1.1`
3. Select "Top 1000" ports
4. Click "Start Scan"
5. View real-time results

### Password Strength Check
1. Navigate to Password Checker
2. Enter password to test
3. Enable breach checking
4. Click "Analyze Password"
5. Review strength report

### Web Vulnerability Scan
1. Navigate to Web Scanner
2. Enter target URL: `https://testsite.com`
3. Select scan depth
4. Click "Start Web Scan"
5. Monitor vulnerability detection

## 📈 Performance Optimization

### Resource Management
- Concurrent scan limiting
- Memory usage monitoring
- CPU utilization tracking
- Network bandwidth control

### Caching
- Tool result caching
- Configuration caching
- Asset optimization
- Database indexing

## 🛠️ Troubleshooting

### Common Issues

**Dashboard won't start:**
- Check Python installation
- Verify dependencies installed
- Ensure port 8501 is available

**Network tools not working:**
- Run as administrator
- Check firewall settings
- Verify network interface names

**Performance issues:**
- Reduce concurrent scans
- Lower thread counts
- Increase timeout values

### Debug Mode
Enable debug logging in `config.json`:
```json
{
    "logging": {
        "level": "DEBUG",
        "file": "dashboard.log"
    }
}
```

## 📦 Dependencies

### Core Requirements
- `streamlit>=1.28.0` - Web dashboard framework
- `plotly>=5.15.0` - Interactive visualizations
- `pandas>=2.0.0` - Data manipulation
- `requests>=2.31.0` - HTTP requests
- `psutil>=5.9.0` - System monitoring
- `scapy>=2.5.0` - Packet manipulation

### Optional Dependencies
- `matplotlib` - Additional plotting
- `seaborn` - Statistical visualizations
- `numpy` - Numerical computing

## 🔄 Updates & Maintenance

### Updating Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Backup Configuration
```bash
cp config.json config.json.backup
```

### Log Rotation
Logs are automatically rotated based on size limits in configuration.

## 📝 License

This dashboard is part of the Cybersecurity Tools project and follows the same licensing terms.

## 🆘 Support

For issues or questions:
1. Check troubleshooting section
2. Review log files
3. Verify configuration settings
4. Test with minimal setup

---

**⚠️ Security Notice:** This dashboard provides access to powerful security tools. Use responsibly and only on systems you own or have explicit permission to test.
