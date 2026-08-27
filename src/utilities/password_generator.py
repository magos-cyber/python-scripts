#!/usr/bin/env python3
"""
password_generator.py — Generate secure passwords and passphrases
Supports random passwords, memorable passphrases, and PINs
"""

import secrets
import string
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Word list for passphrases (EFF short list sample)
WORD_LIST = [
    "apple", "banana", "cherry", "date", "elder", "fig", "grape", "honey",
    "iris", "jade", "kiwi", "lemon", "mango", "nut", "olive", "pear",
    "quince", "raspberry", "strawberry", "tomato", "ugli", "vanilla",
    "watermelon", "xenon", "yam", "zucchini", "amber", "bronze", "coral",
    "diamond", "emerald", "frost", "gold", "harbor", "ivory", "jasper",
    "karma", "lunar", "maple", "noble", "ocean", "pearl", "quartz",
    "ruby", "silver", "tiger", "ultra", "violet", "willow", "xray", "yellow", "zephyr"
]


def generate_password(length: int = 20, use_uppercase: bool = True, 
                      use_digits: bool = True, use_symbols: bool = True) -> str:
    """Generate a random password"""
    chars = string.ascii_lowercase
    
    if use_uppercase:
        chars += string.ascii_uppercase
    if use_digits:
        chars += string.digits
    if use_symbols:
        chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"
    
    # Ensure at least one of each required type
    password = []
    if use_uppercase:
        password.append(secrets.choice(string.ascii_uppercase))
    if use_digits:
        password.append(secrets.choice(string.digits))
    if use_symbols:
        password.append(secrets.choice("!@#$%^&*"))
    
    # Fill remaining length
    for _ in range(length - len(password)):
        password.append(secrets.choice(chars))
    
    # Shuffle
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)


def generate_passphrase(word_count: int = 4, separator: str = "-", 
                        capitalize: bool = False, add_number: bool = True) -> str:
    """Generate a memorable passphrase"""
    words = [secrets.choice(WORD_LIST) for _ in range(word_count)]
    
    if capitalize:
        words = [w.capitalize() for w in words]
    
    passphrase = separator.join(words)
    
    if add_number:
        passphrase += separator + str(secrets.randbelow(1000)).zfill(3)
    
    return passphrase


def generate_pin(length: int = 6) -> str:
    """Generate a numeric PIN"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def calculate_entropy(length: int, charset_size: int) -> float:
    """Calculate password entropy in bits"""
    import math
    return length * math.log2(charset_size)


def main():
    parser = argparse.ArgumentParser(description="Password Generator")
    parser.add_argument("--length", "-l", type=int, default=20, help="Password length")
    parser.add_argument("--count", "-c", type=int, default=1, help="Number to generate")
    parser.add_argument("--no-upper", action="store_true", help="Exclude uppercase")
    parser.add_argument("--no-digits", action="store_true", help="Exclude digits")
    parser.add_argument("--no-symbols", action="store_true", help="Exclude symbols")
    parser.add_argument("--passphrase", "-p", action="store_true", help="Generate passphrase")
    parser.add_argument("--words", "-w", type=int, default=4, help="Words in passphrase")
    parser.add_argument("--pin", action="store_true", help="Generate PIN")
    parser.add_argument("--pin-length", type=int, default=6, help="PIN length")
    args = parser.parse_args()
    
    print(f"🔐 Password Generator")
    print(f"{'='*50}\n")
    
    if args.pin:
        for i in range(args.count):
            pin = generate_pin(args.pin_length)
            print(f"{i+1}. {pin}")
    
    elif args.passphrase:
        for i in range(args.count):
            passphrase = generate_passphrase(args.words)
            print(f"{i+1}. {passphrase}")
    
    else:
        for i in range(args.count):
            password = generate_password(
                args.length,
                not args.no_upper,
                not args.no_digits,
                not args.no_symbols
            )
            entropy = calculate_entropy(args.length, 94)
            print(f"{i+1}. {password}  ({entropy:.0f} bits entropy)")
    
    print()


if __name__ == "__main__":
    main()