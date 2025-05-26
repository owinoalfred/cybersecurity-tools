#!/usr/bin/env python3
"""
Advanced Packet Sniffer
Comprehensive network packet analysis tool with protocol analysis, filtering, and forensic capabilities.
"""

import socket
import struct
import time
import threading
import json
import csv
import argparse
import sys
from datetime import datetime
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
import re

# Enhanced protocol constants
PROTOCOLS = {
    1: 'ICMP',
    6: 'TCP',
    17: 'UDP',
    2: 'IGMP',
    89: 'OSPF',
    41: 'IPv6',
    47: 'GRE'
}

TCP_FLAGS = {
    0x01: 'FIN',
    0x02: 'SYN',
    0x04: 'RST',
    0x08: 'PSH',
    0x10: 'ACK',
    0x20: 'URG',
    0x40: 'ECE',
    0x80: 'CWR'
}

ICMP_TYPES = {
    0: 'Echo Reply',
    3: 'Destination Unreachable',
    8: 'Echo Request',
    11: 'Time Exceeded',
    12: 'Parameter Problem',
    13: 'Timestamp Request',
    14: 'Timestamp Reply'
}

@dataclass
class PacketInfo:
    """Enhanced packet information structure"""
    timestamp: float
    src_ip: str
    dst_ip: str
    protocol: str
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    size: int = 0
    flags: List[str] = None
    payload_size: int = 0
    payload_preview: str = ""
    tcp_seq: Optional[int] = None
    tcp_ack: Optional[int] = None
    icmp_type: Optional[str] = None
    suspicious: bool = False
    tags: List[str] = None

    def __post_init__(self):
        if self.flags is None:
            self.flags = []
        if self.tags is None:
            self.tags = []

