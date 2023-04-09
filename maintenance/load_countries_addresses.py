import sqlalchemy as sa
import pandas as pd
import googlemaps
import time
import anyascii

from api import get_subdomains_list
import conf


engine = sa.create_engine(conf.MYSQL_CONNECTION_STRING, isolation_level="AUTOCOMMIT")
gmaps = googlemaps.Client(key=conf.GOOGLE_API_KEY)

countries_list = pd.read_csv('data/country-capital.csv', index_col='name')
countries_list.rename(index=lambda Index: Index.replace(' ', '-').lower(), inplace=True)


def get_country_id_by_name(country):
    with engine.connect() as conn:
        country_id = conn.execute(sa.text(f"""SELECT id FROM countries WHERE tag="{country}" """)).scalar()
    return country_id


def is_english(s):
    return s.isascii()


def load_cities_addresses(obj_types):
    with engine.connect() as conn:
        mail_subdomains_res = get_subdomains_list()
        mail_subdomains = [
            "'" + k.replace(f'.{conf.MAIN_DOMAIN}', '') + "'"
            for k in mail_subdomains_res['response']['list'].keys()
        ]
        cities = conn.execute(
            sa.text(
                f"""
                    SELECT c.id, c.name, c.tag, c.lat, c.lng
                    -- ,count(cd.id) as addr_cnt
                    FROM countries c 
                    -- LEFT JOIN countries_data cd
                    -- ON c.id = cd.country_id
                    WHERE c.capital = 'Turkey'
                    -- WHERE c.tag IN({','.join(mail_subdomains)}) AND c.prime = 'is_city'
                    -- GROUP BY c.id
                    -- HAVING addr_cnt = 0
                """
            )
        ).fetchall()
        for city in cities:
            data = {
                'query': '',
                'location': {
                    'lat': city.lat,
                    'lng': city.lng
                },
                'radius': 15000,
                'language': "EN",
                'type': obj_types
            }
            places = gmaps.places(**data)

            data_place = {}
            i = 0
            for place in places['results']:
                if 'formatted_address' in place and 'place_id' in place:
                    if not is_english(place['formatted_address']):
                        place['formatted_address'] = anyascii.anyascii(place['formatted_address'])
                    data1 = {
                        "place_id": place['place_id'],
                        "fields": ["international_phone_number"],
                        "language": "EN"
                    }
                    geocode_place = gmaps.place(**data1)
                    print(geocode_place)

                    if 'international_phone_number' in geocode_place['result']:
                        data_place['address'] = place['formatted_address']
                        data_place['phone'] = geocode_place['result']['international_phone_number']
                        data_place['country_id'] = city.id
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
                            ).lastrowid
                            print(f'INSERTED address {data_place["address"]}: {last_id}')
                            i += 1
                            if i >= 10:
                                break
                            time.sleep(1)
            # return


def load_country_addresses(obj_type: list):

    for country in countries_list.index:
        country_id = get_country_id_by_name(country.replace(' ', '-').lower())
        if not country_id:
            print('Can not find country')
            continue
        # TODO: get location coordinates from GoogleAPI, not from file
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
    # load_country_addresses(obj_type=['bar', 'cafe', 'restaurant', 'supermarket'])
    # obj_types: https://developers.google.com/maps/documentation/places/web-service/supported_types?hl=ru
    load_cities_addresses(
        obj_types=[
            'real_estate_agency', 'shoe_store', 'shopping_mall', 'taxi_stand', 'tourist_attraction',
            'train_station', 'transit_station', 'travel_agency', 'university', 'jewelry_store', 'insurance_agency',
            'home_goods_store', 'bar', 'cafe', 'supermarket', 'restaurant'
        ]
    )


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print(f'ERROR {err}')
        raise

    print('OK')
