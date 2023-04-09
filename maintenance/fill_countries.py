import sqlalchemy as sa
from sqlalchemy.dialects.mysql import insert
import pandas as pd
from anyascii import anyascii
from optparse import OptionParser

import conf


engine = sa.create_engine(conf.MYSQL_CONNECTION_STRING, isolation_level="AUTOCOMMIT")


def update_on_duplicate(table, conn, keys, data_iter):
    insert_stmt = insert(table.table).values(list(data_iter))
    on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(insert_stmt.inserted)
    conn.execute(on_duplicate_key_stmt)


def get_countries_from_file(file_path, separator=':'):
    countries = []
    with open(file_path) as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith('#') or not len(line.strip()):
                continue
            tmp = line.split(':')
            countries.append(tmp[0].strip())

    return countries


def load_locations_from_file(filepath, prime=''):
    locations = pd.read_csv(filepath, usecols=['name', 'lat', 'lng', 'capital'])
    locations.drop_duplicates(subset=['name'], inplace=True)
    locations['name'] = locations['name'].apply(lambda val: anyascii(val))
    locations['capital'] = locations['capital'].apply(lambda val: anyascii(val))
    locations['tag'] = locations['name'].str.lower().replace(' ', '-')
    locations['prime'] = prime
    return locations


def main():
    # OLD VERSION FOR TXT FILE
    # f_q_upsert = """
    #     INSERT INTO countries (`name`) VALUES ('{country}')
    #     ON DUPLICATE KEY UPDATE `name` = '{country}'
    # """
    # with engine.connect() as conn:
    #     for country in get_countries_from_file('data/countries.txt'):
    #         print(f_q_upsert.format(country=country))
    #         res = conn.execute(sa.text(f_q_upsert.format(country=country)))
    #         print(f'add {country} to the database\n {res.lastrowid}')
    #     conn.execute(sa.text('COMMIT'))

    # NEW VERSION FOR CSV FILE
    usage = """
    python -m maintenance.fill_countries --insert --file data/countries.csv
    """

    parser = OptionParser(usage=usage)

    parser.add_option('--insert', action='store_true', dest='insert', default=False,
                      help='Add locations from file, requires --file option')
    parser.add_option('--update', action='store_true', dest='update', default=False,
                      help='Add locations from file, requires --file option')
    parser.add_option('--file', action='store', dest='file', default=False,
                      help='File path for process')
    parser.add_option('--prime', action='store', dest='prime', default='',
                      help='Prime for locations (is_city for cities, empty for countries)')

    (options, args) = parser.parse_args()

    if not options.file:
        print('--file option required')
        return False
    locations = load_locations_from_file(options.file, prime=options.prime)
    if options.insert:
        with engine.connect() as conn:
            res = locations.to_sql('countries', con=conn, if_exists='append', index=False)
            print(f'Added locations to the database\n {res}')
    elif options.update:
        with engine.connect() as conn:
            for i, location in locations.iteritems():
                print(f'{location.name} {location.capital}')
            # conn.execute()
    else:
        parser.print_help()


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print(f'ERROR {err}')
        raise

    print('FINISHED')
