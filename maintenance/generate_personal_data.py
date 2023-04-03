import sqlalchemy as sa
import random
import rstr
from optparse import OptionParser

import googlemaps  # https://googlemaps.github.io/google-maps-services-python/docs/index.html
from api import get_mailboxes_list

import conf

engine = sa.create_engine(conf.MYSQL_CONNECTION_STRING, isolation_level="AUTOCOMMIT")
gmaps = googlemaps.Client(key=conf.GOOGLE_API_KEY)


def get_domain_id_by_name(domain_name):
    with engine.connect() as conn:
        domain_id = conn.execute(sa.text(f"SELECT id FROM domains WHERE name='{domain_name}'")).scalar()
    return domain_id


def get_country_id_by_name(country):
    with engine.connect() as conn:
        country_id = conn.execute(sa.text(f""" SELECT id FROM countries WHERE tag="{country}" """)).scalar()
    return country_id


def get_user_data_from_email(email):
    email_parts = email.split('@')
    user_login = email_parts[0]
    user = user_login.split('.')

    if len(user) == 2:
        name = user[0]
        surname = user[1]
    elif len(user) > 2:
        name = user[0]
        surname = user[-1:][0]
    else:
        print('Can not generate user data')
        return False

    return {'name': name.capitalize(), 'surname': surname.capitalize()}


def generate_phone_number(country):
    return ''


def generate_address_with_phone(country):
    country_id = get_country_id_by_name(country)
    if not country_id:
        return False
    q_get_data = """
        SELECT id, address, phone FROM countries_data
        WHERE used_by_acc IS NULL AND country_id = :country_id
        LIMIT 1 
    """
    with engine.connect() as conn:
        res = conn.execute(sa.text(q_get_data), {'country_id': country_id}).fetchone()
        if res is not None:
            return {'address_id': res[0], 'address': res[1], 'phone': res[2]}
    return False


def generate_personal_id(email, country):
    if country in conf.COUNTRIES_PERSONAL_ID_TEMPLATES and 'reg_ex' in conf.COUNTRIES_PERSONAL_ID_TEMPLATES[country]:
        country_rules = conf.COUNTRIES_PERSONAL_ID_TEMPLATES[country]
        personal_id = rstr.xeger(country_rules['reg_ex'])
        if 'rules' in country_rules and 'field' in country_rules['rules'] and 'type' in country_rules['rules']:
            field = country_rules['rules']['field']
            with engine.connect() as conn:
                account_field = conn.execute(
                    sa.text(f"SELECT {field} FROM accounts WHERE email = :email"),
                    {'email': email}
                ).scalar()
                print('Account:')
                print(account_field)
                if account_field is None:
                    return False
                if country_rules['rules']['type'] == 'date':
                    fdata = {f'{field}': account_field.strftime(country_rules['rules']['format'])}
                    personal_id = personal_id.format(**fdata)
                elif country_rules['rules']['type'] == 'value':
                    fdata = {f'{field}': account_field}
                    personal_id = personal_id.format(**fdata)
    else:
        return False
    # TODO: check if personal_id not exists
    return personal_id


def generate_password(user_name):
    return f'Pwd4{user_name}'


def generate_birth_date():
    year = random.randrange(1970, 2000)
    month = random.randrange(1, 12)
    if month < 10:
        month = f'0{month}'
    day = random.randrange(1, 28)
    if day < 10:
        day = f'{0}{day}'
    return f'{year}-{month}-{day}'


def generate_user_data(email, country=False):
    # TODO: do not use email to determine the country
    tmp = email.split('@')
    domain = tmp[1]
    if not country:
        country = domain.replace(f'.{conf.MAIN_DOMAIN}', '')
    user_data = get_user_data_from_email(email)
    if not user_data:
        print('Error while get user data')
        return False
    addr_phone = generate_address_with_phone(country)
    if not addr_phone:
        print('Can not find address')
        return False
    user_data['email'] = email
    user_data['birth_date'] = generate_birth_date()
    user_data['country_id'] = get_country_id_by_name(country)
    user_data['domain_id'] = get_domain_id_by_name(domain)
    user_data['password'] = generate_password(user_data['name'])
    user_data['address_id'] = addr_phone['address_id']
    user_data['personal_id'] = generate_personal_id(country)
    user_data['prime'] = ''

    return user_data


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


