"""
Cybersecurity Tools Dashboard
Professional Web Interface using Streamlit
"""

import streamlit as st
import subprocess
import sys
import os
import json
import time
import threading
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import re
import hashlib
import requests

# Add tools directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

# Page configuration
st.set_page_config(
    page_title="CyberSec Tools Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for light responsive theme
st.markdown("""
<style>
    /* Responsive design */
    .main {
        padding: 1rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        color: #2c3e50;
        min-height: 100vh;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Header styling */
    .cyber-header {
        background: linear-gradient(90deg, #3498db 0%, #2980b9 50%, #1abc9c 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: none;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .cyber-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    /* Card styling */
    .tool-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e3e6ea;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .tool-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.9);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e3e6ea;
        text-align: center;
        color: #2c3e50;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        background: rgba(52, 152, 219, 0.1);
        border-color: #3498db;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #3498db, #2980b9);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 2rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(52, 152, 219, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #2980b9, #1abc9c);
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(52, 152, 219, 0.4);
    }
    
    /* Results display */
    .results-container {
        background: white;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #3498db;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    
    .success-result {
        border-left-color: #27ae60;
        background: #f8fff9;
    }
    
    .error-result {
        border-left-color: #e74c3c;
        background: #fdf2f2;
    }
    
    .warning-result {
        border-left-color: #f39c12;
        background: #fffcf5;
    }
    
    /* Status indicators */
    .status-success { color: #27ae60; font-weight: bold; }
    .status-warning { color: #f39c12; font-weight: bold; }
    .status-error { color: #e74c3c; font-weight: bold; }
    .status-running { color: #3498db; font-weight: bold; }
    
    /* Responsive design for mobile */
    @media (max-width: 768px) {
        .main {
            padding: 0.5rem;
        }
        .cyber-header {
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .tool-card, .metric-card {
            padding: 1rem;
            margin: 0.5rem 0;
        }
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e3e6ea;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3498db;
        box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 2px solid #e3e6ea;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #3498db, #1abc9c);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.95);
        border-right: 1px solid #e3e6ea;
    }
</style>
""", unsafe_allow_html=True)

def get_tools_directory():
    """Get the absolute path to the tools directory"""
    current_dir = Path(__file__).parent
    return current_dir.parent / "tools"

def run_tool_command(tool_path, args, timeout=60):
    """Run a tool command and return the output"""
    try:
        cmd = [sys.executable, str(tool_path)] + args
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(tool_path.parent))
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", f"Command timed out after {timeout} seconds", 1
    except Exception as e:
        return "", f"Error running command: {str(e)}", 1

