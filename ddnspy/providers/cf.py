import CloudFlare
import logging


def get_zone_id(cf, zone_name):
    """Get ID of a DNS zone

    Args:
        cf (CloufFlare): CloudFlare client
        zone_name (str): Name of the zone

    Returns:
        str: Zone ID
    """
    result = None
    try:
        params = {'name':zone_name}
        zones = cf.zones.get(params=params)
        if zones or len(zones) == 1:
            result = zones[0]['id']
        else:
            logging.error('/zones - failed to parse zone')
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        logging.exception(f'/zones {e} - api call failed')
    except Exception as e:
        logging.exception(f'/zones.get - {e} - api call failed')

    return result


def do_dns_update(cf, zone_id, dns_name, ip_address, ip_address_type='A'):
    """Updates DNS record to a provided IP address

    Args:
        cf (CloufFlare): CloudFlare client
        zone_id (str): DNS zone ID
        dns_name (str): DNS entry to update
        ip_address (str): IP address to be assigned to the DNS entry
        ip_address_type (str, optional): DNS Record type (A and AAAA supported only). Defaults to 'A'.
    """
    try:
        params = {'name':dns_name, 'match':'all', 'type':ip_address_type}
        dns_records = cf.zones.dns_records.get(zone_id, params=params)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        logging.exception(f'/zones/dns_records {dns_name} - {e} - api call failed')
        return

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
            logging.info(f'IGNORED: {dns_name} {old_ip_address}; wrong address family')
            continue

        if ip_address == old_ip_address:
            logging.info(f'UNCHANGED: {dns_name} {ip_address}')
            updated = True
            continue

        proxied_state = dns_record['proxied']
        dns_record_id = dns_record['id']
        dns_record = {
            'name':dns_name,
            'type':ip_address_type,
            'content':ip_address,
            'proxied':proxied_state
        }
        try:
            dns_record = cf.zones.dns_records.put(zone_id, dns_record_id, data=dns_record)
            updated = True
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            logging.exception(f'/zones.dns_records.put {dns_name} - {e} - api call failed')
        logging.info(f'UPDATED: {dns_name} {old_ip_address} -> {ip_address}')

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
        logging.exception(f'/zones.dns_records.post {dns_name} - {e} - api call failed')
    logging.info(f'CREATED: {dns_name} {ip_address}')