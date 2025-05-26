import socket
import struct
import time
import json
import threading
import argparse
import sys
import platform
import re
import ctypes
import os
from collections import defaultdict, deque
from datetime import datetime, timedelta
import logging
import statistics
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from colorama import init, Fore, Style
import warnings

# Initialize colorama
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='advanced_ids.log'
)

def check_admin_privileges():
    """Check if running with administrator privileges"""
    try:
        if platform.system() == "Windows":
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            return os.geteuid() == 0
    except:
        return False

def require_admin():
    """Require administrator privileges or exit with instructions"""
    if not check_admin_privileges():
        print(f"{Fore.RED}[ERROR] Insufficient privileges. Run as Administrator/root.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Network monitoring requires administrator privileges to:{Style.RESET_ALL}")
        print("  • Create raw sockets")
        print("  • Monitor network interfaces") 
        print("  • Access low-level network data")
        print()
        if platform.system() == "Windows":
            print(f"{Fore.CYAN}Solutions:{Style.RESET_ALL}")
            print("1. Right-click PowerShell → 'Run as administrator'")
            print("2. Use admin launcher: scripts\\run_ids_admin.bat")
            print("3. Use PowerShell: scripts\\run_as_admin.ps1 ids")
        else:
            print(f"{Fore.CYAN}Solution:{Style.RESET_ALL}")
            print("Run with: sudo python -m tools.network.ids")
        sys.exit(1)
    return True

@dataclass
class NetworkEvent:
    """Represents a network event for analysis"""
    timestamp: float
    src_ip: str
    dst_ip: str
    protocol: str
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    packet_size: int = 0
    flags: Optional[str] = None

@dataclass
class ThreatSignature:
    """Represents a threat detection signature"""
    name: str
    pattern: str
    severity: str
    description: str
    action: str = "ALERT"

