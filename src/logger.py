
#
# Author: Elias Sjödin
# Created: 2024-12-31

import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

def log_info(msg: str, newline: bool = False) -> None:
    """
    Logs an informational message in blue.
    """
    if newline:
        print()
    for line in msg.splitlines():
        print(Fore.BLUE + "[INFO] " + Style.RESET_ALL + line)

def log_success(msg: str, newline: bool = False) -> None:
    """
    Logs a success or confirmation message in green.
    """
    if newline:
        print()
    for line in msg.splitlines():
        print(Fore.GREEN + "[SUCCESS] " + Style.RESET_ALL + line)

def log_warning(msg: str, newline: bool = False) -> None:
    """
    Logs a warning message in yellow.
    """
    if newline:
        print()
    for line in msg.splitlines():
        print(Fore.YELLOW + "[WARNING] " + Style.RESET_ALL + line)

def log_error(msg: str, newline: bool = False) -> None:
    """
    Logs an error message in red.
    """
    if newline:
        print()
    for line in msg.splitlines():
        print(Fore.RED + "[ERROR] " + Style.RESET_ALL + line)

def log_custom(tag: str, msg: str, color: Fore = Fore.WHITE, newline: bool = False) -> None:
    """
    Logs a custom message in a specified color.
    """
    if newline:
        print()
    for line in msg.splitlines():
        print(color + f"[{tag}] " + Style.RESET_ALL + line)
