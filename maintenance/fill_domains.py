import sqlalchemy as sa

from api import get_mailboxes_list

import conf


engine = sa.create_engine(conf.MYSQL_CONNECTION_STRING, isolation_level="AUTOCOMMIT")


def main():
    mailboxes = get_mailboxes_list()
    if mailboxes['result']:
        # TODO: function for getting host_id by name
        f_q_upsert_domain = """
            INSERT INTO domains (`name`, `host_id`) VALUES ('{domain}', 1) 
            ON DUPLICATE KEY UPDATE `name` = '{domain}'
        """
        with engine.connect() as conn:
            for domain in mailboxes['response']['list'].keys():
                print(f'Inserting domain {domain}')
                res = conn.execute(sa.text(f_q_upsert_domain.format(domain=domain)))
                print(res.lastrowid)
    else:
        print(mailboxes['messages'])


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print(f'ERROR {err}')
        raise

    print('OK')
