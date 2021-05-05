
import sys
from datetime import datetime, timedelta

from fn_pymapi import MapiClient
from fn_pymapi.errors import PymapiError


# credentials:
PMAPI_USER = 'admin'
PMAPI_PASSWORD = 'cnlbISgaJHtMkGDVjgxGi11E5EpO4vpc'
PMAPI_HOST = 'api.freenet.de'
PMAPI_VERSION = 'stable'


pmapi_client = MapiClient(PMAPI_USER, PMAPI_PASSWORD, hostname=PMAPI_HOST, mapi_version=PMAPI_VERSION)


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


def check_if_is_older(mariaDB_history_entry, limit_days_ago, logger):
    entry_datetime = datetime.strptime(mariaDB_history_entry, '%d/%m/%Y, %H:%M:%S')
    date_limit = datetime.now() - timedelta(days=int(limit_days_ago))
    if entry_datetime < date_limit:
        logger.debug('MariadDB entry: {} is older than limit!'.format(entry_datetime))
        return True
    else:
        logger.debug('MariadDB entry: {} is newer than limit!'.format(entry_datetime))
        return False


def delete_old_entries(input_file, logger, limit_number_of_accounts: int = 10, limit_days_ago=None):
    with open(input_file, 'r') as f:
        lines = f.readlines()
    with open(input_file, "w") as f:
        delete_counter = 0
        for line in lines:
            if delete_counter >= limit_number_of_accounts:
                f.write(line)
            else:
                delete_counter += 1
                address = line.split(' ')[0]
                mariaDB_history_entry = line.split('MariaDB: ')[1]
                logger.debug('Checking account {} with MariaDB history entry {}'.format(address, mariaDB_history_entry))
                if mariaDB_history_entry is not 'Not found':
                    if limit_days_ago is None or check_if_is_older(mariaDB_history_entry, limit_days_ago, logger) is False:
                        continue
                logger.debug('Proceeding to remove lock for account {}'.format(address))
                try:
                    route = address_route(address)
                except ValueError as err:
                    logger.error('ERROR: {}'.format(err))
                    return
                # Double check to be sure that it is not an alias account
                try:
                    ret = pmapi_client.make_request('get', route)
                except PymapiError as err:
                    print('PMAPI error: {}'.format(err))
                    continue
                else:
                    data = ret.json()['data']
                    if 'forwardto' in data:
                        logger.warning('Address {} is an alias account!'.format(address))
                        continue
                payload = dict()
                payload['lock'] = ""
                try:
                    pmapi_client.make_request('patch', route, payload=payload)
                except PymapiError as err:
                    logger.error('PMAPI error: {}'.format(err))
                    sys.exit(1)
                else:
                    logger.debug('Lock -> Submit was deleted for account {}'.format(address))