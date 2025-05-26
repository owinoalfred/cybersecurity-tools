import hashlib
import time
import argparse
import sys
import threading
import itertools
import string
from queue import Queue, Empty
from colorama import init, Fore, Style
import logging

# Initialize colorama for colored output
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='hash_cracker_advanced.log'
)

class AdvancedHashCracker:
    def __init__(self, hash_to_crack, hash_type='md5', threads=4):
        self.hash_to_crack = hash_to_crack.lower().strip()
        self.hash_type = hash_type.lower()
        self.threads = threads
        self.hash_func = getattr(hashlib, self.hash_type, None)
        self.found = None
        self.queue = Queue()
        self.start_time = time.time()
        self.attempts = 0
        self.lock = threading.Lock()
        self.total_passwords_generated = 0

    def validate(self):
        """Validate inputs and hash format."""
        if not self.hash_func:
            print(f"{Fore.RED}[ERROR] Unsupported hash type: {self.hash_type}{Style.RESET_ALL}")
            print(f"Supported types: md5, sha1, sha256, sha512")
            return False
        if not self.hash_to_crack:
            print(f"{Fore.RED}[ERROR] Hash cannot be empty{Style.RESET_ALL}")
            return False
        
        # Validate hash format
        expected_lengths = {
            'md5': 32,
            'sha1': 40,
            'sha256': 64,
            'sha512': 128
        }
        
        if len(self.hash_to_crack) != expected_lengths.get(self.hash_type, 0):
            print(f"{Fore.RED}[ERROR] Invalid {self.hash_type.upper()} hash length{Style.RESET_ALL}")
            print(f"Expected: {expected_lengths.get(self.hash_type)} characters, Got: {len(self.hash_to_crack)}")
            return False
        
        return True

    def dictionary_attack(self, wordlist_path):
        """Dictionary-based attack with common transformations."""
        try:
            with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as file:
                for line in file:
                    base_word = line.strip()
                    if not base_word:
                        continue
                    
                    # Try the word as-is
                    self.queue.put(base_word)
                    self.total_passwords_generated += 1
                    
                    # Common transformations
                    transformations = [
                        base_word.upper(),
                        base_word.lower(),
                        base_word.capitalize(),
                        base_word + '!',
                        base_word + '123',
                        base_word + '1',
                        '123' + base_word,
                        base_word + '2024',
                        base_word + '2025',
                        base_word.replace('a', '@'),
                        base_word.replace('e', '3'),
                        base_word.replace('i', '1'),
                        base_word.replace('o', '0'),
                        base_word.replace('s', '$'),
                        base_word[::-1],  # Reverse
                    ]
                    
                    for transformed in transformations:
                        if transformed != base_word:  # Avoid duplicates
                            self.queue.put(transformed)
                            self.total_passwords_generated += 1
                            
        except FileNotFoundError:
            print(f"{Fore.RED}[ERROR] Wordlist file not found: {wordlist_path}{Style.RESET_ALL}")
            return False
        return True

    def brute_force_attack(self, min_length=1, max_length=4, charset="letters_digits"):
        """Smart brute force with optimized character sets."""
        charsets = {
            "digits": string.digits,
            "letters": string.ascii_lowercase,
            "letters_digits": string.ascii_lowercase + string.digits,
            "letters_mixed": string.ascii_letters,
            "letters_mixed_digits": string.ascii_letters + string.digits,
            "all_printable": string.ascii_letters + string.digits + "!@#$%^&*"
        }
        
        chars = charsets.get(charset, string.ascii_lowercase + string.digits)
        
        print(f"{Fore.CYAN}[INFO] Starting brute force attack{Style.RESET_ALL}")
        print(f"Character set: {charset} ({len(chars)} characters)")
        print(f"Length range: {min_length}-{max_length}")
        
        for length in range(min_length, max_length + 1):
            print(f"{Fore.YELLOW}[INFO] Trying length {length}...{Style.RESET_ALL}")
            
            # Calculate total combinations for this length
            total_combinations = len(chars) ** length
            print(f"Total combinations for length {length}: {total_combinations:,}")
            
            # Generate all combinations of the current length
            for combo in itertools.product(chars, repeat=length):
                password = ''.join(combo)
                self.queue.put(password)
                self.total_passwords_generated += 1
                
                # Check if we found the password to stop generating
                if self.found:
                    return

    def hybrid_attack(self, wordlist_path, append_digits=True, prepend_digits=True):
        """Hybrid attack combining wordlist with brute force patterns."""
        try:
            with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as file:
                for line in file:
                    base_word = line.strip()
                    if not base_word or self.found:
                        continue
                    
                    # Append digits (word123, word2024, etc.)
                    if append_digits:
                        for i in range(100):  # 00-99
                            self.queue.put(f"{base_word}{i:02d}")
                            self.total_passwords_generated += 1
                        
                        for year in range(1990, 2026):
                            self.queue.put(f"{base_word}{year}")
                            self.total_passwords_generated += 1
                    
                    # Prepend digits
                    if prepend_digits:
                        for i in range(100):
                            self.queue.put(f"{i:02d}{base_word}")
                            self.total_passwords_generated += 1
                    
                    # Common patterns
                    patterns = ['!', '@', '#', '$', '*', '123', '321', '111']
                    for pattern in patterns:
                        self.queue.put(f"{base_word}{pattern}")
                        self.queue.put(f"{pattern}{base_word}")
                        self.total_passwords_generated += 2
                        
        except FileNotFoundError:
            print(f"{Fore.RED}[ERROR] Wordlist file not found: {wordlist_path}{Style.RESET_ALL}")
            return False
        return True

    def worker(self):
        """Optimized thread worker with better performance."""
        local_attempts = 0
        batch_size = 1000  # Process in batches for better performance
        
        while not self.found:
            batch = []
            
            # Get a batch of passwords
            for _ in range(batch_size):
                try:
                    password = self.queue.get_nowait()
                    batch.append(password)
                except Empty:
                    break
            
            if not batch:
                break
            
            # Process the batch
            for password in batch:
                if self.found:
                    break
                
                local_attempts += 1
                hashed_word = self.hash_func(password.encode()).hexdigest()
                
                if hashed_word == self.hash_to_crack:
                    with self.lock:
                        if not self.found:
                            self.found = password
                            self.attempts += local_attempts
                            elapsed = time.time() - self.start_time
                            print(f"\n{Fore.GREEN}🎉 PASSWORD FOUND: {password}{Style.RESET_ALL}")
                            print(f"Time elapsed: {elapsed:.2f} seconds")
                            print(f"Attempts: {self.attempts:,}")
                            print(f"Rate: {self.attempts/elapsed:,.0f} attempts/second")
                            logging.info(f"Password found: {password}, Time: {elapsed:.2f}s, Attempts: {self.attempts}")
                    return
                
                # Update global counter periodically
                if local_attempts % 10000 == 0:
                    with self.lock:
                        self.attempts += 10000
                        elapsed = time.time() - self.start_time
                        rate = self.attempts / elapsed if elapsed > 0 else 0
                        print(f"\r{Fore.YELLOW}[INFO] Attempts: {self.attempts:,} | Rate: {rate:,.0f}/sec | Time: {elapsed:.1f}s{Style.RESET_ALL}", end='')
                    local_attempts = 0
            
            # Mark batch as processed
            for _ in batch:
                self.queue.task_done()
        
        # Update final attempts count
        with self.lock:
            self.attempts += local_attempts

    def crack_with_strategy(self, strategy, **kwargs):
        """Execute cracking strategy."""
        if not self.validate():
            return False

        print(f"{Fore.CYAN}Advanced Hash Cracker v2.0{Style.RESET_ALL}")
        print(f"Hash: {self.hash_to_crack}")
        print(f"Hash type: {self.hash_type.upper()}")
        print(f"Strategy: {strategy}")
        print(f"Threads: {self.threads}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

        # Generate passwords based on strategy
        if strategy == "dictionary":
            wordlist = kwargs.get('wordlist', 'rockyou.txt')
            if not self.dictionary_attack(wordlist):
                return False
        elif strategy == "brute_force":
            min_len = kwargs.get('min_length', 1)
            max_len = kwargs.get('max_length', 4)
            charset = kwargs.get('charset', 'letters_digits')
            self.brute_force_attack(min_len, max_len, charset)
        elif strategy == "hybrid":
            wordlist = kwargs.get('wordlist', 'rockyou.txt')
            if not self.hybrid_attack(wordlist):
                return False

        print(f"\n{Fore.YELLOW}[INFO] Generated {self.total_passwords_generated:,} password candidates{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[INFO] Starting {self.threads} worker threads...{Style.RESET_ALL}")

        # Start worker threads
        threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()
            threads.append(t)

        # Wait for completion or password found
        try:
            while not self.found and any(t.is_alive() for t in threads):
                time.sleep(0.1)
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[INFO] Cracking interrupted by user{Style.RESET_ALL}")
            return False

        # Final results
        elapsed = time.time() - self.start_time
        if not self.found:
            print(f"\n{Fore.RED}❌ Password not found{Style.RESET_ALL}")
            print(f"Time elapsed: {elapsed:.2f} seconds")
            print(f"Attempts: {self.attempts:,}")
            print(f"Average rate: {self.attempts/elapsed:,.0f} attempts/second")
            logging.info(f"Password not found, Time: {elapsed:.2f}s, Attempts: {self.attempts}")
        
        return self.found is not None

def main():
    parser = argparse.ArgumentParser(description="Advanced Hash Cracker v2.0")
    parser.add_argument("hash", help="Hash to crack")
    parser.add_argument("strategy", choices=['dictionary', 'brute_force', 'hybrid'], 
                       help="Cracking strategy")
    parser.add_argument("--type", default="md5", 
                       choices=['md5', 'sha1', 'sha256', 'sha512'], 
                       help="Hash type (default: md5)")
    parser.add_argument("--threads", type=int, default=4, 
                       help="Number of threads (default: 4)")
    parser.add_argument("--wordlist", default="rockyou.txt", 
                       help="Wordlist file for dictionary/hybrid attacks")
    parser.add_argument("--min-length", type=int, default=1, 
                       help="Minimum length for brute force (default: 1)")
    parser.add_argument("--max-length", type=int, default=4, 
                       help="Maximum length for brute force (default: 4)")
    parser.add_argument("--charset", default="letters_digits",
                       choices=['digits', 'letters', 'letters_digits', 'letters_mixed', 'letters_mixed_digits', 'all_printable'],
                       help="Character set for brute force (default: letters_digits)")
    
    args = parser.parse_args()

    try:
        cracker = AdvancedHashCracker(args.hash, args.type, args.threads)
        
        kwargs = {
            'wordlist': args.wordlist,
            'min_length': args.min_length,
            'max_length': args.max_length,
            'charset': args.charset
        }
        
        success = cracker.crack_with_strategy(args.strategy, **kwargs)
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[INFO] Cracking interrupted by user{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Unexpected error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