class AdvancedPacketSniffer:
    def __init__(self, interface=None, max_packets=None, output_file=None):
        self.interface = interface
        self.max_packets = max_packets
        self.output_file = output_file
        self.packets = []
        self.packet_count = 0
        self.start_time = None
        self.running = False
        self.filters = {}
        
        # Enhanced statistics tracking
        self.stats = {
            'protocols': defaultdict(int),
            'ports': defaultdict(int),
            'ips': defaultdict(int),
            'packet_sizes': deque(maxlen=1000),
            'connections': defaultdict(int),
            'suspicious_activity': defaultdict(int)
        }
        
        # Anomaly detection
        self.connection_tracker = defaultdict(lambda: {'count': 0, 'last_seen': 0})
        self.port_scan_detector = defaultdict(lambda: {'ports': set(), 'last_activity': 0})
        
        # Pattern matching for suspicious content
        self.suspicious_patterns = [
            re.compile(rb'(?i)(union.*select|select.*from|insert.*into|delete.*from)', re.IGNORECASE),
            re.compile(rb'(?i)(<script|javascript:|vbscript:)', re.IGNORECASE),
            re.compile(rb'(?i)(cmd\.exe|/bin/sh|/bin/bash)', re.IGNORECASE),
            re.compile(rb'(?i)(password|passwd|pwd)', re.IGNORECASE)
        ]

    def create_socket(self):
        """Create and configure raw socket"""
        try:
            if sys.platform == "win32":
                # Windows raw socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
                sock.bind((socket.gethostbyname(socket.gethostname()), 0))
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
                # Enable promiscuous mode on Windows
                sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
                return sock
            else:
                # Linux/Unix raw socket
                sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0003))
                return sock
        except PermissionError:
            print("Error: Raw socket requires administrator/root privileges")
            sys.exit(1)
        except Exception as e:
            print(f"Error creating socket: {e}")
            sys.exit(1)

    def parse_ethernet_header(self, data):
        """Parse Ethernet header (Linux only)"""
        if len(data) < 14:
            return None, data
        
        eth_header = struct.unpack('!6s6sH', data[:14])
        eth_protocol = socket.ntohs(eth_header[2])
        
        # Return IP data if it's an IP packet
        if eth_protocol == 0x0800:  # IPv4
            return eth_header, data[14:]
        return None, data[14:]

    def parse_ip_header(self, data):
        """Parse IP header with enhanced information extraction"""
        if len(data) < 20:
            return None
        
        ip_header = struct.unpack('!BBHHHBBH4s4s', data[:20])
        
        version_ihl = ip_header[0]
        version = version_ihl >> 4
        ihl = (version_ihl & 0xF) * 4
        
        if version != 4:  # Only IPv4 for now
            return None
        
        protocol = ip_header[6]
        src_ip = socket.inet_ntoa(ip_header[8])
        dst_ip = socket.inet_ntoa(ip_header[9])
        total_length = ip_header[2]
        
        return {
            'src_ip': src_ip,
            'dst_ip': dst_ip,
            'protocol': protocol,
            'total_length': total_length,
            'header_length': ihl,
            'payload': data[ihl:total_length] if total_length <= len(data) else data[ihl:]
        }

    def parse_tcp_header(self, data):
        """Parse TCP header with detailed flag analysis"""
        if len(data) < 20:
            return None
        
        tcp_header = struct.unpack('!HHLLBBHHH', data[:20])
        
        src_port = tcp_header[0]
        dst_port = tcp_header[1]
        seq_num = tcp_header[2]
        ack_num = tcp_header[3]
        flags_byte = tcp_header[5]
        window_size = tcp_header[6]
        
        # Parse TCP flags
        flags = []
        for flag_bit, flag_name in TCP_FLAGS.items():
            if flags_byte & flag_bit:
                flags.append(flag_name)
        
        tcp_header_length = ((tcp_header[4] >> 4) & 0xF) * 4
        payload = data[tcp_header_length:]
        
        return {
            'src_port': src_port,
            'dst_port': dst_port,
            'seq': seq_num,
            'ack': ack_num,
            'flags': flags,
            'window': window_size,
            'payload': payload
        }

    def parse_udp_header(self, data):
        """Parse UDP header"""
        if len(data) < 8:
            return None
        
        udp_header = struct.unpack('!HHHH', data[:8])
        
        return {
            'src_port': udp_header[0],
            'dst_port': udp_header[1],
            'length': udp_header[2],
            'payload': data[8:]
        }

    def parse_icmp_header(self, data):
        """Parse ICMP header"""
        if len(data) < 8:
            return None
        
        icmp_header = struct.unpack('!BBHHH', data[:8])
        icmp_type = icmp_header[0]
        icmp_code = icmp_header[1]
        
        type_name = ICMP_TYPES.get(icmp_type, f'Type {icmp_type}')
        
        return {
            'type': icmp_type,
            'code': icmp_code,
            'type_name': type_name,
            'payload': data[8:]
        }

    def detect_suspicious_activity(self, packet_info: PacketInfo, payload: bytes):
        """Enhanced suspicious activity detection"""
        suspicious_reasons = []
        
        # 1. Port scanning detection
        if packet_info.src_port and packet_info.dst_port:
            key = packet_info.src_ip
            self.port_scan_detector[key]['ports'].add(packet_info.dst_port)
            self.port_scan_detector[key]['last_activity'] = time.time()
            
            # If same IP accessed many different ports recently
            if len(self.port_scan_detector[key]['ports']) > 10:
                if time.time() - self.port_scan_detector[key]['last_activity'] < 60:
                    suspicious_reasons.append("potential_port_scan")
        
        # 2. Unusual port combinations
        if packet_info.dst_port in [22, 23, 21, 3389, 1433, 3306]:  # Common targets
            suspicious_reasons.append("high_value_target")
        
        # 3. Payload pattern analysis
        if payload:
            for pattern in self.suspicious_patterns:
                if pattern.search(payload):
                    suspicious_reasons.append("suspicious_payload_pattern")
                    break
        
        # 4. Unusual packet sizes
        if packet_info.size > 1500 or (packet_info.payload_size > 0 and packet_info.payload_size < 10):
            suspicious_reasons.append("unusual_packet_size")
        
        # 5. TCP flag combinations
        if 'SYN' in packet_info.flags and 'FIN' in packet_info.flags:
            suspicious_reasons.append("syn_fin_scan")
        elif 'FIN' in packet_info.flags and 'URG' in packet_info.flags and 'PSH' in packet_info.flags:
            suspicious_reasons.append("xmas_scan")
        elif not packet_info.flags and packet_info.protocol == 'TCP':
            suspicious_reasons.append("null_scan")
        
        if suspicious_reasons:
            packet_info.suspicious = True
            packet_info.tags.extend(suspicious_reasons)
            for reason in suspicious_reasons:
                self.stats['suspicious_activity'][reason] += 1

    def get_payload_preview(self, payload: bytes, max_length: int = 50) -> str:
        """Get a safe preview of payload content"""
        if not payload:
            return ""
        
        # Try to decode as text
        try:
            preview = payload[:max_length].decode('utf-8', errors='ignore')
            # Replace non-printable characters
            preview = ''.join(c if c.isprintable() else '.' for c in preview)
            return preview
        except:
            # Fallback to hex representation
            return payload[:max_length//2].hex()

    def process_packet(self, data):
        """Enhanced packet processing with comprehensive analysis"""
        timestamp = time.time()
        
        # Handle different platforms
        if sys.platform != "win32":
            eth_header, ip_data = self.parse_ethernet_header(data)
            if eth_header is None:
                return None
        else:
            ip_data = data
        
        ip_info = self.parse_ip_header(ip_data)
        if not ip_info:
            return None
        
        protocol_name = PROTOCOLS.get(ip_info['protocol'], f"Protocol-{ip_info['protocol']}")
        
        packet_info = PacketInfo(
            timestamp=timestamp,
            src_ip=ip_info['src_ip'],
            dst_ip=ip_info['dst_ip'],
            protocol=protocol_name,
            size=len(data),
            payload_size=len(ip_info['payload'])
        )
        
        # Protocol-specific parsing
        if ip_info['protocol'] == 6:  # TCP
            tcp_info = self.parse_tcp_header(ip_info['payload'])
            if tcp_info:
                packet_info.src_port = tcp_info['src_port']
                packet_info.dst_port = tcp_info['dst_port']
                packet_info.flags = tcp_info['flags']
                packet_info.tcp_seq = tcp_info['seq']
                packet_info.tcp_ack = tcp_info['ack']
                packet_info.payload_preview = self.get_payload_preview(tcp_info['payload'])
                
                # Detect suspicious activity
                self.detect_suspicious_activity(packet_info, tcp_info['payload'])
        
        elif ip_info['protocol'] == 17:  # UDP
            udp_info = self.parse_udp_header(ip_info['payload'])
            if udp_info:
                packet_info.src_port = udp_info['src_port']
                packet_info.dst_port = udp_info['dst_port']
                packet_info.payload_preview = self.get_payload_preview(udp_info['payload'])
                
                # Detect suspicious activity
                self.detect_suspicious_activity(packet_info, udp_info['payload'])
        
        elif ip_info['protocol'] == 1:  # ICMP
            icmp_info = self.parse_icmp_header(ip_info['payload'])
            if icmp_info:
                packet_info.icmp_type = icmp_info['type_name']
                packet_info.payload_preview = self.get_payload_preview(icmp_info['payload'])
        
        # Update statistics
        self.update_statistics(packet_info)
        
        return packet_info

    def update_statistics(self, packet_info: PacketInfo):
        """Update comprehensive packet statistics"""
        self.stats['protocols'][packet_info.protocol] += 1
        self.stats['ips'][packet_info.src_ip] += 1
        self.stats['ips'][packet_info.dst_ip] += 1
        self.stats['packet_sizes'].append(packet_info.size)
        
        if packet_info.src_port:
            self.stats['ports'][packet_info.src_port] += 1
        if packet_info.dst_port:
            self.stats['ports'][packet_info.dst_port] += 1
        
        # Track connections
        if packet_info.src_port and packet_info.dst_port:
            connection = f"{packet_info.src_ip}:{packet_info.src_port}->{packet_info.dst_ip}:{packet_info.dst_port}"
            self.stats['connections'][connection] += 1

    def apply_filters(self, packet_info: PacketInfo) -> bool:
        """Apply packet filters"""
        if not self.filters:
            return True
        
        # IP filters
        if 'src_ip' in self.filters and packet_info.src_ip not in self.filters['src_ip']:
            return False
        if 'dst_ip' in self.filters and packet_info.dst_ip not in self.filters['dst_ip']:
            return False
        
        # Protocol filter
        if 'protocol' in self.filters and packet_info.protocol not in self.filters['protocol']:
            return False
        
        # Port filters
        if 'port' in self.filters:
            ports = self.filters['port']
            if not (packet_info.src_port in ports or packet_info.dst_port in ports):
                return False
        
        # Suspicious activity filter
        if 'suspicious_only' in self.filters and self.filters['suspicious_only'] and not packet_info.suspicious:
            return False
        
        return True

    def set_filter(self, filter_type: str, values: List[str]):
        """Set packet filters"""
        if filter_type == 'port':
            self.filters[filter_type] = [int(p) for p in values]
        else:
            self.filters[filter_type] = values

    def print_packet(self, packet_info: PacketInfo):
        """Enhanced packet display"""
        time_str = datetime.fromtimestamp(packet_info.timestamp).strftime('%H:%M:%S.%f')[:-3]
        
        # Base packet info
        output = f"[{time_str}] {packet_info.src_ip}"
        if packet_info.src_port:
            output += f":{packet_info.src_port}"
        output += f" -> {packet_info.dst_ip}"
        if packet_info.dst_port:
            output += f":{packet_info.dst_port}"
        output += f" [{packet_info.protocol}]"
        
        # Add flags for TCP
        if packet_info.flags:
            output += f" [{','.join(packet_info.flags)}]"
        
        # Add ICMP type
        if packet_info.icmp_type:
            output += f" [{packet_info.icmp_type}]"
        
        # Add size info
        output += f" Size: {packet_info.size}B"
        if packet_info.payload_size > 0:
            output += f" Payload: {packet_info.payload_size}B"
        
        # Add suspicious indicator
        if packet_info.suspicious:
            output += f" ⚠️  SUSPICIOUS: {', '.join(packet_info.tags)}"
        
        # Add payload preview
        if packet_info.payload_preview:
            output += f"\n    Preview: {packet_info.payload_preview}"
        
        print(output)

    def save_to_file(self, filename: str, format: str = 'json'):
        """Save captured packets to file"""
        try:
            if format == 'json':
                with open(filename, 'w') as f:
                    packet_data = [asdict(packet) for packet in self.packets]
                    json.dump({
                        'capture_info': {
                            'start_time': self.start_time,
                            'packet_count': len(self.packets),
                            'duration': time.time() - self.start_time if self.start_time else 0
                        },
                        'statistics': dict(self.stats),
                        'packets': packet_data
                    }, f, indent=2, default=str)
            
            elif format == 'csv':
                with open(filename, 'w', newline='') as f:
                    if self.packets:
                        writer = csv.DictWriter(f, fieldnames=asdict(self.packets[0]).keys())
                        writer.writeheader()
                        for packet in self.packets:
                            writer.writerow(asdict(packet))
            
            print(f"Packets saved to {filename}")
        except Exception as e:
            print(f"Error saving packets: {e}")

    def print_statistics(self):
        """Display comprehensive capture statistics"""
        if not self.packets:
            print("No packets captured.")
            return
        
        duration = time.time() - self.start_time if self.start_time else 0
        
        print("\n" + "="*60)
        print("PACKET CAPTURE STATISTICS")
        print("="*60)
        print(f"Capture Duration: {duration:.2f} seconds")
        print(f"Total Packets: {len(self.packets)}")
        print(f"Packets/second: {len(self.packets)/duration:.2f}" if duration > 0 else "N/A")
        
        # Protocol distribution
        print(f"\nProtocol Distribution:")
        for protocol, count in sorted(self.stats['protocols'].items(), key=lambda x: x[1], reverse=True)[:10]:
            percentage = (count / len(self.packets)) * 100
            print(f"  {protocol}: {count} ({percentage:.1f}%)")
        
        # Top talkers
        print(f"\nTop Source IPs:")
        for ip, count in sorted(self.stats['ips'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {ip}: {count} packets")
        
        # Top ports
        if any(self.stats['ports'].values()):
            print(f"\nTop Ports:")
            for port, count in sorted(self.stats['ports'].items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {port}: {count} packets")
        
        # Suspicious activity summary
        if any(self.stats['suspicious_activity'].values()):
            print(f"\nSuspicious Activity Detected:")
            for activity, count in self.stats['suspicious_activity'].items():
                print(f"  {activity}: {count} incidents")
        
        # Packet size analysis
        if self.stats['packet_sizes']:
            sizes = list(self.stats['packet_sizes'])
            avg_size = sum(sizes) / len(sizes)
            min_size = min(sizes)
            max_size = max(sizes)
            print(f"\nPacket Size Analysis:")
            print(f"  Average: {avg_size:.1f} bytes")
            print(f"  Range: {min_size} - {max_size} bytes")

    def sniff(self):
        """Main packet sniffing loop"""
        sock = self.create_socket()
        self.start_time = time.time()
        self.running = True
        
        print(f"Starting packet capture...")
        if self.max_packets:
            print(f"Capturing up to {self.max_packets} packets")
        print("Press Ctrl+C to stop\n")
        
        try:
            while self.running:
                if self.max_packets and self.packet_count >= self.max_packets:
                    break
                
                try:
                    data, addr = sock.recvfrom(65535)
                    packet_info = self.process_packet(data)
                    
                    if packet_info and self.apply_filters(packet_info):
                        self.packets.append(packet_info)
                        self.packet_count += 1
                        self.print_packet(packet_info)
                
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Error processing packet: {e}")
                    continue
        
        except KeyboardInterrupt:
            print("\nStopping packet capture...")
        
        finally:
            if sys.platform == "win32":
                sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
            sock.close()
            self.running = False
        
        # Print final statistics
        self.print_statistics()
        
        # Save to file if specified
        if self.output_file:
            self.save_to_file(self.output_file)

def main():
    parser = argparse.ArgumentParser(description='Advanced Network Packet Sniffer')
    parser.add_argument('-i', '--interface', help='Network interface to capture on')
    parser.add_argument('-c', '--count', type=int, help='Number of packets to capture')
    parser.add_argument('-o', '--output', help='Output file for packet data')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Output format')
    parser.add_argument('--filter-ip', nargs='+', help='Filter by IP addresses')
    parser.add_argument('--filter-port', nargs='+', help='Filter by ports')
    parser.add_argument('--filter-protocol', nargs='+', help='Filter by protocols')
    parser.add_argument('--suspicious-only', action='store_true', help='Show only suspicious packets')
    
    args = parser.parse_args()
    
    # Create sniffer instance
    sniffer = AdvancedPacketSniffer(
        interface=args.interface,
        max_packets=args.count,
        output_file=args.output
    )
    
    # Apply filters
    if args.filter_ip:
        sniffer.set_filter('src_ip', args.filter_ip)
        sniffer.set_filter('dst_ip', args.filter_ip)
    if args.filter_port:
        sniffer.set_filter('port', args.filter_port)
    if args.filter_protocol:
        sniffer.set_filter('protocol', args.filter_protocol)
    if args.suspicious_only:
        sniffer.set_filter('suspicious_only', [True])
    
    # Start sniffing
    sniffer.sniff()

if __name__ == "__main__":
    main()
