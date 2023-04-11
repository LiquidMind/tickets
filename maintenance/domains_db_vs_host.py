import sqlalchemy as sa
import pandas as pd

from api import get_subdomains_list

import conf

engine = sa.create_engine(conf.MYSQL_CONNECTION_STRING, isolation_level="AUTOCOMMIT")


def main():
    host_domains_res = get_subdomains_list()
    locations_host = [h.replace(f'.{conf.MAIN_DOMAIN}', '') for h in host_domains_res['response']['list'].keys()]
    with open('data/locations_host.txt', 'w+') as f:
        for location in locations_host:
            f.write(location+'\n')

    totals = {}
    with engine.connect() as conn:
        locations_db_res = conn.execute(sa.text("""
            SELECT id, capital, tag FROM countries
        """)).fetchall()
        locations_db = [h for h in locations_db_res]
        totals = {'':0, 'Germany': 0, 'Spain': 0, 'Italy': 0, 'Portugal': 0, 'United Kingdom': 0, 'Turkey': 0}
        with open('data/locations_db.txt', 'w+') as f:
            for db_location in locations_db:
                # print(db_location[2])

                if db_location[2] in locations_host:
                    # print(db_location[2])
                    addresses = conn.execute(
                        sa.text("SELECT COUNT(id) FROM countries_data WHERE country_id = :country_id"),
                        {'country_id': db_location[0]}
                    ).scalar()
                    totals[db_location[1]] += addresses
                    # print(totals[db_location[1]])
                    f.write(f'{db_location[1]};{db_location[2]};{addresses}\n')
            f.write(f'Total: {totals}')
        print(totals)
    pass


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print(f'ERROR {err}')
        raise

    print('OK')