def insert_user_data(user_data):
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
            print(user_data)
            prompt = input('continue? (y/n)\n')
            if not prompt:
                return 0
            last_id = conn.execute(q_insert, user_data).lastrowid
            if last_id:
                upd_id = conn.execute(
                    sa.text(f'UPDATE countries_data SET used_by_acc = {last_id} WHERE id = {user_data["address_id"]}')
                ).rowcount
                print(f'UPDATE countries_data res {upd_id}')

        return last_id
    else:
        print('account already exists')
        return 0


def update_user_data(email, data):
    if not len(data):
        print('data can not be empty')
        return False

    acc_where_clause = 'WHERE email = :email'
    id_where_clause = 'WHERE TRUE'
    set_str = ''

    for key in data:
        set_str += f'{key} = :{key}, '
        id_where_clause += f' AND {key} = :{key}'

    with engine.connect() as conn:
        acc_exists = conn.execute(sa.text(f"SELECT COUNT(id) FROM accounts {acc_where_clause}"), {'email': email}).scalar()
        if not acc_exists:
            # TODO: add account?
            return False
        id_exists = conn.execute(
            sa.text(f"SELECT COUNT(id) FROM accounts {id_where_clause}"),
            data
        ).scalar()
        if id_exists is not None:
            # TODO: regenerate ID
            return False

    with engine.connect() as conn:
        upd_res = conn.execute(sa.text(f"UPDATE accounts SET {set_str[:-2]} {acc_where_clause}"), {'email': email}).rowcount
        print(f'UPDATING account data: {upd_res}')
        print(f"UPDATE accounts SET {set_str[:-2]} {acc_where_clause}")
        return upd_res


def main():
    # res = generate_personal_id('marc.perez@andorra.chronisto.com', 'cyprus')  # TODO: for test, remove
    # print(res)
    # return
    # TODO: --update-accounts add --key option for updating specific keys
    usage = """
    python -m maintenance.generate_personal_data --insert-accounts
    python -m maintenance.generate_personal_data --update-accounts
    """
    parser = OptionParser(usage=usage)

    parser.add_option(
        '--insert-accounts', action='store_true', dest='insert_accounts', default=False,
        help='Generate and insert accounts data based on email and country values')
    parser.add_option(
        '--update-accounts', action='store_true', dest='update_accounts', default=False,
        help='Generate and update existing accounts data based on email and country values')

    (options, args) = parser.parse_args()
    print(options)
    mailboxes = get_mailboxes_list()
    if options.insert_accounts:
        tmp = 0
        if mailboxes['result']:
            for domain, mailboxes in mailboxes['response']['list'].items():
                for mailbox in mailboxes:
                    email = mailbox['email_auto']
                    if email.startswith('info'):
                        continue
                    print(email)
                    user_data = generate_user_data(email)
                    print(user_data)
                    if not user_data:
                        print('empty user_data')
                        continue
                    ins_res = insert_user_data(user_data)

                    print(f'insert_user_data: {ins_res}')
                    tmp += 1
                    if tmp > 11:
                        return
    elif options.update_accounts:
        if mailboxes['result']:
            for domain, mailboxes in mailboxes['response']['list'].items():
                for mailbox in mailboxes:
                    # TODO: in future do not use country from domain
                    email = mailbox['email_auto']
                    country = domain.replace(f'.{conf.MAIN_DOMAIN}', '')
                    personal_id = generate_personal_id(email, country)
                    if personal_id:
                        data = {'personal_id': personal_id}
                        upd_res = update_user_data(email, data)
                        print(f'Updating personal data: {upd_res}')
    else:
        parser.print_help()
    pass


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print(f'ERROR {err}')
        raise

    print('OK')
