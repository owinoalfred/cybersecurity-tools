import socket
import argparse
import threading
import queue
import sys
import struct
import random
from datetime import datetime
import time
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

class AdvancedPortScanner:
    def __init__(self, target, port_range, timeout=1, threads=100, scan_type="tcp"):
        self.target = target
        self.start_port, self.end_port = map(int, port_range.split('-'))
        self.ports = range(self.start_port, self.end_port + 1)
        self.timeout = timeout
        self.threads = threads
        self.scan_type = scan_type.lower()
        self.open_ports = []
        self.filtered_ports = []
        self.closed_ports = []
        self.port_queue = queue.Queue()
        self.lock = threading.Lock()
        
        # Enhanced service detection
        self.common_services = {
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
            80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 993: "IMAPS",
            995: "POP3S", 3389: "RDP", 5432: "PostgreSQL", 3306: "MySQL",
            1433: "MSSQL", 6379: "Redis", 27017: "MongoDB", 5900: "VNC"
        }

    def resolve_target(self):
        """Resolve hostname to IP address."""
        try:
            ip = socket.gethostbyname(self.target)
            return ip
        except socket.gaierror:
            print(f"{Fore.RED}[ERROR] Could not resolve hostname: {self.target}{Style.RESET_ALL}")
            sys.exit(1)

    def tcp_connect_scan(self, ip, port):
        """Traditional TCP connect scan."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip, port))
            if result == 0:
                service = self.detect_service(ip, port)
                with self.lock:
                    self.open_ports.append((port, service))
                    print(f"{Fore.GREEN}[OPEN] Port {port}/TCP - {service}{Style.RESET_ALL}")
            sock.close()
        except socket.error:
            pass

    def udp_scan(self, ip, port):
        """UDP port scanning."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            
            # Send UDP packet
            sock.sendto(b'', (ip, port))
            
            # Try to receive response
            try:
                data, addr = sock.recvfrom(1024)
                service = self.common_services.get(port, "Unknown UDP service")
                with self.lock:
                    self.open_ports.append((port, f"{service} (UDP)"))
                    print(f"{Fore.GREEN}[OPEN] Port {port}/UDP - {service}{Style.RESET_ALL}")
            except socket.timeout:
                # No response might mean open/filtered
                with self.lock:
                    self.filtered_ports.append(port)
            
            sock.close()
        except socket.error as e:
            if "port unreachable" in str(e).lower():
                with self.lock:
                    self.closed_ports.append(port)

    def detect_service(self, ip, port):
        """Enhanced service detection with banner grabbing."""
        try:
            # Try banner grabbing
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((ip, port))
            
            # Send HTTP request for web services
            if port in [80, 443, 8080, 8443]:
                sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
                banner = sock.recv(1024).decode('utf-8', errors='ignore')
                if 'server:' in banner.lower():
                    server = banner.split('Server:')[1].split('\r\n')[0].strip()
                    return f"HTTP ({server})"
                return "HTTP"
            
            # For other services, just grab banner
            banner = sock.recv(1024).decode('utf-8', errors='ignore')
            sock.close()
            
            if banner:
                # Detect service based on banner
                banner_lower = banner.lower()
                if 'ssh' in banner_lower:
                    return f"SSH ({banner.strip()[:50]})"
                elif 'ftp' in banner_lower:
                    return f"FTP ({banner.strip()[:50]})"
                elif 'smtp' in banner_lower:
                    return f"SMTP ({banner.strip()[:50]})"
                else:
                    return f"{self.common_services.get(port, 'Unknown')} ({banner.strip()[:30]})"
            
        except:
            pass
        
        return self.common_services.get(port, "Unknown")

    def worker(self, ip):
        """Thread worker function."""
        while True:
            try:
                port = self.port_queue.get_nowait()
            except queue.Empty:
                break
            
            if self.scan_type == "tcp":
                self.tcp_connect_scan(ip, port)
            elif self.scan_type == "udp":
                self.udp_scan(ip, port)
            elif self.scan_type == "both":
                self.tcp_connect_scan(ip, port)
                self.udp_scan(ip, port)
            
            self.port_queue.task_done()
            # Rate limiting to avoid overwhelming target
            time.sleep(0.01)

    def scan(self):
        """Main scanning function with enhanced output."""
        print(f"{Fore.CYAN}Advanced Port Scanner v2.0{Style.RESET_ALL}")
        print(f"Target: {self.target}")
        print(f"Scan Type: {self.scan_type.upper()}")
        print(f"Time started: {datetime.now()}")
        print(f"Scanning ports {self.start_port} to {self.end_port} ({len(self.ports)} ports)")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

        start_time = time.time()
        ip = self.resolve_target()
        print(f"Resolved IP: {ip}")

        # Fill the queue with ports
        for port in self.ports:
            self.port_queue.put(port)

        # Start worker threads
        threads = []
        for _ in range(min(self.threads, len(self.ports))):
            t = threading.Thread(target=self.worker, args=(ip,))
            t.start()
            threads.append(t)

        # Wait for all threads to complete
        for t in threads:
            t.join()

        self.port_queue.join()
        end_time = time.time()
        duration = round(end_time - start_time, 2)

        # Enhanced summary
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Scan completed in {duration} seconds{Style.RESET_ALL}")
        
        if self.open_ports:
            print(f"{Fore.GREEN}Open ports found: {len(self.open_ports)}{Style.RESET_ALL}")
            for port, service in sorted(self.open_ports):
                print(f"  {port}: {service}")
        
        if self.filtered_ports and self.scan_type in ["udp", "both"]:
            print(f"{Fore.YELLOW}Filtered/Open UDP ports: {len(self.filtered_ports)}{Style.RESET_ALL}")
            for port in sorted(self.filtered_ports)[:10]:  # Show first 10
                print(f"  {port}/UDP: Filtered/Open")
        
        if not self.open_ports and not self.filtered_ports:
            print(f"{Fore.RED}No open ports found.{Style.RESET_ALL}")

def main():
    parser = argparse.ArgumentParser(description="Advanced Port Scanner v2.0")
    parser.add_argument("target", help="Target hostname or IP")
    parser.add_argument("ports", help="Port range (e.g., 1-1000)")
    parser.add_argument("--timeout", type=float, default=1.0, help="Socket timeout (default: 1.0)")
    parser.add_argument("--threads", type=int, default=50, help="Number of threads (default: 50)")
    parser.add_argument("--type", choices=["tcp", "udp", "both"], default="tcp", 
                       help="Scan type: tcp, udp, or both (default: tcp)")
    args = parser.parse_args()

    # Validate port range
    try:
        start, end = map(int, args.ports.split('-'))
        if not (1 <= start <= end <= 65535):
            raise ValueError
    except ValueError:
        print(f"{Fore.RED}[ERROR] Invalid port range. Use format 'start-end' (1-65535){Style.RESET_ALL}")
        sys.exit(1)

    try:
        scanner = AdvancedPortScanner(args.target, args.ports, args.timeout, args.threads, args.type)
        scanner.scan()
    except KeyboardInterrupt:
        print(f"{Fore.RED}[!] Scan interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Unexpected error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
