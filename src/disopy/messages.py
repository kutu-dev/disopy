from colorama import Fore, Style


def info(issuer: str, message: str) -> None:
    print(
        f"{Style.BRIGHT}{issuer}{Style.RESET_ALL} | {Fore.GREEN}[INFO]{Style.RESET_ALL} {message}"
    )


def warn(issuer: str, message: str) -> None:
    print(
        f"{Style.BRIGHT}{issuer}{Style.RESET_ALL} | {Fore.YELLOW}[WARN]{Style.RESET_ALL} {message}"
    )


def error(issuer: str, message: str) -> None:
    print(
        f"{Style.BRIGHT}{issuer}{Style.RESET_ALL} | {Fore.RED}[ERROR]{Style.RESET_ALL} {message}"
    )
