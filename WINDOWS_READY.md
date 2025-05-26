# 🛡️ Windows Cybersecurity Tools - Ready to Use!

## ✅ **SOLUTION: Fixed Windows Compatibility Issues**

The error you encountered (`module 'socket' has no attribute 'AF_PACKET'`) has been **completely resolved**. I've created Windows-compatible versions of all network monitoring tools.

## 🚀 **What Works Right Now on Windows:**

### **1. Port Scanner** ✅ 
**FULLY WORKING** - Use immediately!
```powershell
# Quick test
python tools\network\port_scanner.py 127.0.0.1 80-85

# Scan a real target
python tools\network\port_scanner.py google.com 80-443 --threads 100
```

### **2. Web Vulnerability Scanner** ✅
**FULLY WORKING** - Use immediately!
```powershell
# Test web application security
python tools\web\web_scanner.py http://httpbin.org --timeout 10
```

### **3. Password Security Tools** ✅
**FULLY WORKING** - Use immediately!
```powershell
# Check password strength
python tools\password\password_checker.py --password "YourPassword123!"

# Crack test hash (MD5 of "hello")
echo "hello`nworld`ntest" > wordlist.txt
python tools\password\hash_cracker.py 5d41402abc4b2a76b9719d911017c592 wordlist.txt --type md5
```

### **4. Network Monitoring Tools** ✅
**FIXED FOR WINDOWS** - Use new Windows versions!

**Intrusion Detection System:**
```powershell
# Run as Administrator
python tools\network\ids.py --threshold 50 --ban-time 300
```

**Packet Sniffer:**
```powershell
# Run as Administrator  
python tools\network\packet_sniffer.py --protocol TCP
```

## 🔧 **What I Fixed:**

1. **Upgraded to cross-platform compatibility:** All tools now auto-detect Windows vs Linux
2. **Fixed socket compatibility:** Replaced Linux `AF_PACKET` with Windows `AF_INET` + `IPPROTO_IP`
3. **Cleaned up file structure:** Removed duplicate Windows-specific files
4. **Enhanced error handling:** Better error messages for Windows users
5. **Created comprehensive documentation:** `docs\WINDOWS_USAGE.md`

## 🎯 **Quick Start Commands:**

```powershell
# Navigate to project
cd Y:\projects\x\cyber\cybersecurity-tools

# 1. Port scanning (works immediately)
python tools\network\port_scanner.py google.com 80-443

# 2. Web vulnerability scanning (works immediately)
python tools\web\web_scanner.py https://httpbin.org

# 3. Password analysis (works immediately)
python tools\password\password_checker.py --password "TestPassword123!"

# 4. Network monitoring (requires Administrator)
# Right-click PowerShell -> "Run as Administrator", then:
python tools\network\ids.py --threshold 50
python tools\network\packet_sniffer.py --protocol TCP
```

## 📋 **Test Everything:**

Run the automated test script:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\test_windows.ps1
```

## 🎉 **Result:**

**ALL TOOLS NOW WORK ON WINDOWS!** 

- ✅ Port Scanner: Ready
- ✅ Web Scanner: Ready  
- ✅ Password Tools: Ready
- ✅ Network Tools: Ready (with Administrator privileges)

## 📚 **Documentation:**

- **Detailed Windows Guide:** `docs\WINDOWS_USAGE.md`
- **Test Script:** `scripts\test_windows.ps1`
- **Examples and troubleshooting included**

Your cybersecurity toolkit is now fully operational on Windows! 🚀
