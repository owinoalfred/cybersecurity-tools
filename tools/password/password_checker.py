import re
import math
import argparse
import sys
import hashlib
import requests
from datetime import datetime
from colorama import init, Fore, Style
import logging

# Initialize colorama for colored output
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='password_checker_advanced.log'
)

class AdvancedPasswordChecker:
    def __init__(self, password):
        self.password = password
        self.strength_score = 0
        self.entropy_score = 0
        self.suggestions = []
        self.warnings = []
        
        # NIST-based common passwords (expanded list)
        self.common_passwords = {
            "password", "123456", "123456789", "qwerty", "abc123", "111111",
            "password123", "admin", "letmein", "welcome", "monkey", "dragon",
            "master", "hello", "freedom", "whatever", "qazwsx", "trustno1",
            "jordan23", "harley", "robert", "matthew", "jordan", "superman"
        }
        
        # Common patterns that reduce security
        self.weak_patterns = [
            r'\d{4,}',  # 4+ consecutive digits
            r'[a-zA-Z]{4,}',  # 4+ consecutive letters
            r'(.)\1{2,}',  # 3+ repeated characters
            r'123|234|345|456|567|678|789|890',  # sequential numbers
            r'abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz',  # sequential letters
            r'qwe|wer|ert|rty|tyu|yui|uio|iop|asd|sdf|dfg|fgh|ghj|hjk|jkl|zxc|xcv|cvb|vbn|bnm'  # keyboard patterns
        ]

    def calculate_entropy(self):
        """Calculate password entropy using Shannon entropy and character space."""
        if not self.password:
            return 0
        
        # Character space calculation
        charset_size = 0
        if re.search(r'[a-z]', self.password):
            charset_size += 26
        if re.search(r'[A-Z]', self.password):
            charset_size += 26
        if re.search(r'[0-9]', self.password):
            charset_size += 10
        if re.search(r'[^a-zA-Z0-9]', self.password):
            charset_size += 32  # Common special characters
        
        # Shannon entropy calculation
        char_counts = {}
        for char in self.password:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        shannon_entropy = 0
        length = len(self.password)
        for count in char_counts.values():
            probability = count / length
            if probability > 0:
                shannon_entropy -= probability * math.log2(probability)
        
        # Effective entropy considering both character space and distribution
        max_entropy = math.log2(charset_size) * length if charset_size > 0 else 0
        effective_entropy = shannon_entropy * length * 0.7  # Discount factor for real-world patterns
        
        self.entropy_score = min(effective_entropy, max_entropy)
        return self.entropy_score

    def check_against_breaches(self):
        """Check if password appears in known breaches using HaveIBeenPwned API."""
        try:
            # Hash the password using SHA-1
            sha1_hash = hashlib.sha1(self.password.encode('utf-8')).hexdigest().upper()
            prefix = sha1_hash[:5]
            suffix = sha1_hash[5:]
              # Query HaveIBeenPwned API
            url = f"https://api.pwnedpasswords.com/range/{prefix}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                for line in response.text.splitlines():
                    hash_suffix, count = line.split(':')
                    if hash_suffix == suffix:
                        self.warnings.append(f"[WARNING] Password found in {count} data breaches!")
                        return int(count)
            return 0
        except Exception as e:
            self.warnings.append("Could not check against breach databases (network error)")
            return -1

    def check_patterns(self):
        """Advanced pattern detection."""
        pattern_score = 0
        
        # Check for weak patterns
        for pattern in self.weak_patterns:
            if re.search(pattern, self.password.lower()):
                self.suggestions.append(f"Avoid predictable patterns in password")
                pattern_score -= 1
                break
        
        # Check for keyboard patterns
        keyboard_rows = ['qwertyuiop', 'asdfghjkl', 'zxcvbnm', '1234567890']
        for row in keyboard_rows:
            for i in range(len(row) - 3):
                if row[i:i+4] in self.password.lower():
                    self.suggestions.append("Avoid keyboard patterns (qwerty, asdf, etc.)")
                    pattern_score -= 1
                    break
        
        return pattern_score

    def check_composition(self):
        """Enhanced composition checking based on NIST guidelines."""
        composition_score = 0
        length = len(self.password)
        
        # Length scoring (NIST recommends 8+ characters minimum)
        if length >= 16:
            composition_score += 3
        elif length >= 12:
            composition_score += 2
        elif length >= 8:
            composition_score += 1
        else:
            self.suggestions.append("Use at least 8 characters (12+ recommended)")
        
        # Character diversity
        char_types = 0
        if re.search(r'[a-z]', self.password):
            char_types += 1
        if re.search(r'[A-Z]', self.password):
            char_types += 1
        if re.search(r'[0-9]', self.password):
            char_types += 1
        if re.search(r'[^a-zA-Z0-9]', self.password):
            char_types += 1
        
        composition_score += char_types
        
        if char_types < 3:
            self.suggestions.append("Use a mix of uppercase, lowercase, numbers, and symbols")
        
        return composition_score

    def check_dictionary(self):
        """Check against common passwords and dictionary words."""
        lower_password = self.password.lower()
          # Check exact matches
        if lower_password in self.common_passwords:
            self.warnings.append("[ALERT] Password is in common password list!")
            return -5
        
        # Check if password contains common words
        for common in self.common_passwords:
            if common in lower_password and len(common) > 3:
                self.suggestions.append(f"Avoid using common words like '{common}'")
                return -2
        
        # Check for simple transformations (leet speak, etc.)
        leet_map = {'@': 'a', '3': 'e', '1': 'i', '0': 'o', '5': 's', '7': 't', '4': 'a'}
        normalized = lower_password
        for leet, normal in leet_map.items():
            normalized = normalized.replace(leet, normal)
        
        if normalized in self.common_passwords:
            self.suggestions.append("Simple character substitutions don't significantly improve security")
            return -3
        
        return 0

    def estimate_crack_time(self):
        """Estimate time to crack using modern techniques."""
        # Assume various attack scenarios
        online_slow = 100  # 100 attempts per second (rate-limited online)
        online_fast = 10000  # 10K attempts per second (fast online)
        offline_slow = 1e7  # 10M attempts per second (CPU)
        offline_fast = 1e11  # 100B attempts per second (GPU cluster)
        
        charset_size = 95  # Full ASCII printable characters
        possible_passwords = charset_size ** len(self.password)
        
        # Average case: half the keyspace
        avg_attempts = possible_passwords / 2
        
        scenarios = {
            "Online (slow)": avg_attempts / online_slow,
            "Online (fast)": avg_attempts / online_fast,
            "Offline (CPU)": avg_attempts / offline_slow,
            "Offline (GPU)": avg_attempts / offline_fast
        }
        
        return scenarios

    def format_time(self, seconds):
        """Format time duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            return f"{seconds/60:.1f} minutes"
        elif seconds < 86400:
            return f"{seconds/3600:.1f} hours"
        elif seconds < 31536000:
            return f"{seconds/86400:.1f} days"
        else:
            return f"{seconds/31536000:.1f} years"

    def analyze(self):
        """Comprehensive password analysis."""
        print(f"{Fore.CYAN}Advanced Password Security Analysis{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        
        # Core analysis
        composition_score = self.check_composition()
        dictionary_score = self.check_dictionary()
        pattern_score = self.check_patterns()
        entropy = self.calculate_entropy()
        breach_count = self.check_against_breaches()
        
        # Calculate final score
        self.strength_score = max(0, composition_score + dictionary_score + pattern_score + (entropy / 10))
        max_score = 10
        
        # Display results
        print(f"Password: {'*' * len(self.password)}")
        print(f"Length: {len(self.password)} characters")
        print(f"Entropy: {entropy:.1f} bits")
          # Strength bar
        filled = int((self.strength_score / max_score) * 20)
        bar = '#' * filled + '-' * (20 - filled)
        
        if self.strength_score >= 8:
            strength_color = Fore.GREEN
            rating = "Very Strong"
        elif self.strength_score >= 6:
            strength_color = Fore.YELLOW
            rating = "Strong"
        elif self.strength_score >= 4:
            strength_color = Fore.YELLOW
            rating = "Medium"
        elif self.strength_score >= 2:
            strength_color = Fore.RED
            rating = "Weak"
        else:
            strength_color = Fore.RED
            rating = "Very Weak"
        
        print(f"Strength: {strength_color}[{bar}] {self.strength_score:.1f}/{max_score}{Style.RESET_ALL}")
        print(f"Rating: {strength_color}{rating}{Style.RESET_ALL}")
        
        # Breach information
        if breach_count > 0:
            print(f"{Fore.RED}Breach Status: Found in {breach_count:,} breaches{Style.RESET_ALL}")
        elif breach_count == 0:
            print(f"{Fore.GREEN}Breach Status: Not found in known breaches{Style.RESET_ALL}")
        
        # Crack time estimates
        print(f"\n{Fore.CYAN}Estimated Crack Times:{Style.RESET_ALL}")
        crack_times = self.estimate_crack_time()
        for scenario, time_seconds in crack_times.items():
            time_str = self.format_time(time_seconds)
            if time_seconds < 86400:  # Less than a day
                color = Fore.RED
            elif time_seconds < 31536000:  # Less than a year
                color = Fore.YELLOW
            else:
                color = Fore.GREEN
            print(f"  {scenario}: {color}{time_str}{Style.RESET_ALL}")
          # Warnings
        if self.warnings:
            print(f"\n{Fore.RED}[!] Warnings:{Style.RESET_ALL}")
            for warning in self.warnings:
                print(f"  {warning}")
          # Suggestions
        if self.suggestions:
            print(f"\n{Fore.YELLOW}[*] Suggestions:{Style.RESET_ALL}")
            for suggestion in self.suggestions:
                print(f"  * {suggestion}")
          # NIST compliance check
        print(f"\n{Fore.CYAN}NIST Compliance:{Style.RESET_ALL}")
        nist_compliant = (len(self.password) >= 8 and 
                         breach_count == 0 and 
                         dictionary_score >= 0)
        
        if nist_compliant:
            print(f"  {Fore.GREEN}[+] Meets NIST guidelines{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}[-] Does not meet NIST guidelines{Style.RESET_ALL}")

def main():
    parser = argparse.ArgumentParser(description="Advanced Password Security Checker")
    parser.add_argument("--password", help="Password to check (will prompt if not provided)")
    args = parser.parse_args()
    
    if args.password:
        password = args.password
    else:
        import getpass
        password = getpass.getpass("Enter password to analyze: ")
    
    if not password:
        print(f"{Fore.RED}[ERROR] No password provided{Style.RESET_ALL}")
        sys.exit(1)
    
    try:
        checker = AdvancedPasswordChecker(password)
        checker.analyze()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[INFO] Analysis interrupted by user{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Unexpected error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
