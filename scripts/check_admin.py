#!/usr/bin/env python3
"""
Admin Privilege Checker
Checks if the current process has administrator privileges and provides guidance.
"""

import os
import sys
import ctypes
import platform

def is_admin():
    """Check if the current process has administrator privileges"""
    try:
        if platform.system() == "Windows":
            # Windows: Check if running as administrator
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            # Unix/Linux: Check if running as root
            return os.geteuid() == 0
    except:
        return False

def get_elevation_command():
    """Get the command to run with elevated privileges"""
    if platform.system() == "Windows":
        # PowerShell command to run as administrator
        current_script = sys.argv[0] if sys.argv else "python"
        args = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
        return f'Start-Process powershell -Verb RunAs -ArgumentList "cd \'{os.getcwd()}\'; python {current_script} {args}"'
    else:
        # Unix/Linux: Use sudo
        return f"sudo {' '.join(sys.argv)}"

def require_admin(tool_name="this tool"):
    """Require administrator privileges or exit with instructions"""
    if not is_admin():
        print(f"❌ {tool_name} requires administrator privileges!")
        print(f"Current user: {os.getlogin() if hasattr(os, 'getlogin') else 'Unknown'}")
        print(f"Platform: {platform.system()}")
        print()
        
        if platform.system() == "Windows":
            print("🔧 Solutions:")
            print("1. Right-click PowerShell/Command Prompt → 'Run as administrator'")
            print("2. Use the elevation script:")
            print(f"   {get_elevation_command()}")
            print("3. Or run this PowerShell command:")
            print("   Start-Process powershell -Verb RunAs")
        else:
            print("🔧 Solution:")
            print(f"   {get_elevation_command()}")
        
        print("\n⚠️  Network monitoring tools require admin privileges to:")
        print("   • Create raw sockets")
        print("   • Monitor network interfaces")
        print("   • Access system-level network data")
        print("   • Implement real-time threat blocking")
        
        sys.exit(1)
    else:
        print(f"✅ Running with administrator privileges")
        return True

def main():
    """Main function to check admin status"""
    print("Administrator Privilege Checker")
    print("=" * 40)
    
    if is_admin():
        print("✅ Current process has administrator privileges")
        print(f"Platform: {platform.system()}")
        print(f"User: {os.getlogin() if hasattr(os, 'getlogin') else 'Administrator'}")
        print("\n🎯 You can now run network monitoring tools:")
        print("   • IDS (Intrusion Detection System)")
        print("   • Packet Sniffer")
        print("   • Advanced Network Analysis")
    else:
        require_admin("Cybersecurity Tools")

if __name__ == "__main__":
    main()
