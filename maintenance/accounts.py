import logging
import sqlalchemy as sa
from optparse import OptionParser

from common.functions import print_and_log
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

    (options, args) = parser.parse_args()

    if options.get_free:
        print_and_log(logger, 'Getting account')
        with engine.connect() as conn:
            account = conn.execute(sa.text("""
                SELECT 
                    a.id, a.name, a.surname, a.email, a.birth_date, a.personal_id, c.name, cd.address, cd.phone, a.prime
                FROM 
                    accounts a 
                    LEFT JOIN countries c ON a.country_id = c.id
                    LEFT JOIN countries_data cd ON a.country_id = cd.country_id
                WHERE
                    a.email_verified = 1 
                    AND used = 0 
                LIMIT 1
            """)).fetchone()
            print(account)
        return account
    elif options.set_used:
        if options.email is None:
            parser.error('--email option required')
        print_and_log(logger, f'Marking account as used: {options.email}')
        with engine.connect() as conn:
            upd_res = conn.execute(sa.text("""
                UPDATE accounts SET used = 1 WHERE email = :email
            """), {'email': options.email}).rowcount
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
