
import gzip
import pymysql.cursors

from common import MARIA_DB_CONFIGURATION
import ldap_parser


class DBError(Exception):
    """Base error class for API stuff."""

    def __init__(self, message=''):
        self.message = message


def open_mdb_connection(logger):
    for host in MARIA_DB_CONFIGURATION['hosts']:
        try:
            connection = pymysql.connect(
                user=MARIA_DB_CONFIGURATION['user'],
                password=MARIA_DB_CONFIGURATION['password'],
                database=MARIA_DB_CONFIGURATION['database'],
                host=host,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
            )
        except:
            if host == MARIA_DB_CONFIGURATION['hosts'][-1]:
                log_str = "Failed to connect to any MariaDB host"
                logger.exception(log_str, exc_info=True)
                raise DBError(log_str)
            else:
                logger.warning('Failed to connect to MariaDB on host {}. Trying next host.'.format(host))
        else:
            if connection.open:
                logger.debug('mariadb connection to host {} successful.'.format(host))
                return connection
            else:
                err_str = 'Connection to MariaDB failed.'
                logger.error(err_str)
                raise DBError(err_str)


class DetectSubmitLock:
    def __init__(self, output_file, mariadb_connection, logger):
        self.output_file = output_file
        self.mariadb_connection = mariadb_connection
        self.logger = logger

    def process_entry(self, dn, entry):
        self.logger.debug('Start processing of dn ' + dn)
        self.logger.debug(entry)

        if entry['objectClass'][-1].decode("utf-8") == 'mailaccount':
            object_class = 'mailaccount'
            address = entry['cn'][0].decode("utf-8")
            if 'forwardto' in entry:
                self.logger.debug('Skipping alias account {}'.format(address))
                return
        else:
            self.logger.debug('Skipping object of class {}'.format(entry['objectClass'][-1].decode("utf-8")))
            return

        if 'lock' in entry:
            lock = entry['lock'][0].decode("utf-8")
            if lock == 'submit':
                self.logger.debug('Address {} has lock = submit!'.format(address))
                locking_date = self.check_account_history(address)
                self.output_file.write(address + ' ' + object_class + ' locking date in MariaDB: ' +
                                       locking_date + '\n')

    def check_account_history(self, address):
        self.logger.debug('Checking account: {}'.format(address))
        cursor = self.mariadb_connection.cursor()
        query_string = 'SELECT ts FROM {} WHERE account=\'{}\''.format(MARIA_DB_CONFIGURATION['table'], address)
        self.logger.debug('Mariadb query: ' + query_string)
        mariadb_hits = cursor.execute(query_string)

        if mariadb_hits == 0:
            self.logger.debug('Account not found in mariadb during policy period.')
            return 'Not found'
        else:
            result = cursor.fetchone()
            self.logger.debug('MariaDB first result: \n{}'.format(result))
            return result['ts'].strftime("%m/%d/%Y, %H:%M:%S")


def check_submit_locks(dump_file, logger):
    if dump_file.endswith('.gz'):
        input_file = gzip.open(dump_file, 'rb')
    else:
        input_file = open(dump_file, 'rb')

    output_file = open('lock_submit_accounts.txt', 'w')

    processing_object = DetectSubmitLock(output_file, mariadb_connection=open_mdb_connection(),
                                         logger=logger)
    parser = ldap_parser.ParseLDIF(input_file, processing_object)
    parser.parse()