def display_results(stdout, stderr, returncode, tool_name=""):
    """Display results with proper formatting and status"""
    
    # Determine result type
    if returncode == 0 and not stderr:
        result_class = "success-result"
        status_class = "status-success"
        status_text = "✅ Success"
    elif stderr:
        result_class = "error-result"
        status_class = "status-error"
        status_text = "❌ Error"
    else:
        result_class = "warning-result" 
        status_class = "status-warning"
        status_text = "⚠️ Warning"
    
    # Create results container
    st.markdown(f"""
    <div class="results-container {result_class}">
        <h4>🔍 {tool_name} Results</h4>
        <p class="{status_class}">{status_text}</p>
        <div style="font-size: 0.9rem; color: #666;">
            <strong>Executed at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display output in organized sections
    if stdout:
        st.subheader("📊 Output")
        
        # Parse and format output based on tool type
        if tool_name.lower() == "hash cracker":
            display_hash_cracker_results(stdout)
        elif tool_name.lower() == "password checker":
            display_password_checker_results(stdout)
        elif tool_name.lower() == "port scanner":
            display_port_scanner_results(stdout)
        elif tool_name.lower() == "web scanner":
            display_web_scanner_results(stdout)
        else:
            # Generic output display
            st.code(stdout, language='text')
    
    if stderr:
        st.subheader("⚠️ Errors/Warnings")
        st.error(stderr)
    
    # Add export functionality
    if stdout or stderr:
        export_data = {
            "tool": tool_name,
            "timestamp": datetime.now().isoformat(),
            "output": stdout,
            "errors": stderr,
            "return_code": returncode
        }
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📄 Export as JSON", key=f"export_json_{tool_name}"):
                st.download_button(
                    label="Download JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"{tool_name.lower().replace(' ', '_')}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        with col2:
            if st.button("📊 Export as CSV", key=f"export_csv_{tool_name}"):
                df = pd.DataFrame([export_data])
                st.download_button(
                    label="Download CSV",
                    data=df.to_csv(index=False),
                    file_name=f"{tool_name.lower().replace(' ', '_')}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        with col3:
            if st.button("📝 Export as TXT", key=f"export_txt_{tool_name}"):
                txt_content = f"Tool: {tool_name}\nTimestamp: {datetime.now()}\n\nOutput:\n{stdout}\n\nErrors:\n{stderr}"
                st.download_button(
                    label="Download TXT",
                    data=txt_content,
                    file_name=f"{tool_name.lower().replace(' ', '_')}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )

def display_hash_cracker_results(output):
    """Display hash cracker results with structured formatting"""
    lines = output.split('\n')
    
    # Parse hash cracker output
    hash_info = {}
    cracked_password = None
    
    for line in lines:
        if 'Hash Type:' in line:
            hash_info['type'] = line.split(':', 1)[1].strip()
        elif 'Hash Length:' in line:
            hash_info['length'] = line.split(':', 1)[1].strip()
        elif 'Found:' in line or 'Password:' in line:
            cracked_password = line.split(':', 1)[1].strip() if ':' in line else line.strip()
        elif 'Time taken:' in line:
            hash_info['time'] = line.split(':', 1)[1].strip()
    
    # Display structured results
    if hash_info:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Hash Type", hash_info.get('type', 'Unknown'))
            st.metric("Hash Length", hash_info.get('length', 'Unknown'))
        with col2:
            if cracked_password:
                st.success(f"🔓 Password Found: **{cracked_password}**")
            else:
                st.warning("🔒 Password not found in wordlist")
            if 'time' in hash_info:
                st.metric("Time Taken", hash_info['time'])
    
    # Display full output
    with st.expander("View Full Output"):
        st.code(output, language='text')

def display_password_checker_results(output):
    """Display password checker results with visual indicators"""
    lines = output.split('\n')
    
    # Parse password checker output
    strength_score = None
    feedback = []
    breach_status = None
    
    for line in lines:
        if 'Strength Score:' in line or 'Score:' in line:
            try:
                score_text = line.split(':', 1)[1].strip()
                strength_score = float(score_text.split('/')[0])
            except:
                pass
        elif 'Feedback:' in line:
            feedback.append(line.split(':', 1)[1].strip())
        elif 'breach' in line.lower():
            breach_status = line.strip()
        elif line.strip() and not line.startswith('-'):
            feedback.append(line.strip())
    
    # Display strength meter
    if strength_score is not None:
        col1, col2 = st.columns([1, 2])
        with col1:
            # Create strength meter
            strength_percent = min(100, (strength_score / 10) * 100)
            color = '#e74c3c' if strength_score < 4 else '#f39c12' if strength_score < 7 else '#27ae60'
            
            st.markdown(f"""
            <div style="background: #f0f0f0; border-radius: 10px; padding: 10px; margin: 10px 0;">
                <h4>Password Strength</h4>
                <div style="background: #ddd; border-radius: 5px; height: 20px; overflow: hidden;">
                    <div style="background: {color}; height: 100%; width: {strength_percent}%; transition: width 0.3s ease;"></div>
                </div>
                <p><strong>{strength_score}/10</strong></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if feedback:
                st.subheader("💡 Recommendations")
                for item in feedback:
                    if item:
                        st.write(f"• {item}")
    
    # Display breach status
    if breach_status:
        if 'not found' in breach_status.lower():
            st.success("🛡️ Password not found in known breaches")
        else:
            st.error("⚠️ Password found in known breaches!")
    
    # Display full output
    with st.expander("View Full Analysis"):
        st.code(output, language='text')

def display_port_scanner_results(output):
    """Display port scanner results with interactive table"""
    lines = output.split('\n')
    
    # Parse port scanner output
    open_ports = []
    scan_info = {}
    
    for line in lines:
        if 'open' in line.lower() and ':' in line:
            try:
                parts = line.split()
                port = parts[0].replace(':', '')
                service = parts[1] if len(parts) > 1 else 'Unknown'
                open_ports.append({'Port': port, 'Service': service, 'Status': 'Open'})
            except:
                pass
        elif 'Target:' in line:
            scan_info['target'] = line.split(':', 1)[1].strip()
        elif 'Scan time:' in line:
            scan_info['scan_time'] = line.split(':', 1)[1].strip()
    
    # Display scan summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Target Host", scan_info.get('target', 'Unknown'))
    with col2:
        st.metric("Open Ports Found", len(open_ports))
    with col3:
        st.metric("Scan Duration", scan_info.get('scan_time', 'Unknown'))
    
    # Display open ports table
    if open_ports:
        st.subheader("🚪 Open Ports")
        df = pd.DataFrame(open_ports)
        st.dataframe(df, use_container_width=True)
        
        # Create port distribution chart
        if len(open_ports) > 0:
            port_nums = [int(p['Port']) for p in open_ports if p['Port'].isdigit()]
            if port_nums:
                fig = px.bar(x=port_nums, y=[1]*len(port_nums), 
                           title="Open Ports Distribution",
                           labels={'x': 'Port Number', 'y': 'Count'})
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No open ports found")
    
    # Display full output
    with st.expander("View Full Scan Output"):
        st.code(output, language='text')

def display_web_scanner_results(output):
    """Display web scanner results with vulnerability categorization"""
    lines = output.split('\n')
    
    # Parse web scanner output
    vulnerabilities = []
    scan_info = {}
    
    for line in lines:
        if any(vuln in line.lower() for vuln in ['sql', 'xss', 'csrf', 'injection', 'vulnerability']):
            vulnerabilities.append(line.strip())
        elif 'Target:' in line:
            scan_info['target'] = line.split(':', 1)[1].strip()
        elif 'Pages scanned:' in line:
            scan_info['pages'] = line.split(':', 1)[1].strip()
    
    # Display scan summary
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Target URL", scan_info.get('target', 'Unknown'))
    with col2:
        st.metric("Vulnerabilities Found", len(vulnerabilities))
    
    # Categorize and display vulnerabilities
    if vulnerabilities:
        st.subheader("🔍 Vulnerabilities Found")
        
        vuln_categories = {
            'SQL Injection': [],
            'XSS': [],
            'CSRF': [],
            'Other': []
        }
        
        for vuln in vulnerabilities:
            if 'sql' in vuln.lower():
                vuln_categories['SQL Injection'].append(vuln)
            elif 'xss' in vuln.lower():
                vuln_categories['XSS'].append(vuln)
            elif 'csrf' in vuln.lower():
                vuln_categories['CSRF'].append(vuln)
            else:
                vuln_categories['Other'].append(vuln)
        
        # Display by category
        for category, vulns in vuln_categories.items():
            if vulns:
                with st.expander(f"{category} ({len(vulns)} found)"):
                    for vuln in vulns:
                        st.warning(f"⚠️ {vuln}")
        
        # Create vulnerability chart
        vuln_counts = {k: len(v) for k, v in vuln_categories.items() if v}
        if vuln_counts:
            fig = px.pie(values=list(vuln_counts.values()), 
                        names=list(vuln_counts.keys()),
                        title="Vulnerability Distribution")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("✅ No vulnerabilities found")
    
    # Display full output
    with st.expander("View Full Scan Report"):
        st.code(output, language='text')

def main():
    # Header
    st.markdown("""
    <div class="cyber-header">
        <h1>🛡️ CYBERSECURITY TOOLS DASHBOARD 🛡️</h1>
        <p>Professional Security Testing & Analysis Platform</p>
        <p><strong>Status:</strong> <span class="success-text">SECURE CONNECTION ESTABLISHED</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.markdown("## 🔧 Tool Selection")
    
    tools = {
        "🔍 Overview": "overview",
        "🔐 Hash Cracker": "hash_cracker",
        "🛡️ Password Checker": "password_checker", 
        "🌐 Port Scanner": "port_scanner",
        "🕷️ Web Scanner": "web_scanner",
        "🚨 Intrusion Detection": "ids",
        "📡 Packet Sniffer": "packet_sniffer",
        "📊 Reports": "reports"
    }
    
    selected_tool = st.sidebar.selectbox("Choose Tool:", list(tools.keys()))
    
    # Get tools directory
    tools_dir = get_tools_directory()
    
    # Main content area
    if tools[selected_tool] == "overview":
        show_overview(tools_dir)
    elif tools[selected_tool] == "hash_cracker":
        show_hash_cracker(tools_dir)
    elif tools[selected_tool] == "password_checker":
        show_password_checker(tools_dir)
    elif tools[selected_tool] == "port_scanner":
        show_port_scanner(tools_dir)
    elif tools[selected_tool] == "web_scanner":
        show_web_scanner(tools_dir)
    elif tools[selected_tool] == "ids":
        show_ids(tools_dir)
    elif tools[selected_tool] == "packet_sniffer":
        show_packet_sniffer(tools_dir)
    elif tools[selected_tool] == "reports":
        show_reports()

def show_overview(tools_dir):
    """Display overview dashboard"""
    st.markdown("## 🔍 System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🔐 Password Tools</h3>
            <p>Hash Cracker</p>
            <p>Password Checker</p>
            <p><strong>Status: Active</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>🌐 Network Tools</h3>
            <p>Port Scanner</p>
            <p>IDS System</p>
            <p><strong>Status: Active</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>🕷️ Web Security</h3>
            <p>Web Scanner</p>
            <p>Vulnerability Detection</p>
            <p><strong>Status: Active</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>📡 Monitoring</h3>
            <p>Packet Sniffer</p>
            <p>Real-time Analysis</p>
            <p><strong>Status: Active</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("## ⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    with col1:        
        if st.button("🔍 Quick Port Scan", key="quick_port"): 
            st.markdown("### Running Quick Port Scan on localhost...")
            tool_path = tools_dir / "network" / "port_scanner.py"
            stdout, stderr, returncode = run_tool_command(tool_path, ["127.0.0.1", "80-443"])
            display_results(stdout, stderr, returncode, "Port Scanner")
    
    with col2:
        if st.button("🛡️ Test Password Strength", key="quick_password"):
            test_password = st.text_input("Enter password to test:", type="password", key="quick_pass_input")
            if test_password:
                tool_path = tools_dir / "password" / "password_checker.py"
                stdout, stderr, returncode = run_tool_command(tool_path, ["--password", test_password])
                display_results(stdout, stderr, returncode, "Password Checker")
    
    with col3:
        if st.button("🕷️ Quick Web Scan", key="quick_web"):
            test_url = st.text_input("Enter URL to scan:", key="quick_url_input")
            if test_url:
                tool_path = tools_dir / "web" / "web_scanner.py"
                stdout, stderr, returncode = run_tool_command(tool_path, [test_url])
                display_results(stdout, stderr, returncode, "Web Scanner")

def show_hash_cracker(tools_dir):
    """Display hash cracker interface"""
    st.markdown("## 🔐 Hash Cracker")
    st.markdown("Advanced hash cracking with multiple algorithm support")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        hash_input = st.text_input("Hash to crack:", placeholder="Enter hash here...")
        hash_type = st.selectbox("Hash Type:", ["auto", "md5", "sha1", "sha256", "sha512"])
        strategy = st.selectbox("Attack Strategy:", ["dictionary", "brute_force", "hybrid"])
        wordlist_option = st.selectbox("Wordlist:", ["Built-in", "NCSC Top 100k", "Custom"])
        
        if wordlist_option == "Custom":
            custom_wordlist = st.text_input("Wordlist path:", placeholder="Path to wordlist file")
    
    with col2:
        st.markdown("### Supported Hash Types")
        st.markdown("""
        - **MD5** - 32 character hex
        - **SHA1** - 40 character hex  
        - **SHA256** - 64 character hex
        - **SHA512** - 128 character hex
        - **Auto** - Automatic detection
        """)
        st.markdown("### Attack Strategies")
        st.markdown("""        - **Dictionary** - Uses wordlist-based attacks
        - **Brute Force** - Tries all possible combinations
        - **Hybrid** - Combines dictionary and brute force
        """)
        
        st.markdown("### Wordlist Options")
        st.markdown("""
        - **Built-in** - Small test wordlist (17 passwords)
        - **NCSC Top 100k** - Real-world pwned passwords (100,000 entries)
        - **Custom** - Your own wordlist file
        """)
        if st.button("🚀 Start Cracking", key="crack_hash"):
            if hash_input:
                tool_path = tools_dir / "password" / "hash_cracker.py"
                args = [hash_input, strategy]
                
                if hash_type != "auto":
                    args.extend(["--type", hash_type])
                  # Handle wordlist selection
                if wordlist_option == "Custom" and 'custom_wordlist' in locals():
                    args.extend(["--wordlist", custom_wordlist])
                elif wordlist_option == "Built-in":
                    # Use the built-in test wordlist
                    builtin_wordlist = tools_dir.parent / "test_wordlist.txt"
                    args.extend(["--wordlist", str(builtin_wordlist)])
                elif wordlist_option == "NCSC Top 100k":
                    # Use the NCSC Top 100k pwned passwords wordlist
                    ncsc_wordlist = tools_dir.parent / "ncsc_top100k.txt"
                    args.extend(["--wordlist", str(ncsc_wordlist)])
                
                with st.spinner("Cracking hash..."):
                    stdout, stderr, returncode = run_tool_command(tool_path, args)
                    display_results(stdout, stderr, returncode, "Hash Cracker")
            else:
                st.error("Please enter a hash to crack")

def show_password_checker(tools_dir):
    """Display password checker interface"""
    st.markdown("## 🛡️ Password Strength Checker")
    st.markdown("Advanced password analysis with breach detection")
    
    password_input = st.text_input("Password to check:", type="password", placeholder="Enter password...")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        check_breaches = st.checkbox("Check against known breaches", value=True)
        detailed_analysis = st.checkbox("Detailed analysis", value=True)
    
    with col2:
        st.markdown("### Security Features")
        st.markdown("""
        - **Strength Analysis** - Comprehensive scoring
        - **Breach Detection** - HaveIBeenPwned integration
        - **Pattern Recognition** - Common password patterns        - **Compliance** - NIST SP 800-63B standards
        """)
    
    if st.button("🔍 Analyze Password", key="check_password"):
        if password_input:
            tool_path = tools_dir / "password" / "password_checker.py"
            args = ["--password", password_input]
            
            with st.spinner("Analyzing password..."):
                stdout, stderr, returncode = run_tool_command(tool_path, args)
                display_results(stdout, stderr, returncode, "Password Checker")
        else:
            st.error("Please enter a password to check")

def show_port_scanner(tools_dir):
    """Display port scanner interface"""
    st.markdown("## 🌐 Advanced Port Scanner")
    st.markdown("High-performance network port scanning")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        target = st.text_input("Target Host:", placeholder="IP address or hostname (e.g., 192.168.1.1 or google.com)")
        st.caption("⚠️ Enter only the hostname or IP address. Port range is selected below.")
        scan_type = st.selectbox("Scan Type:", ["TCP", "UDP", "Both"])
        port_range = st.selectbox("Port Range:", ["Top 1000", "Top 100", "All Ports", "Custom"])
        
        if port_range == "Custom":
            custom_ports = st.text_input("Custom Ports:", placeholder="1-65535 or 80,443,8080")
    with col2:
        threads = st.slider("Threads:", 1, 100, 20)
        timeout = st.slider("Timeout (seconds):", 1, 10, 1)
        
        st.markdown("### Scan Features")
        st.markdown("""
        - **Multi-threading** - High-speed scanning
        - **Service Detection** - Identify running services
        - **OS Fingerprinting** - Basic OS detection
        - **Export Results** - JSON/CSV output
        """)
        
        st.markdown("### Performance Tips")
        st.markdown("""
        - **Lower timeout** = faster scans but may miss slow services
        - **More threads** = faster scanning (20-50 recommended)
        - **Top 100 ports** for quick scans
        """)
    
    if st.button("🚀 Start Scan", key="start_port_scan"):
        if target:
            # Clean and validate target input (remove any extra spaces or ports)
            target_clean = target.strip().split()[0]  # Take only the first part (hostname/IP)
            
            tool_path = tools_dir / "network" / "port_scanner.py"
            
            # Determine port range
            if port_range == "Top 100":
                ports = "1-100"
            elif port_range == "Top 1000":
                ports = "1-1000"
            elif port_range == "All Ports":
                ports = "1-65535"
            elif port_range == "Custom" and 'custom_ports' in locals():
                ports = custom_ports
            else:
                ports = "1-1000"  # Default fallback
            
            # Convert scan type to lowercase for the scanner
            scan_type_lower = scan_type.lower()
            
            # Build args: target, ports, then optional flags
            args = [target_clean, ports, "--threads", str(threads), "--timeout", str(timeout), "--type", scan_type_lower]
            
            st.info(f"🔍 Running: python {tool_path} {' '.join(args)}")
            with st.spinner(f"Scanning {target_clean}..."):
                # Use extended timeout for port scanning (up to 5 minutes)
                scan_timeout = 300 if port_range in ["Top 1000", "All Ports"] else 120
                stdout, stderr, returncode = run_tool_command(tool_path, args, timeout=scan_timeout)
                display_results(stdout, stderr, returncode, "port_scanner")
        else:
            st.error("Please enter a target host")

def show_web_scanner(tools_dir):
    """Display web scanner interface"""
    st.markdown("## 🕷️ Web Vulnerability Scanner")
    st.markdown("OWASP-compliant web application security testing")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        target_url = st.text_input("Target URL:", placeholder="https://example.com")
        scan_depth = st.slider("Crawling Depth:", 1, 5, 2)
        threads = st.slider("Number of Threads:", 1, 20, 10)
    
    with col2:
        timeout = st.slider("Request Timeout (seconds):", 5, 30, 10)
        
        st.markdown("### OWASP Top 10 Coverage")
        st.markdown("""
        - **A1** - Injection (SQL, XSS, Command)
        - **A2** - Broken Authentication
        - **A3** - Sensitive Data Exposure
        - **A4** - XML External Entities
        - **A5** - Broken Access Control
        - **A6** - Security Misconfiguration
        - **A7** - Cross-Site Scripting (XSS)
        - **A8** - Insecure Deserialization
        - **A9** - Known Vulnerable Components
        - **A10** - Insufficient Logging
        """)
    
    if st.button("🚀 Start Web Scan", key="start_web_scan"):
        if target_url:
            # Ensure URL has protocol
            if not target_url.startswith(('http://', 'https://')):
                target_url = 'https://' + target_url
            
            tool_path = tools_dir / "web" / "web_scanner.py"
            args = [target_url, "--timeout", str(timeout), "--threads", str(threads), "--depth", str(scan_depth)]
            
            st.info(f"🔍 Running: python {tool_path} {' '.join(args)}")
            
            with st.spinner(f"Scanning {target_url}..."):
                stdout, stderr, returncode = run_tool_command(tool_path, args)
                display_results(stdout, stderr, returncode, "web_scanner")
        else:
            st.error("Please enter a target URL")

def show_ids(tools_dir):
    """Display IDS interface"""
    st.markdown("## 🚨 Intrusion Detection System")
    st.markdown("Real-time network monitoring and threat detection")
    
    st.warning("⚠️ This tool requires administrator privileges")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        interface = st.text_input("Network Interface (optional):", placeholder="e.g., eth0, wlan0 (auto-detect if empty)")
        threshold = st.slider("Max Requests per Minute per IP:", 10, 500, 100)
        ban_time = st.slider("Ban Duration (seconds):", 60, 3600, 600)
        learning_period = st.slider("Learning Period (seconds):", 60, 1800, 300)
    
    with col2:
        st.markdown("### Detection Modules")
        enable_port_scan = st.checkbox("Port Scan Detection", value=True)
        enable_dos = st.checkbox("DoS Detection", value=True) 
        enable_anomaly = st.checkbox("Anomaly Detection", value=True)
        
        st.markdown("### Detection Capabilities")
        st.markdown("""
        - **Port Scanning** - Detect reconnaissance attempts
        - **DoS/DDoS** - Traffic flood detection
        - **Anomaly Detection** - Behavioral analysis
        - **Real-time Alerts** - Immediate notifications
        - **Auto-banning** - Automatic IP blocking
        """)
    
    if st.button("🚀 Start IDS Monitoring", key="start_ids"):
        tool_path = tools_dir / "network" / "ids.py"
        
        # Build arguments based on user selections
        args = ["--threshold", str(threshold), "--ban-time", str(ban_time), "--learning-period", str(learning_period)]
        
        # Add interface if specified
        if interface.strip():
            args.extend(["--interface", interface.strip()])
        
        # Add disable flags for unchecked detection modules
        if not enable_port_scan:
            args.append("--disable-port-scan")
        if not enable_dos:
            args.append("--disable-dos") 
        if not enable_anomaly:
            args.append("--disable-anomaly")
        
        st.info(f"🔍 Running: python {tool_path} {' '.join(args)}")
        st.info("Starting IDS system... (This may require admin privileges)")
        
        with st.spinner("Initializing IDS monitoring..."):
            stdout, stderr, returncode = run_tool_command(tool_path, args)
            display_results(stdout, stderr, returncode, "ids")

def show_packet_sniffer(tools_dir):
    """Display packet sniffer interface"""
    st.markdown("## 📡 Advanced Packet Sniffer")
    st.markdown("Deep packet inspection and network analysis")
    
    st.warning("⚠️ This tool requires administrator privileges")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        interface = st.selectbox("Network Interface:", ["auto", "eth0", "wlan0"], key="sniffer_interface")
        protocol_filter = st.multiselect("Protocol Filter:", ["TCP", "UDP", "ICMP", "HTTP", "HTTPS", "DNS"])
        packet_count = st.slider("Packet Count:", 10, 1000, 100)
    
    with col2:
        save_pcap = st.checkbox("Save to PCAP file")
        real_time = st.checkbox("Real-time analysis", value=True)
        
        st.markdown("### Analysis Features")
        st.markdown("""
        - **Protocol Decoding** - Layer 2-7 analysis
        - **Traffic Statistics** - Bandwidth monitoring
        - **Anomaly Detection** - Unusual patterns
        - **Export Options** - PCAP, JSON, CSV
        - **Live Filtering** - Dynamic packet filtering
        """)
    
    if st.button("🚀 Start Packet Capture", key="start_sniffer"):
        tool_path = tools_dir / "network" / "packet_sniffer.py"
        
        # Build arguments based on the actual packet sniffer script
        args = ["--count", str(packet_count), "--format", "json"]
        
        # Add interface if not auto
        if interface != "auto":
            args.extend(["--interface", interface])
        
        # Add protocol filters (the script uses --filter-protocol)
        if protocol_filter:
            args.extend(["--filter-protocol"] + [p.lower() for p in protocol_filter])
        
        # Add output file if saving
        if save_pcap:
            args.extend(["--output", f"packet_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"])
        
        st.info(f"🔍 Running: python {tool_path} {' '.join(args)}")
        st.info("Starting packet capture... (This requires admin privileges)")
        
        with st.spinner("Capturing packets..."):
            stdout, stderr, returncode = run_tool_command(tool_path, args)
            display_results(stdout, stderr, returncode, "packet_sniffer")

def show_reports():
    """Display reports and analytics"""
    st.markdown("## 📊 Security Reports & Analytics")
    
    # Sample data for visualization
    scan_data = {
        'Tool': ['Port Scanner', 'Web Scanner', 'Hash Cracker', 'Password Checker', 'IDS', 'Packet Sniffer'],
        'Success Rate': [95, 87, 78, 92, 89, 91],
        'Avg Runtime (s)': [12.5, 45.2, 5.8, 2.1, 0, 0],
        'Threats Detected': [23, 45, 12, 67, 89, 34]
    }
    
    df = pd.DataFrame(scan_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Success rate chart
        fig1 = px.bar(df, x='Tool', y='Success Rate', 
                     title='Tool Success Rates',
                     color='Success Rate',
                     color_continuous_scale='Viridis')
        fig1.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#00ff00'
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Threats detected pie chart
        fig2 = px.pie(df, values='Threats Detected', names='Tool',
                     title='Threats Detected by Tool')
        fig2.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#00ff00'
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Runtime performance
    fig3 = px.line(df, x='Tool', y='Avg Runtime (s)',
                  title='Average Runtime Performance',
                  markers=True)
    fig3.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#00ff00'
    )
    st.plotly_chart(fig3, use_container_width=True)
    
    # Recent scan history
    st.markdown("### 📈 Recent Scan History")
    
    history_data = {
        'Timestamp': ['2025-05-26 10:30:00', '2025-05-26 09:15:00', '2025-05-26 08:45:00'],
        'Tool': ['Port Scanner', 'Web Scanner', 'Hash Cracker'],
        'Target': ['192.168.1.1', 'https://testsite.com', 'MD5 Hash'],
        'Status': ['✅ Complete', '✅ Complete', '✅ Cracked'],
        'Findings': ['23 open ports', '5 vulnerabilities', 'Password: admin123']
    }
    
    history_df = pd.DataFrame(history_data)
    st.table(history_df)

if __name__ == "__main__":
    main()
