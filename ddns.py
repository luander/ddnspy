"""
DDNSPY Dynamic DNS Updater

This is a simple script to discover current public IP and update a hostname A record to it.

```
import ddnspy
ddnspy.update("subdomain.example.com")
```

"""
import argparse
import logging
import sys
import os
import CloudFlare
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from ddnspy.providers.cf import (
    do_dns_update,
    get_zone_id
)
from ddnspy.dns import (
    get_public_ip,
    resolve_hostname
)


def main():
    setup_logging()
    args = _get_args()
    current_ip = resolve_hostname(args.hostname)
    public_ip = get_public_ip()
    if not public_ip:
        logging.error(f'{args.hostname} resolution failure')
        sys.exit(os.EX_SOFTWARE)
    if not current_ip:
        logging.error(f'{args.hostname} cannot determine public IP')
        sys.exit(os.EX_SOFTWARE)

    if current_ip == public_ip:
        logging.info(f'{args.hostname} -> A({current_ip}) == Public IP({public_ip})')
        sys.exit(os.EX_OK)

    cf: CloudFlare = CloudFlare.CloudFlare()
    update(cf, args.hostname, public_ip)


def setup_logging():
    """Configures Sentry.io logging"""
    sentry_logging = LoggingIntegration(
        level = logging.INFO,
        event_level = logging.ERROR
    )
    sentry_dsn = os.environ.get("DDNSPY_SENTRY_DSN", '')
    sentry_sdk.init(
        dsn = sentry_dsn,
        integrations = [
            sentry_logging
        ]
    )


def _get_args():
    parser = argparse.ArgumentParser(description='DDNSPY Dynamic DNS Updater')
    parser.add_argument(
        'hostname',
        help='Hostname to update',
        type=str
    )
    parser.add_argument(
        '-p',
        '--provider',
        help='DNS Provider. Currently only supports `cf`',
        required=False,
        default='cf',
        choices=['cf'],
        type=str
    )
    return parser.parse_args()


def update(provider, hostname: str, ip: str):
    """
    DDNSPY Dynamic DNS Updater

    This is a simple script to discover current public IP and update a hostname A record to it.

    ```
    import ddnspy
    import CloudFlare

    provider = CloudFlare.CloudFlare()
    ddnspy.update(provider, "subdomain.example.com", "127.0.0.1")
    ```

    """
    zone_name = '.'.join(hostname.split('.')[-2:]) # FQDN of the provided hostname
    
    zone_id = get_zone_id(provider, zone_name)
    do_dns_update(provider, zone_id, hostname, ip)


if __name__ == "__main__":
    main()