class AdvancedIDS:
    def __init__(self, threshold=100, ban_time=600, interface=None, learning_period=300):
        self.threshold = threshold
        self.ban_time = ban_time
        self.interface = interface
        self.learning_period = learning_period
        
        # Data structures for tracking
        self.request_counts = defaultdict(int)
        self.banned_ips = {}
        self.events_history = deque(maxlen=10000)  # Last 10k events
        self.ip_profiles = defaultdict(lambda: {
            'first_seen': time.time(),
            'packet_count': 0,
            'avg_packet_size': 0,
            'protocols': set(),
            'ports_accessed': set(),
            'connection_patterns': deque(maxlen=100)
        })
        
        # Behavioral baselines
        self.baseline_established = False
        self.baseline_start_time = time.time()
        self.normal_traffic_patterns = {}
        
        # Threat signatures
        self.threat_signatures = self._load_threat_signatures()
        
        # Statistics
        self.packet_count = 0
        self.alerts_generated = 0
        self.threats_blocked = 0
        self.last_reset = time.time()
        
        # Threading
        self.lock = threading.Lock()
        self.running = True
        
        # Advanced detection flags
        self.port_scan_detection = True
        self.dos_detection = True
        self.anomaly_detection = True
        self.geo_anomaly_detection = True

    def _load_threat_signatures(self) -> List[ThreatSignature]:
        """Load threat detection signatures"""
        signatures = [
            ThreatSignature(
                "SQL_INJECTION_ATTEMPT",
                r"(union.*select|drop.*table|exec.*xp_|script.*alert)",
                "HIGH",
                "Potential SQL injection or XSS attempt detected",
                "BLOCK"
            ),
            ThreatSignature(
                "BRUTE_FORCE_SSH",
                r"ssh.*failed.*authentication",
                "MEDIUM",
                "SSH brute force attempt detected",
                "MONITOR"
            ),
            ThreatSignature(
                "MALWARE_CALLBACK",
                r"(\.tk|\.ml|\.ga|\.cf).*\/[a-f0-9]{32}",
                "CRITICAL",
                "Potential malware callback detected",
                "BLOCK"
            ),
            ThreatSignature(
                "PORT_SCAN",
                r"tcp.*syn.*multiple_ports",
                "MEDIUM",
                "Port scanning activity detected",
                "MONITOR"
            ),
            ThreatSignature(
                "DGA_DOMAIN",
                r"[a-z]{10,}\.com",
                "LOW",
                "Potential DGA (Domain Generation Algorithm) domain",
                "ALERT"
            )
        ]
        return signatures

    def setup_socket(self):
        """Set up raw socket with advanced Windows compatibility"""
        try:
            if platform.system() == "Windows":
                # Windows raw socket setup
                conn = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                conn.bind((local_ip, 0))
                conn.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
                
                print(f"{Fore.CYAN}[INFO] Advanced Windows IDS Mode Activated{Style.RESET_ALL}")
                print(f"{Fore.CYAN}[INFO] Monitoring IP traffic on {local_ip}{Style.RESET_ALL}")
                return conn
            else:
                # Linux/Unix mode with enhanced error handling
                conn = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0003))
                if self.interface:
                    conn.bind((self.interface, 0))
                print(f"{Fore.CYAN}[INFO] Advanced Linux IDS Mode Activated{Style.RESET_ALL}")
                print(f"{Fore.CYAN}[INFO] Monitoring interface: {self.interface or 'all'}{Style.RESET_ALL}")
                return conn
                
        except PermissionError:
            print(f"{Fore.RED}[ERROR] Insufficient privileges. Run as Administrator/root.{Style.RESET_ALL}")
            sys.exit(1)
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Socket setup failed: {str(e)}{Style.RESET_ALL}")
            if platform.system() == "Windows":
                print(f"{Fore.YELLOW}[TIP] Ensure Windows firewall allows raw socket access{Style.RESET_ALL}")
            sys.exit(1)

    def parse_packet(self, data, is_windows=False):
        """Enhanced packet parsing with protocol-specific analysis"""
        try:
            if is_windows:
                # Windows: Direct IP packet
                ip_header = data[:20]
                version_ihl = struct.unpack('!B', ip_header[0:1])[0]
                version = version_ihl >> 4
                ihl = (version_ihl & 0xF) * 4
                
                if version != 4:
                    return None
                
                ttl, protocol, src, dst = struct.unpack('!8xBB2x4s4s', ip_header)
                src_ip = socket.inet_ntoa(src)
                dst_ip = socket.inet_ntoa(dst)
                
                # Parse transport layer
                transport_data = data[ihl:]
                src_port = dst_port = None
                flags = None
                
                if protocol == 6:  # TCP
                    if len(transport_data) >= 20:
                        src_port, dst_port, seq, ack, flags_window = struct.unpack('!HHLL H', transport_data[:14])
                        flags = self._parse_tcp_flags((flags_window >> 8) & 0xFF)
                elif protocol == 17:  # UDP
                    if len(transport_data) >= 8:
                        src_port, dst_port = struct.unpack('!HH', transport_data[:4])
                
                return NetworkEvent(
                    timestamp=time.time(),
                    src_ip=src_ip,
                    dst_ip=dst_ip,
                    protocol=self._get_protocol_name(protocol),
                    src_port=src_port,
                    dst_port=dst_port,
                    packet_size=len(data),
                    flags=flags
                )
            else:
                # Linux: Ethernet frame parsing
                if len(data) < 14:
                    return None
                
                eth_header = struct.unpack('!6s6sH', data[:14])
                eth_protocol = socket.ntohs(eth_header[2])
                
                if eth_protocol != 0x0800:  # Not IPv4
                    return None
                
                return self.parse_packet(data[14:], is_windows=True)
                
        except Exception as e:
            logging.debug(f"Packet parsing error: {str(e)}")
            return None

    def _parse_tcp_flags(self, flags_byte):
        """Parse TCP flags from byte"""
        flag_names = []
        if flags_byte & 0x01: flag_names.append("FIN")
        if flags_byte & 0x02: flag_names.append("SYN")
        if flags_byte & 0x04: flag_names.append("RST")
        if flags_byte & 0x08: flag_names.append("PSH")
        if flags_byte & 0x10: flag_names.append("ACK")
        if flags_byte & 0x20: flag_names.append("URG")
        return "|".join(flag_names) if flag_names else "NONE"

    def _get_protocol_name(self, proto_num):
        """Get protocol name from number"""
        protocols = {1: 'ICMP', 6: 'TCP', 17: 'UDP', 47: 'GRE', 50: 'ESP', 51: 'AH'}
        return protocols.get(proto_num, f'PROTO_{proto_num}')

    def detect_port_scan(self, event: NetworkEvent) -> bool:
        """Advanced port scan detection using connection patterns"""
        if not self.port_scan_detection or event.protocol != 'TCP':
            return False
        
        profile = self.ip_profiles[event.src_ip]
        profile['ports_accessed'].add(event.dst_port)
        
        # Check for rapid port access
        current_time = time.time()
        profile['connection_patterns'].append((current_time, event.dst_port))
        
        # Remove old connections (older than 60 seconds)
        while (profile['connection_patterns'] and 
               current_time - profile['connection_patterns'][0][0] > 60):
            profile['connection_patterns'].popleft()
        
        # Port scan indicators
        unique_ports_60s = len(set(port for _, port in profile['connection_patterns']))
        total_connections_60s = len(profile['connection_patterns'])
        
        # Alert if accessing many unique ports quickly
        if unique_ports_60s > 20 and total_connections_60s > 30:
            return True
        
        # Check for sequential port scanning
        recent_ports = [port for _, port in list(profile['connection_patterns'])[-10:]]
        if len(recent_ports) >= 5:
            # Check if ports are sequential
            sorted_ports = sorted(recent_ports)
            sequential = all(sorted_ports[i] + 1 == sorted_ports[i + 1] 
                           for i in range(len(sorted_ports) - 1))
            if sequential:
                return True
        
        return False

    def detect_dos_attack(self, event: NetworkEvent) -> bool:
        """Enhanced DoS detection with statistical analysis"""
        if not self.dos_detection:
            return False
        
        current_time = time.time()
        
        # Update request counts
        self.request_counts[event.src_ip] += 1
        
        # Reset counts every minute
        if current_time - self.last_reset > 60:
            with self.lock:
                self.request_counts.clear()
                self.last_reset = current_time
        
        # Check various DoS patterns
        requests_per_minute = self.request_counts[event.src_ip]
        
        # Traditional rate-based detection
        if requests_per_minute > self.threshold:
            return True
        
        # SYN flood detection
        if event.protocol == 'TCP' and event.flags and 'SYN' in event.flags:
            profile = self.ip_profiles[event.src_ip]
            syn_count = sum(1 for e in list(self.events_history)[-100:] 
                          if e.src_ip == event.src_ip and e.flags and 'SYN' in e.flags)
            if syn_count > 50:  # More than 50 SYN packets in recent history
                return True
        
        return False

    def detect_anomalies(self, event: NetworkEvent) -> List[str]:
        """Behavioral anomaly detection"""
        if not self.anomaly_detection or not self.baseline_established:
            return []
        
        anomalies = []
        profile = self.ip_profiles[event.src_ip]
        
        # Update profile
        profile['packet_count'] += 1
        old_avg = profile['avg_packet_size']
        profile['avg_packet_size'] = ((old_avg * (profile['packet_count'] - 1)) + event.packet_size) / profile['packet_count']
        profile['protocols'].add(event.protocol)
        
        # Check for unusual packet sizes
        if event.packet_size > profile['avg_packet_size'] * 3:
            anomalies.append("UNUSUAL_PACKET_SIZE")
        
        # Check for new protocols from known IPs
        if (profile['packet_count'] > 100 and 
            len(profile['protocols']) == 1 and 
            event.protocol not in profile['protocols']):
            anomalies.append("NEW_PROTOCOL_USAGE")
        
        # Check for first-time communication
        if profile['packet_count'] == 1:
            recent_new_ips = sum(1 for ip, p in self.ip_profiles.items() 
                               if time.time() - p['first_seen'] < 300)
            if recent_new_ips > 50:  # Many new IPs in 5 minutes
                anomalies.append("SUSPICIOUS_NEW_IP_PATTERN")
        
        return anomalies

    def check_threat_signatures(self, event: NetworkEvent) -> List[ThreatSignature]:
        """Check event against threat signatures"""
        matched_signatures = []
        
        # Create searchable string from event
        event_string = f"{event.src_ip} {event.dst_ip} {event.protocol}"
        if event.src_port:
            event_string += f" {event.src_port}"
        if event.dst_port:
            event_string += f" {event.dst_port}"
        if event.flags:
            event_string += f" {event.flags}"
        
        for signature in self.threat_signatures:
            try:
                if re.search(signature.pattern, event_string, re.IGNORECASE):
                    matched_signatures.append(signature)
            except re.error:
                logging.warning(f"Invalid regex pattern in signature: {signature.name}")
        
        return matched_signatures

    def handle_threat(self, event: NetworkEvent, threat_type: str, details: str, severity: str):
        """Handle detected threat with appropriate response"""
        current_time = time.time()
        
        with self.lock:
            self.alerts_generated += 1
            
            # Color coding by severity
            if severity == "CRITICAL":
                color = Fore.MAGENTA
                prefix = "[CRITICAL]"
            elif severity == "HIGH":
                color = Fore.RED
                prefix = "🔴 HIGH"
            elif severity == "MEDIUM":
                color = Fore.YELLOW
                prefix = "🟡 MEDIUM"
            else:
                color = Fore.CYAN
                prefix = "🔵 LOW"
            
            # Display alert
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"{color}[{prefix}] {timestamp} - {threat_type}{Style.RESET_ALL}")
            print(f"  Source: {event.src_ip}:{event.src_port or 'N/A'}")
            print(f"  Target: {event.dst_ip}:{event.dst_port or 'N/A'}")
            print(f"  Protocol: {event.protocol}")
            print(f"  Details: {details}")
            
            # Log the threat
            logging.warning(f"{threat_type} - {event.src_ip} -> {event.dst_ip} - {details}")
            
            # Take action based on severity
            if severity in ["CRITICAL", "HIGH"] and event.src_ip not in self.banned_ips:
                self.banned_ips[event.src_ip] = current_time
                self.threats_blocked += 1
                print(f"  {Fore.RED}[BLOCKED] {event.src_ip} for {self.ban_time//60} minutes{Style.RESET_ALL}")
                logging.warning(f"Blocked IP {event.src_ip} due to {threat_type}")

    def establish_baseline(self):
        """Establish normal traffic baseline during learning period"""
        current_time = time.time()
        
        if current_time - self.baseline_start_time >= self.learning_period:
            if not self.baseline_established:
                print(f"{Fore.GREEN}[INFO] Baseline learning period completed{Style.RESET_ALL}")
                print(f"[INFO] Analyzed {len(self.ip_profiles)} unique IP addresses")
                print(f"[INFO] Processed {self.packet_count:,} packets")
                self.baseline_established = True
                logging.info("Baseline established successfully")

    def monitor_traffic(self):
        """Main traffic monitoring loop with advanced threat detection"""
        conn = self.setup_socket()
        is_windows = platform.system() == "Windows"
        
        print(f"{Fore.MAGENTA}[IDS] Advanced Intrusion Detection System v2.0{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Target Platform: {platform.system()}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Learning Period: {self.learning_period}s{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Detection Threshold: {self.threshold} req/min{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Ban Duration: {self.ban_time//60} minutes{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🧠 Learning normal traffic patterns...{Style.RESET_ALL}")
        
        try:
            while self.running:
                # Receive packet
                if is_windows:
                    raw_data, addr = conn.recvfrom(65536)
                else:
                    raw_data, _ = conn.recvfrom(65536)
                
                # Parse packet
                event = self.parse_packet(raw_data, is_windows)
                if not event:
                    continue
                
                with self.lock:
                    self.packet_count += 1
                    self.events_history.append(event)
                
                # Check if still in learning period
                if not self.baseline_established:
                    self.establish_baseline()
                    continue
                
                # Skip banned IPs
                current_time = time.time()
                if event.src_ip in self.banned_ips:
                    if current_time - self.banned_ips[event.src_ip] >= self.ban_time:
                        with self.lock:
                            del self.banned_ips[event.src_ip]
                            print(f"{Fore.GREEN}[+] Unbanned {event.src_ip}{Style.RESET_ALL}")
                    else:
                        continue
                
                # Run threat detection algorithms
                
                # 1. Port scan detection
                if self.detect_port_scan(event):
                    self.handle_threat(
                        event, "PORT_SCAN_DETECTED", 
                        f"Scanning multiple ports from {event.src_ip}", "MEDIUM"
                    )
                
                # 2. DoS attack detection
                if self.detect_dos_attack(event):
                    self.handle_threat(
                        event, "DOS_ATTACK_DETECTED",
                        f"High request rate: {self.request_counts[event.src_ip]} req/min", "HIGH"
                    )
                
                # 3. Behavioral anomaly detection
                anomalies = self.detect_anomalies(event)
                for anomaly in anomalies:
                    self.handle_threat(
                        event, f"ANOMALY_{anomaly}",
                        f"Behavioral anomaly detected: {anomaly}", "MEDIUM"
                    )
                
                # 4. Signature-based detection
                signatures = self.check_threat_signatures(event)
                for signature in signatures:
                    self.handle_threat(
                        event, signature.name, signature.description, signature.severity
                    )
                
                # Periodic status update
                if self.packet_count % 1000 == 0:
                    print(f"{Fore.GREEN}[INFO] Processed {self.packet_count:,} packets | "
                          f"Alerts: {self.alerts_generated} | Blocked: {self.threats_blocked}{Style.RESET_ALL}")
        
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[INFO] Stopping Advanced IDS...{Style.RESET_ALL}")
            self._print_summary()
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Monitoring error: {str(e)}{Style.RESET_ALL}")
            logging.error(f"Monitoring error: {str(e)}")
        finally:
            self._cleanup_socket(conn, is_windows)

    def _print_summary(self):
        """Print detailed summary statistics"""
        runtime = time.time() - self.baseline_start_time
        
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[STATS] Advanced IDS Session Summary{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"Runtime: {runtime/60:.1f} minutes")
        print(f"Total packets processed: {self.packet_count:,}")
        print(f"Unique IP addresses seen: {len(self.ip_profiles):,}")
        print(f"Security alerts generated: {self.alerts_generated}")
        print(f"Threats blocked: {self.threats_blocked}")
        print(f"Average packets/second: {self.packet_count/runtime:.1f}")
        print(f"Currently banned IPs: {len(self.banned_ips)}")
        
        if self.banned_ips:
            print(f"\n{Fore.RED}🚫 Banned IP Addresses:{Style.RESET_ALL}")
            for ip, ban_time in self.banned_ips.items():
                remaining = max(0, self.ban_time - (time.time() - ban_time))
                print(f"  {ip} (unbans in {remaining/60:.1f} minutes)")
        
        logging.info(f"IDS session ended - Packets: {self.packet_count}, Alerts: {self.alerts_generated}")

    def _cleanup_socket(self, conn, is_windows):
        """Clean up socket resources"""
        try:
            if is_windows:
                conn.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
            conn.close()
        except:
            pass

