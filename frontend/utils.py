"""
Dashboard Utilities
Helper functions for the cybersecurity tools dashboard
"""

import os
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
import streamlit as st

class DashboardUtils:
    """Utility class for dashboard operations"""
    
    def __init__(self, config_path="config.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.setup_logging()
    
    def load_config(self):
        """Load dashboard configuration"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                return self.get_default_config()
        except Exception as e:
            st.error(f"Error loading config: {e}")
            return self.get_default_config()
    
    def get_default_config(self):
        """Get default configuration"""
        return {
            "dashboard": {"title": "CyberSec Tools", "port": 8501},
            "security": {"timeout_seconds": 60},
            "tools": {},
            "logging": {"level": "INFO"}
        }
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config.get("logging", {}).get("level", "INFO"))
        log_file = self.config.get("logging", {}).get("file", "dashboard.log")
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def check_admin_privileges(self):
        """Check if running with administrator privileges"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            # For non-Windows systems
            return os.getuid() == 0
    
    def validate_ip(self, ip_address):
        """Validate IP address format"""
        import socket
        try:
            socket.inet_aton(ip_address)
            return True
        except socket.error:
            return False
    
    def validate_url(self, url):
        """Validate URL format"""
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    def format_scan_results(self, stdout, stderr, tool_name):
        """Format scan results for display"""
        results = {
            "tool": tool_name,
            "timestamp": datetime.now().isoformat(),
            "success": stderr == "",
            "output": stdout,
            "errors": stderr
        }
        
        # Tool-specific parsing
        if tool_name == "port_scanner":
            results["open_ports"] = self.parse_port_scan_results(stdout)
        elif tool_name == "web_scanner":
            results["vulnerabilities"] = self.parse_web_scan_results(stdout)
        elif tool_name == "hash_cracker":
            results["cracked"] = "Found:" in stdout
        
        return results
    
    def parse_port_scan_results(self, output):
        """Parse port scanner output"""
        open_ports = []
        for line in output.split('\n'):
            if 'open' in line.lower():
                try:
                    port = int(line.split()[0])
                    open_ports.append(port)
                except:
                    continue
        return open_ports
    
    def parse_web_scan_results(self, output):
        """Parse web scanner output"""
        vulnerabilities = []
        for line in output.split('\n'):
            if any(vuln in line.lower() for vuln in ['sql', 'xss', 'csrf', 'injection']):
                vulnerabilities.append(line.strip())
        return vulnerabilities
    
    def export_results(self, results, format_type="json", filename=None):
        """Export scan results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scan_results_{timestamp}.{format_type}"
        
        export_dir = Path(self.config.get("export", {}).get("output_directory", "exports"))
        export_dir.mkdir(exist_ok=True)
        filepath = export_dir / filename
        
        try:
            if format_type == "json":
                with open(filepath, 'w') as f:
                    json.dump(results, f, indent=2)
            elif format_type == "csv":
                import pandas as pd
                df = pd.DataFrame([results])
                df.to_csv(filepath, index=False)
            elif format_type == "txt":
                with open(filepath, 'w') as f:
                    f.write(str(results))
            
            return str(filepath)
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return None
    
    def get_system_info(self):
        """Get system information for dashboard"""
        import platform
        import psutil
        
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "python_version": sys.version,
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "disk_usage": psutil.disk_usage('/').percent
        }
    
    def create_scan_session(self):
        """Create a new scan session"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_data = {
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "scans": [],
            "status": "active"
        }
        return session_data
    
    def log_scan_activity(self, tool_name, target, status, duration=None):
        """Log scan activity"""
        activity = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "target": target,
            "status": status,
            "duration": duration
        }
        self.logger.info(f"Scan activity: {activity}")
        return activity

class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def sanitize_input(user_input):
        """Sanitize user input to prevent injection attacks"""
        if not isinstance(user_input, str):
            return str(user_input)
        
        # Remove potentially dangerous characters
        dangerous_chars = ['&', '|', ';', '$', '`', '<', '>', '(', ')', '{', '}']
        sanitized = user_input
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()
    
    @staticmethod
    def validate_command_args(args):
        """Validate command line arguments"""
        safe_args = []
        for arg in args:
            # Check for command injection attempts
            if any(dangerous in str(arg) for dangerous in ['rm ', 'del ', 'format', 'shutdown']):
                continue
            safe_args.append(SecurityValidator.sanitize_input(str(arg)))
        return safe_args
    
    @staticmethod
    def check_file_access(filepath):
        """Check if file can be safely accessed"""
        try:
            path = Path(filepath).resolve()
            # Ensure it's within allowed directories
            allowed_dirs = [Path.cwd(), Path.home()]
            return any(str(path).startswith(str(allowed)) for allowed in allowed_dirs)
        except:
            return False

def format_bytes(bytes_value):
    """Format bytes into human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def create_status_indicator(status):
    """Create status indicator with appropriate styling"""
    if status == "success":
        return "🟢 Success"
    elif status == "warning":
        return "🟡 Warning"
    elif status == "error":
        return "🔴 Error"
    elif status == "running":
        return "🔵 Running"
    else:
        return "⚪ Unknown"
