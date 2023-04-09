import logging
import pandas as pd
import sqlalchemy as sa
from optparse import OptionParser

import googlemaps  # https://googlemaps.github.io/google-maps-services-python/docs/index.html

from api import get_obj_id
from common.functions import print_and_log
from . import PersonalData

import conf

engine = sa.create_engine(conf.MYSQL_CONNECTION_STRING, isolation_level="AUTOCOMMIT")
gmaps = googlemaps.Client(key=conf.GOOGLE_API_KEY)

logger = logging.getLogger('generate_personal_data')
handler = logging.FileHandler('logs/generate_personal_data.log')
handler.setFormatter(logging.Formatter(fmt='[%(asctime)s: %(levelname)s] %(message)s'))
logger.setLevel('DEBUG')
logger.addHandler(handler)


def check_subdomain_on_host(email: str):
    subdomain = email.split('@')[1]
    return get_obj_id(subdomain, 'host')


def check_if_exists(user_data):
    q_exists = sa.text("""
        SELECT count(id) FROM accounts 
        WHERE
            (name = :name AND surname = :surname) OR email = :email OR (address_id <> 0 AND address_id = :address_id) 
            OR (personal_id <> '' AND personal_id = :personal_id)
    """)

    with engine.connect() as conn:
        exists = conn.execute(q_exists, user_data).scalar()

    return exists


def insert_user_data(user_data: dict):
    exists = check_if_exists(user_data)
    if not exists:
        q_insert = sa.text("""
            INSERT INTO accounts 
            (name, surname, email, password, personal_id, birth_date, domain_id, country_id, address_id)
            VALUES(
                :name, :surname, :email, :password, :personal_id, :birth_date, 
                :domain_id, :country_id, :address_id
            )
        """)

        with engine.connect() as conn:
            # print(user_data)
            prompt = input('continue? (y/n)\n')
            if not prompt:
                return 0
            last_id = conn.execute(q_insert, user_data).lastrowid
            if last_id:
                upd_id = conn.execute(
                    sa.text(f'UPDATE countries_data SET used_by_acc = {last_id} WHERE id = {user_data["address_id"]}')
                ).rowcount
                # print_and_log(logger, f'UPDATE countries_data res {upd_id}')

        return last_id
    else:
        # print_and_log(logger, f'account already exists: {user_data}')
        return 0


def update_user_data(user_data: PersonalData):
    with engine.connect() as conn:
        user_data_in_db = conn.execute(sa.text(f"""
            SELECT * FROM accounts WHERE email = :email
        """), user_data.account['email']).fetchone()
    if user_data_in_db is not None:
        # updating user
        pass
    else:
        # new user
        pass
    return


def main():
    # res = generate_personal_id('marc.perez@andorra.chronisto.com', 'cyprus')  # TODO: for test, remove
    # print(res)
    # return
    # TODO: --update-accounts add --key option for updating specific keys
    usage = """
    python -m maintenance.generate_personal_data --insert-accounts --file data/personal_data.csv
    python -m maintenance.generate_personal_data --update-accounts
    """
    parser = OptionParser(usage=usage)

    parser.add_option(
        '--insert-accounts', action='store_true', dest='insert_accounts', default=False,
        help='Generate and insert accounts data based on email and country values')
    parser.add_option(
        '--update-accounts', action='store_true', dest='update_accounts', default=False,
        help='Generate and update existing accounts data based on email and country values')
    parser.add_option('--file', action='store', dest='file', default=False,
                      help='File path for process')

    (options, args) = parser.parse_args()
    print(options)
    if not options.file:
        print('--file option required')
        return False
    else:
        accounts = pd.read_csv(options.file, sep=';')
        print(len(accounts))
    if options.insert_accounts:
        i = 0
        for indx, account in accounts.iterrows():
            print_and_log(logger, f'country: {account[0]} name: {account[1]}')
            try:
                acc = PersonalData(account[1], 'chronisto.com', account[0])
                print_and_log(logger, f'PersonalData: {acc}')
                exist_on_host = check_subdomain_on_host(acc.account['email'])
                print_and_log(logger, f'{acc.account["email"]} exists: {exist_on_host}')
                if exist_on_host['result']:
                    print_and_log(logger, f'Account for {account[0]} {account[1]} will be added')
                    res = insert_user_data(acc.account)
                    print_and_log(logger, f'Result: {res}')
                else:
                    print_and_log(logger, f'Error: {exist_on_host}')
                    if exist_on_host['messages']['error'][0].startswith('Too Many Requests'):
                        return
            except Exception as e:
                print_and_log(logger, f'ERROR: add personal data failed {account[0]}\n {e}')
                continue
            # print(acc.account)
            i += 1
        print_and_log(logger, f'Added {i} from {len(accounts)} accounts')

    # mailboxes = get_mailboxes_list()
    # if options.insert_accounts:
    #     tmp = 0
    #     if mailboxes['result']:
    #         for domain, mailboxes in mailboxes['response']['list'].items():
    #             for mailbox in mailboxes:
    #                 email = mailbox['email_auto']
    #                 if email.startswith('info'):
    #                     continue
    #                 print(email)
    #                 user_data = generate_user_data(email)
    #                 print(user_data)
    #                 if not user_data:
    #                     print('empty user_data')
    #                     continue
    #                 ins_res = insert_user_data(user_data)
    #
    #                 print(f'insert_user_data: {ins_res}')
    #                 tmp += 1
    #                 if tmp > 11:
    #                     return
    # elif options.update_accounts:
    #     tmp = 0
    #     if mailboxes['result']:
    #         for domain, mailboxes in mailboxes['response']['list'].items():
    #             for mailbox in mailboxes:
    #                 # TODO: in future do not use country from domain
    #                 email = mailbox['email_auto']
    #                 if email.startswith('info'):
    #                     continue
    #                 country = domain.replace(f'.{conf.MAIN_DOMAIN}', '')
    #                 # personal_id = generate_personal_id(email, country)
    #                 # if personal_id:
    #                 #     data = {'personal_id': personal_id}
    #                 #     upd_res = update_user_data(email, data)
    #                 #     print(data)
    #                 #     print(f'Updating personal data for {email}: {upd_res}')
    #                 user_data = PersonalData(email, country).account
    #                 del user_data['country']  # TODO: remove from account property in class
    #                 upd_res = update_user_data(email, user_data)
    #                 print(user_data)
    #                 print(f'Updating personal data for {email}: {upd_res}')
    #                 tmp += 1
    #                 if tmp > 11:
    #                     return
    # else:
    #     parser.print_help()
    pass


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print(f'ERROR {err}')
        raise

    print('OK')
