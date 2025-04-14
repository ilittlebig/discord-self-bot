# Enhanced logging functionality with color-coded output
#
# Author: Elias Sjödin
# Created: 2024-12-31

import colorama
from colorama import Fore, Style, Back
import time
import os
from datetime import datetime

# Initialize colorama
colorama.init(autoreset=True)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Current log file
current_log_file = f"logs/discord_bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def _get_timestamp():
    """Get formatted timestamp for logs."""
    return datetime.now().strftime("%H:%M:%S")

def _log_to_file(level, msg):
    """Write log message to file."""
    try:
        with open(current_log_file, "a") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] [{level}] {msg}\n")
    except Exception as e:
        print(f"{Fore.RED}Failed to write to log file: {e}{Style.RESET_ALL}")

def log_info(msg: str, newline: bool = False) -> None:
    """
    Logs an informational message in blue.
    """
    if newline:
        print()
    timestamp = _get_timestamp()
    for line in msg.splitlines():
        print(f"{Fore.WHITE}[{timestamp}] {Fore.BLUE}[INFO] {Style.RESET_ALL}{line}")
    _log_to_file("INFO", msg)

def log_success(msg: str, newline: bool = False) -> None:
    """
    Logs a success or confirmation message in green.
    """
    if newline:
        print()
    timestamp = _get_timestamp()
    for line in msg.splitlines():
        print(f"{Fore.WHITE}[{timestamp}] {Fore.GREEN}[SUCCESS] {Style.RESET_ALL}{line}")
    _log_to_file("SUCCESS", msg)

def log_warning(msg: str, newline: bool = False) -> None:
    """
    Logs a warning message in yellow.
    """
    if newline:
        print()
    timestamp = _get_timestamp()
    for line in msg.splitlines():
        print(f"{Fore.WHITE}[{timestamp}] {Fore.YELLOW}[WARNING] {Style.RESET_ALL}{line}")
    _log_to_file("WARNING", msg)

def log_error(msg: str, newline: bool = False) -> None:
    """
    Logs an error message in red.
    """
    if newline:
        print()
    timestamp = _get_timestamp()
    for line in msg.splitlines():
        print(f"{Fore.WHITE}[{timestamp}] {Fore.RED}[ERROR] {Style.RESET_ALL}{line}")
    _log_to_file("ERROR", msg)

def log_custom(tag: str, msg: str, color: Fore = Fore.WHITE, newline: bool = False) -> None:
    """
    Logs a custom message in a specified color.
    """
    if newline:
        print()
    timestamp = _get_timestamp()
    for line in msg.splitlines():
        print(f"{Fore.WHITE}[{timestamp}] {color}[{tag}] {Style.RESET_ALL}{line}")
    _log_to_file(tag, msg)

def log_highlight(msg: str, newline: bool = False) -> None:
    """
    Logs a highlighted message with background color.
    """
    if newline:
        print()
    timestamp = _get_timestamp()
    for line in msg.splitlines():
        print(f"{Fore.WHITE}[{timestamp}] {Back.BLUE}{Fore.WHITE}[HIGHLIGHT] {line}{Style.RESET_ALL}")
    _log_to_file("HIGHLIGHT", msg)
