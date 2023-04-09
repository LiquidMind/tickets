import pandas as pd

import faker
from anyascii import anyascii


def main():
    countries = {'tr': 'tr_TR', 'de': 'de_DE', 'es': 'es_ES', 'gb': 'en_GB', 'it': 'it_IT', 'pt': 'pt_PT'}
    countries = {'pt': 'pt_PT'}
    try:
        for country, iso_code in countries.items():
            fake = faker.Faker(iso_code)
            fake.unique.clear()
            cities = pd.read_csv(f'data/{country}.csv')
            # if country == 'tr':
            #     max_rows = 500
            # else:
            #     max_rows = 100  # tr, pt not working UniquenessException: Got duplicated values after 1,000 iterations
            # names = [
            #     f'{anyascii(c)};{anyascii(fake.unique.first_name())} {anyascii(fake.unique.last_name())}\n'
            #     for c in cities.loc[:max_rows, 'city']
            # ]
            names = [
                # f'{anyascii(c)};{anyascii(fake.unique.first_name())} {anyascii(fake.unique.last_name())}\n'
                f'{anyascii(c)};{anyascii(fake.first_name())} {anyascii(fake.last_name())}\n'
                for c in cities['name']
            ]
            with open(f'data/{country}_personal_data_full.csv', 'w+') as f:
                f.writelines(names)
    except Exception as e:
        print(f'Exception: {e}')
    pass


if __name__ == '__main__':
    main()