def main():
    parser = argparse.ArgumentParser(description="Advanced Intrusion Detection System v2.0")
    parser.add_argument("--threshold", type=int, default=100, 
                       help="Max requests per minute per IP (default: 100)")
    parser.add_argument("--ban-time", type=int, default=600, 
                       help="Ban duration in seconds (default: 600)")
    parser.add_argument("--interface", help="Network interface to monitor (Linux only)")
    parser.add_argument("--learning-period", type=int, default=300,
                       help="Baseline learning period in seconds (default: 300)")
    parser.add_argument("--disable-port-scan", action="store_true",
                       help="Disable port scan detection")
    parser.add_argument("--disable-dos", action="store_true",
                       help="Disable DoS detection")
    parser.add_argument("--disable-anomaly", action="store_true",
                       help="Disable anomaly detection")
    
    args = parser.parse_args()

    try:
        ids = AdvancedIDS(
            threshold=args.threshold,
            ban_time=args.ban_time,
            interface=args.interface,
            learning_period=args.learning_period
        )
        
        # Configure detection modules
        if args.disable_port_scan:
            ids.port_scan_detection = False
        if args.disable_dos:
            ids.dos_detection = False
        if args.disable_anomaly:
            ids.anomaly_detection = False
        
        require_admin()  # Check for admin privileges
        require_admin()  # Check for admin privileges before starting
        ids.monitor_traffic()
        
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Unexpected error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
