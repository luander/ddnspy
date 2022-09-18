from typing import List
import requests
import logging
import socket

IP_PROVIDERS = [
    "https://ifconfig.me/ip",
    "https://icanhazip.com",
    "https://myip.dnsomatic.com",
    "https://myexternalip.com/raw",
    "https://api.ipify.org"
]


def get_public_ip(providers: List[str] = IP_PROVIDERS) -> str:
    """
    Try to get the current public IP from one of providers.
    Return upon success
    """
    for provider in providers:
        try:
            response = requests.get(provider)
            response.raise_for_status()
            return response.content.rstrip().decode('utf-8')
        except requests.exceptions.HTTPError as e:
            logging.error(f"Error accessing {provider}: {e}")
    return None


def resolve_hostname(hostname: str) -> str:
    """
    Always returns the first IP address resolved by the hostname
    """
    try:
        _, _, ipaddrlist = socket.gethostbyname_ex(hostname)
        logging.info(f"{hostname} resolves to {ipaddrlist}")
        return ipaddrlist[0]
    except socket.gaierror:
        logging.exception(f'Unable to resolve {hostname}')
    return None