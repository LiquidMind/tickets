import logging
import sqlalchemy as sa
from optparse import OptionParser

from common.functions import print_and_log
from api.accounts import get_free_account, update_account
import conf

engine = sa.create_engine(conf.MYSQL_CONNECTION_STRING, isolation_level="AUTOCOMMIT")

logger = logging.getLogger('generate_personal_data')
handler = logging.FileHandler('logsacounts.log')
handler.setFormatter(logging.Formatter(fmt='[%(asctime)s: %(levelname)s] %(message)s'))
logger.setLevel('DEBUG')
logger.addHandler(handler)


def main():
    usage = """
    python -m maintenance.accounts --get-free
    python -m maintenance.accounts --set-used --email test@test.com
    """
    parser = OptionParser(usage=usage)

    parser.add_option(
        '--get-free', action='store_true', dest='get_free', default=False,
        help='Returns not used account')
    parser.add_option(
        '--set-used', action='store_true', dest='set_used', default=False,
        help='Mark account as used')
    parser.add_option('--email', action='store', dest='email', default=None,
                      help='Email for process')
    parser.add_option('--after-1000', action='store', dest='after_1000', default=None,
                      help='Get accounts that added later, after 1000')

    (options, args) = parser.parse_args()

    if options.get_free:
        print_and_log(logger, 'Getting account')

        if options.after_1000:
            prime_clause = "AND prime = 'after_1000'"
        else:
            prime_clause = "AND prime IS NULL"

        account = get_free_account(prime_clause)
        print(account)

        return account
    elif options.set_used:
        if options.email is None:
            parser.error('--email option required')
        print_and_log(logger, f'Marking account as used: {options.email}')
        upd_res = update_account(options.email, {'used': 1})
        print(upd_res)
        return upd_res
    else:
        parser.print_help()

    return True


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        raise e

print('DONE')
