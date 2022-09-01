import CloudFlare
import requests
import logging
import sys
import socket


IP_PROVIDERS = [ 
    "https://ifconfig.me/ip",
    "https://icanhazip.com",
    "https://myip.dnsomatic.com",
    "https://myexternalip.com/raw",
    "https://api.ipify.org"
]


def main():
    """
    Dynamic DNS updater
    Based on Cloudflare SDK
    """
    host_name = sys.argv[1]
    zone_name = '.'.join(host_name.split('.')[-2:])
    current_ip = resolve_hostname(host_name)
    if not current_ip:
        logging.error(f"Cannot resolve {host_name}")
        
    public_ip = str(get_public_ip())
    if not public_ip:
        logging.error("Cannot obtain public IP")
        sys.exit(1)

    if current_ip != public_ip:
        cf = CloudFlare.CloudFlare()
        zone_name, zone_id = get_zone_info(cf, zone_name)
        do_dns_update(cf, zone_name, zone_id, host_name, public_ip)


def get_public_ip(providers=IP_PROVIDERS):
    """
    Try to get the current public IP from one of providers.
    Return upon success
    """
    for provider in providers:
        try:
            response = requests.get(provider)
            response.raise_for_status()
            return response.content.rstrip().decode('utf-8')
        except:
            logging.error(f"Error accessing {provider}")


def resolve_hostname(hostname):
    """
    Always returns the first IP address resolved by the hostname
    """
    _, _, ipaddrlist = socket.gethostbyname_ex(hostname)
    logging.info(f"{hostname} resolves to {ipaddrlist}")
    return ipaddrlist[0]
    

def get_zone_info(cf, zone_name):
    # grab the zone identifier
    try:
        params = {'name':zone_name}
        zones = cf.zones.get(params=params)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        exit('/zones %d %s - api call failed' % (e, e))
    except Exception as e:
        exit('/zones.get - %s - api call failed' % (e))

    if len(zones) == 0:
        exit('/zones.get - %s - zone not found' % (zone_name))

    if len(zones) != 1:
        exit('/zones.get - %s - api call returned %d items' % (zone_name, len(zones)))

    zone = zones[0]

    return (zone['name'], zone['id'])


def do_dns_update(cf, zone_name, zone_id, dns_name, ip_address, ip_address_type='A'):
    """Cloudflare API code - example"""

    try:
        params = {'name':dns_name, 'match':'all', 'type':ip_address_type}
        dns_records = cf.zones.dns_records.get(zone_id, params=params)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        exit('/zones/dns_records %s - %d %s - api call failed' % (dns_name, e, e))

    updated = False

    # update the record - unless it's already correct
    for dns_record in dns_records:
        old_ip_address = dns_record['content']
        old_ip_address_type = dns_record['type']

        if ip_address_type not in ['A', 'AAAA']:
            # we only deal with A / AAAA records
            continue

        if ip_address_type != old_ip_address_type:
            # only update the correct address type (A or AAAA)
            # we don't see this becuase of the search params above
            print('IGNORED: %s %s ; wrong address family' % (dns_name, old_ip_address))
            continue

        if ip_address == old_ip_address:
            print('UNCHANGED: %s %s' % (dns_name, ip_address))
            updated = True
            continue

        proxied_state = dns_record['proxied']
 
        # Yes, we need to update this record - we know it's the same address type

        dns_record_id = dns_record['id']
        dns_record = {
            'name':dns_name,
            'type':ip_address_type,
            'content':ip_address,
            'proxied':proxied_state
        }
        try:
            dns_record = cf.zones.dns_records.put(zone_id, dns_record_id, data=dns_record)
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            exit('/zones.dns_records.put %s - %d %s - api call failed' % (dns_name, e, e))
        print('UPDATED: %s %s -> %s' % (dns_name, old_ip_address, ip_address))
        updated = True

    if updated:
        return

    # no exsiting dns record to update - so create dns record
    dns_record = {
        'name':dns_name,
        'type':ip_address_type,
        'content':ip_address
    }
    try:
        dns_record = cf.zones.dns_records.post(zone_id, data=dns_record)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        exit('/zones.dns_records.post %s - %d %s - api call failed' % (dns_name, e, e))
    print('CREATED: %s %s' % (dns_name, ip_address))
    

if __name__ == "__main__":
    main()