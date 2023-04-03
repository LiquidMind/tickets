import sqlalchemy as sa
import pandas as pd
import googlemaps
import time

import conf


engine = sa.create_engine(conf.MYSQL_CONNECTION_STRING, isolation_level="AUTOCOMMIT")
gmaps = googlemaps.Client(key=conf.GOOGLE_API_KEY)

countries_list = pd.read_csv('data/country-capital.csv', index_col='Country')
countries_list.rename(index=lambda Index: Index.replace(' ', '-').lower(), inplace=True)


def get_country_id_by_name(country):
    with engine.connect() as conn:
        country_id = conn.execute(sa.text(f"""SELECT id FROM countries WHERE tag="{country}" """)).scalar()
    return country_id


def is_english(s):
    return s.isascii()


def load_country_addresses(obj_type: list):

    for country in countries_list.index:
        country_id = get_country_id_by_name(country.replace(' ', '-').lower())
        if not country_id:
            print('Can not find country')
            continue
        if country in countries_list.index:
            lat = countries_list['Latitude'][country]
            lng = countries_list['Longitude'][country]

            data = {
                'query': '',
                'location': {
                    'lat': lat,
                    'lng': lng
                },
                'radius': 10000,
                'language': "EN",
                'type': obj_type
            }
            places = gmaps.places(**data)

            data_place = {}
            for place in places['results']:
                if 'formatted_address' in place and 'place_id' in place:
                    if not is_english(place['formatted_address']):
                        continue
                    data1 = {
                        "place_id": place['place_id'],
                        "fields": ["international_phone_number"],
                        "language": "EN"
                    }
                    geocode_place = gmaps.place(**data1)
                    # print(geocode_place)
                    if 'international_phone_number' in geocode_place['result']:
                        data_place['address'] = place['formatted_address']
                        data_place['phone'] = geocode_place['result']['international_phone_number']
                        data_place['country_id'] = country_id
                        data_place['used_by_acc'] = None
                        print(data_place)
                        with engine.connect() as conn:
                            exists = conn.execute(
                                sa.text("""
                                    SELECT COUNT(id) FROM countries_data 
                                    WHERE address = :address OR phone = :phone
                                """),
                                data_place
                            ).scalar()
                            if exists:
                                print(f'SKIPPED address {data_place["address"]}: {exists}')
                                continue
                            last_id = conn.execute(
                                sa.text("""
                                    INSERT INTO countries_data (address, phone, country_id, used_by_acc)
                                    VALUES (:address, :phone, :country_id, :used_by_acc)
                                """),
                                data_place
                            )
                            print(f'INSERTED address {data_place["address"]}: {last_id}')
                            time.sleep(1)
        print(f'FINISHED for {country}')


def main():
    load_country_addresses(obj_type=['bar', 'cafe', 'hotel'])


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print(f'ERROR {err}')
        raise

    print('OK')