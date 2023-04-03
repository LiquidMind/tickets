import sqlalchemy as sa

import conf


engine = sa.create_engine(conf.MYSQL_CONNECTION_STRING, isolation_level="AUTOCOMMIT")


def get_countries_from_file(file_path):
    countries = []
    with open(file_path) as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith('#') or not len(line.strip()):
                continue
            tmp = line.split(':')
            countries.append(tmp[0].strip())

    return countries


def main():
    f_q_upsert = """
        INSERT INTO countries (`name`) VALUES ('{country}') 
        ON DUPLICATE KEY UPDATE `name` = '{country}'
    """
    with engine.connect() as conn:
        for country in get_countries_from_file('data/countries.txt'):
            print(f_q_upsert.format(country=country))
            res = conn.execute(sa.text(f_q_upsert.format(country=country)))
            print(f'add {country} to the database\n {res.lastrowid}')
        conn.execute(sa.text('COMMIT'))


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print(f'ERROR {err}')
        raise

    print('OK')
