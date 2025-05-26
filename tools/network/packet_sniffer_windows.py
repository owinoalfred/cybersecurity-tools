import socket
import struct
import textwrap
import argparse
import sys
import platform
from datetime import datetime
from colorama import init, Fore, Style
import logging

# Initialize colorama for colored output
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='packet_sniffer.log'
)

class PacketSniffer:
    def __init__(self, interface=None, filter_proto=None):
        self.interface = interface
        self.filter_proto = filter_proto.upper() if filter_proto else None
        self.running = True
        self.packet_count = 0
        
        # Protocol numbers
        self.PROTO_IPV4 = 8
        self.PROTO_TCP = 6
        self.PROTO_UDP = 17
        self.PROTO_ICMP = 1

    def setup_socket(self):
        """Set up the raw socket with Windows compatibility."""
        try:
            if platform.system() == "Windows":
                # Windows: Use raw IP socket
                conn = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                conn.bind((local_ip, 0))
                conn.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
                print(f"{Fore.YELLOW}[INFO] Windows mode: Monitoring IP traffic on {local_ip}{Style.RESET_ALL}")
            else:
                # Linux: Use packet socket
                conn = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0003))
                if self.interface:
                    conn.bind((self.interface, 0))
                print(f"{Fore.YELLOW}[INFO] Linux mode: Monitoring on interface {self.interface or 'all'}{Style.RESET_ALL}")
            return conn
        except PermissionError:
            print(f"{Fore.RED}[ERROR] Permission denied. Run as Administrator on Windows or with sudo on Linux.{Style.RESET_ALL}")
            sys.exit(1)
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Failed to create socket: {str(e)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[TIP] On Windows, make sure to run as Administrator.{Style.RESET_ALL}")
            sys.exit(1)

    def ethernet_frame(self, data):
        """Unpack ethernet frame (Linux only)."""
        dest_mac, src_mac, eth_proto = struct.unpack('! 6s 6s H', data[:14])
        return self.get_mac_addr(dest_mac), self.get_mac_addr(src_mac), socket.htons(eth_proto), data[14:]

    def get_mac_addr(self, bytes_addr):
        """Convert MAC address bytes to readable format."""
        return ':'.join(map('{:02x}'.format, bytes_addr)).upper()

    def ipv4_packet(self, data):
        """Unpack IPv4 packet."""
        version_header_length = data[0]
        version = version_header_length >> 4
        header_length = (version_header_length & 15) * 4
        ttl, proto, src, target = struct.unpack('! 8x B B 2x 4s 4s', data[:20])
        return version, header_length, ttl, proto, self.ipv4(src), self.ipv4(target), data[header_length:]

    def ipv4(self, addr):
        """Convert IP address to readable format."""
        return '.'.join(map(str, addr))

    def icmp_packet(self, data):
        """Unpack ICMP packet."""
        icmp_type, code, checksum = struct.unpack('! B B H', data[:4])
        return icmp_type, code, checksum, data[4:]

    def tcp_segment(self, data):
        """Unpack TCP segment."""
        (src_port, dest_port, sequence, acknowledgment, offset_reserved_flags) = struct.unpack('! H H L L H', data[:14])
        offset = (offset_reserved_flags >> 12) * 4
        flag_urg = (offset_reserved_flags & 32) >> 5
        flag_ack = (offset_reserved_flags & 16) >> 4
        flag_psh = (offset_reserved_flags & 8) >> 3
        flag_rst = (offset_reserved_flags & 4) >> 2
        flag_syn = (offset_reserved_flags & 2) >> 1
        flag_fin = offset_reserved_flags & 1
        return src_port, dest_port, sequence, acknowledgment, flag_urg, flag_ack, flag_psh, flag_rst, flag_syn, flag_fin, data[offset:]

    def udp_segment(self, data):
        """Unpack UDP segment."""
        src_port, dest_port, length = struct.unpack('! H H 2x H', data[:8])
        return src_port, dest_port, length, data[8:]

    def format_multi_line(self, prefix, string, size=80):
        """Format data for display."""
        size -= len(prefix)
        if isinstance(string, bytes):
            string = ''.join(r'\x{:02x}'.format(byte) for byte in string)
            if size % 2:
                size -= 1
        return '\n'.join([prefix + line for line in textwrap.wrap(string, size)])

    def run(self):
        """Main sniffer loop."""
        print(f"{Fore.CYAN}Starting packet sniffer on {platform.system()}{Style.RESET_ALL}")
        print(f"Filter: {self.filter_proto or 'All protocols'}")
        print(f"Time started: {datetime.now()}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        
        conn = self.setup_socket()
        
        try:
            while self.running:
                if platform.system() == "Windows":
                    # Windows: receive IP packets directly
                    raw_data, addr = conn.recvfrom(65536)
                    data = raw_data
                    src_mac = dest_mac = "N/A (Windows)"
                else:
                    # Linux: receive Ethernet frames
                    raw_data, addr = conn.recvfrom(65536)
                    src_mac, dest_mac, eth_proto, data = self.ethernet_frame(raw_data)
                    if eth_proto != self.PROTO_IPV4:
                        continue

                self.packet_count += 1

                try:
                    # IPv4
                    version, header_length, ttl, proto, src_ip, target_ip, data = self.ipv4_packet(data)
                    
                    # Apply protocol filter
                    proto_name = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}.get(proto, f'Other({proto})')
                    if self.filter_proto and proto_name != self.filter_proto:
                        continue

                    print(f"\n{Fore.CYAN}--- Packet #{self.packet_count} ---{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}Ethernet Frame:{Style.RESET_ALL}")
                    print(f"  Destination: {dest_mac}, Source: {src_mac}")
                    print(f"{Fore.YELLOW}IPv4 Packet:{Style.RESET_ALL}")
                    print(f"  Version: {version}, Header Length: {header_length}, TTL: {ttl}")
                    print(f"  Protocol: {proto_name}, Source: {src_ip}, Target: {target_ip}")

                    # ICMP
                    if proto == self.PROTO_ICMP:
                        icmp_type, code, checksum, data = self.icmp_packet(data)
                        print(f"{Fore.YELLOW}ICMP Packet:{Style.RESET_ALL}")
                        print(f"  Type: {icmp_type}, Code: {code}, Checksum: {checksum}")

                    # TCP
                    elif proto == self.PROTO_TCP:
                        (src_port, dest_port, sequence, acknowledgment, flag_urg, flag_ack, 
                         flag_psh, flag_rst, flag_syn, flag_fin, data) = self.tcp_segment(data)
                        print(f"{Fore.YELLOW}TCP Segment:{Style.RESET_ALL}")
                        print(f"  Source Port: {src_port}, Dest Port: {dest_port}")
                        print(f"  Sequence: {sequence}, Acknowledgment: {acknowledgment}")
                        print(f"  Flags:")
                        print(f"    URG: {flag_urg}, ACK: {flag_ack}, PSH: {flag_psh}")
                        print(f"    RST: {flag_rst}, SYN: {flag_syn}, FIN: {flag_fin}")

                    # UDP
                    elif proto == self.PROTO_UDP:
                        src_port, dest_port, length, data = self.udp_segment(data)
                        print(f"{Fore.YELLOW}UDP Segment:{Style.RESET_ALL}")
                        print(f"  Source Port: {src_port}, Dest Port: {dest_port}, Length: {length}")

                    # Data payload
                    if data and len(data) > 0:
                        print(f"{Fore.YELLOW}Data:{Style.RESET_ALL}")
                        print(self.format_multi_line('  ', data[:50]))  # Show first 50 bytes
                        if len(data) > 50:
                            print(f"  ... ({len(data)} total bytes)")
                    
                    logging.info(f"Packet #{self.packet_count}: {proto_name} {src_ip}:{src_port if proto in [6, 17] else ''} -> {target_ip}:{dest_port if proto in [6, 17] else ''}")
                    
                except Exception as e:
                    # Skip malformed packets
                    continue

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[INFO] Stopping packet capture...{Style.RESET_ALL}")
            print(f"Total packets captured: {self.packet_count}")
            logging.info(f"Packet sniffer stopped - Total packets: {self.packet_count}")
        finally:
            try:
                if platform.system() == "Windows":
                    conn.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
                conn.close()
            except:
                pass

def main():
    parser = argparse.ArgumentParser(description="Advanced Packet Sniffer (Windows Compatible)")
    parser.add_argument("--interface", help="Network interface to sniff on (Linux only)")
    parser.add_argument("--protocol", choices=['TCP', 'UDP', 'ICMP'], help="Filter by protocol")
    args = parser.parse_args()

    if platform.system() == "Windows":
        print(f"{Fore.CYAN}Windows Packet Sniffer Mode{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Note: Run as Administrator for best results{Style.RESET_ALL}")
        if args.interface:
            print(f"{Fore.YELLOW}Note: Interface parameter ignored on Windows{Style.RESET_ALL}")
    else:
        print(f"{Fore.CYAN}Linux/Unix Packet Sniffer Mode{Style.RESET_ALL}")

    try:
        sniffer = PacketSniffer(args.interface, args.protocol)
        sniffer.run()
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Unexpected error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
