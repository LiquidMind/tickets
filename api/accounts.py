import logging
import sqlalchemy as sa

from common.functions import print_and_log

import conf

engine = sa.create_engine(conf.MYSQL_CONNECTION_STRING, isolation_level="AUTOCOMMIT")


def get_free_accounts(clause='', limit=1):
    # TODO: remove "after_1000"
    with engine.connect() as conn:
        account = conn.execute(sa.text(f"""
             SELECT 
                 a.id, a.name, a.surname, a.email, a.birth_date, a.personal_id, c.name as location, cd.address, 
                 cd.phone, a.prime, a.password, c.capital
             FROM 
                 accounts a 
                 LEFT JOIN countries c ON a.country_id = c.id
                 LEFT JOIN countries_data cd ON a.address_id = cd.id
             WHERE
                 a.email_verified = 1 
                 AND a.used = 0 
                 AND a.prime IS NULL
                 {clause}
             LIMIT {limit}
         """)).fetchall()
    return account


def update_account(account_email: str, params: dict):
    if not len(params):
        return False

    set_values = [f'{key} = :{key}' for key in params.keys()]
    params['email'] = account_email
    with engine.connect() as conn:
        upd_res = conn.execute(sa.text(f"""
            UPDATE accounts SET {', '.join(set_values)} WHERE email = :email
        """), params).rowcount
        return upd_res
