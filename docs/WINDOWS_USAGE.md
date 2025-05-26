# Windows Usage Guide for Cybersecurity Tools

## Quick Start - Windows Compatible Tools

All tools have been tested and work on Windows. Here's how to run each one:

### 🔍 **Port Scanner** (✅ Windows Compatible)

The port scanner works perfectly on Windows and scans target systems for open ports.

**Basic Usage:**
```powershell
# Scan common ports
python tools\network\port_scanner.py 192.168.1.1 1-1000

# Scan specific services
python tools\network\port_scanner.py google.com 80-443

# Fast scan with more threads
python tools\network\port_scanner.py 127.0.0.1 1-65535 --threads 200 --timeout 0.5
```

**Example Output:**
```
Starting port scan on google.com
Time started: 2025-05-26 09:49:26
Scanning ports 80 to 443 (364 ports)
==================================================
Resolved IP: 142.250.191.14
[OPEN] Port 80 - http
[OPEN] Port 443 - https
==================================================
Scan completed in 2.1 seconds
Open ports found: 2
  80: http
  443: https
```

### 🌐 **Web Vulnerability Scanner** (✅ Windows Compatible)

Detects security vulnerabilities in web applications.

**Usage:**
```powershell
# Basic vulnerability scan
python tools\web\web_scanner.py http://example.com --timeout 10

# Quick scan
python tools\web\web_scanner.py https://httpbin.org --timeout 5
```

**What it detects:**
- SQL Injection vulnerabilities
- Cross-Site Scripting (XSS)
- Directory traversal
- Missing security headers
- Server information disclosure

### 🔐 **Password Security Tools** (✅ Windows Compatible)

#### Password Strength Checker
```powershell
# Check password strength
python tools\password\password_checker.py --password "YourPassword123!"

# Interactive mode (secure input)
python tools\password\password_checker.py
```

#### Hash Cracker
```powershell
# Create a simple wordlist for testing
echo "password`ntest`n123456`nadmin`nletmein" > wordlist.txt

# Crack MD5 hash
python tools\password\hash_cracker.py 5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8 wordlist.txt --type md5

# Crack SHA256 hash with multiple threads
python tools\password\hash_cracker.py [hash] wordlist.txt --type sha256 --threads 8
```

### 🚨 **Network Monitoring Tools** (⚠️ Requires Administrator)

For network monitoring tools (IDS and Packet Sniffer), you need Administrator privileges on Windows.

#### Intrusion Detection System (Windows Version)
```powershell
# Run as Administrator in PowerShell
python tools\network\ids_windows.py --threshold 50 --ban-time 300
```

#### Packet Sniffer (Windows Version)
```powershell
# Run as Administrator in PowerShell
python tools\network\packet_sniffer_windows.py --protocol TCP
```

**To run as Administrator:**
1. Right-click on PowerShell
2. Select "Run as Administrator"
3. Navigate to your project directory
4. Run the commands

## 📋 Complete Testing Workflow

Here's a complete security testing workflow you can run on Windows:

```powershell
# 1. Navigate to project directory
cd Y:\projects\x\cyber\cybersecurity-tools

# 2. Test network connectivity and open ports
python tools\network\port_scanner.py google.com 80-443

# 3. Scan a web application for vulnerabilities
python tools\web\web_scanner.py https://httpbin.org

# 4. Check password strength
python tools\password\password_checker.py --password "TestPassword123!"

# 5. Create test hash and crack it
$hash = "5d41402abc4b2a76b9719d911017c592"  # MD5 of "hello"
echo "hello`nworld`ntest`npassword" > test_wordlist.txt
python tools\password\hash_cracker.py $hash test_wordlist.txt --type md5

# 6. For network monitoring (requires Admin rights):
# Start-Process powershell -Verb runAs
# python tools\network\ids_windows.py
```

## 🛠️ Troubleshooting

### Common Issues and Solutions:

1. **Permission Denied Errors:**
   ```
   Solution: Run PowerShell as Administrator for network tools
   ```

2. **Module Import Errors:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Socket Errors on Network Tools:**
   ```
   Solution: Use the Windows-specific versions:
   - tools\network\ids_windows.py
   - tools\network\packet_sniffer_windows.py
   ```

4. **Antivirus Blocking Tools:**
   ```
   Solution: Add exclusion for the cybersecurity-tools folder
   ```

## 🎯 Example Target Testing

### Safe Testing Targets:

```powershell
# Test on localhost
python tools\network\port_scanner.py 127.0.0.1 1-1000

# Test on public testing sites
python tools\web\web_scanner.py http://httpbin.org
python tools\web\web_scanner.py http://testphp.vulnweb.com

# Test DNS resolution
python tools\network\port_scanner.py google.com 53-53
```

### Creating Test Scenarios:

```powershell
# Create test hashes for practice
echo "5d41402abc4b2a76b9719d911017c592" > test_hashes.txt  # MD5 of "hello"
echo "aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d" >> test_hashes.txt  # SHA1 of "hello"

# Create wordlist
echo "hello`nworld`ntest`npassword`nadmin`nletmein" > common_passwords.txt

# Test cracking
python tools\password\hash_cracker.py 5d41402abc4b2a76b9719d911017c592 common_passwords.txt --type md5
```

## 📊 Performance Tips

### Port Scanner Optimization:
```powershell
# Fast scan (high threads, low timeout)
python tools\network\port_scanner.py target 1-1000 --threads 500 --timeout 0.3

# Thorough scan (low threads, high timeout)
python tools\network\port_scanner.py target 1-65535 --threads 50 --timeout 2.0
```

### Hash Cracker Optimization:
```powershell
# Use all CPU cores
python tools\password\hash_cracker.py [hash] wordlist.txt --threads 8
```

## 🔒 Legal and Ethical Usage

**IMPORTANT:** Only use these tools on:
- Your own systems
- Systems you have explicit written permission to test
- Designated testing environments
- Bug bounty programs with proper authorization

**Never use on:**
- Systems you don't own
- Networks without permission
- Production systems without approval
- Any target without explicit consent

## 📈 Advanced Usage

### Automated Scanning:
```powershell
# Create batch scan script
$targets = @("192.168.1.1", "192.168.1.100", "192.168.1.200")
foreach ($target in $targets) {
    python tools\network\port_scanner.py $target 1-1000
}
```

### Log Analysis:
```powershell
# View IDS logs
Get-Content ids.log -Tail 20

# View packet sniffer logs
Get-Content packet_sniffer.log -Tail 20

# View vulnerability scan logs
Get-Content vulnerability_scan.log -Tail 20
```

All tools are now fully compatible with Windows and ready to use!
