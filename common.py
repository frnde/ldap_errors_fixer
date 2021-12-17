
import sys
import logging
import re
from logging.handlers import SysLogHandler
from fn_pymapi import MapiClient


#Logger
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
#handler = SysLogHandler('/dev/log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
LOGGER.addHandler(handler)


# credentials:
PMAPI_USER = 'admin'
PMAPI_PASSWORD = 'cnlbISgaJHtMkGDVjgxGi11E5EpO4vpc'
PMAPI_HOST = 'api.freenet.de'
PMAPI_VERSION = 'legacy'


pmapi_client = MapiClient(PMAPI_USER, PMAPI_PASSWORD, hostname=PMAPI_HOST, mapi_version=PMAPI_VERSION)


MARIA_DB_CONFIGURATION = {
    'hosts': ['mdb0.freenet.de', 'mdb1.freenet.de'],
    'database': 'account_locking',
    'table': 'locking_history',
    'user': 'postmaster',
    'password': 'headscarf-cure-prodigal-crestless-stiffly-job',
}


def split_address(address: str) -> (str, str):
    try:
        return address.split('@')
    except ValueError:
        raise ValueError('Invalid email address {}'.format(address))


def address_route(address: str):
    try:
        localpart, domain = split_address(address)
    except ValueError as err:
        raise err
    return 'domains/{}/localparts/{}'.format(domain, localpart)


def address_field_route(address: str, field: str):
    try:
        localpart, domain = split_address(address)
    except ValueError as err:
        raise err
    return 'domains/{}/localparts/{}/{}'.format(domain, localpart, field)


def domain_route(domain: str):
    return 'domains/{}'.format(domain)


def mailing_list_route(address: str):
    try:
        mailinglist, domain = split_address(address)
    except ValueError as err:
        raise err
    return 'domains/{}/mailinglists/{}'.format(domain, mailinglist)


def remove_01019(addr):
    if not addr:
        return addr
    return re.sub(
        r'@01019freenet\.de$',
        '@freenet.de',
        addr,
        flags=re.IGNORECASE,
    )
