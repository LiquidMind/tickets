"""
docs: https://documenter.getpostman.com/view/1801428/UVC6i6eA#47754ded-22d0-4974-a4a5-7bfbf0edcb2f
"""
import sqlalchemy as sa
import requests
import json
import random
import re
import plyvel
import time
from datetime import timedelta
import httpx
import glob
import os

from maintenance import PersonalData

import conf


engine = sa.create_engine(conf.MYSQL_CONNECTION_STRING, isolation_level="AUTOCOMMIT")
OCTO_ID = '2f781dc1de5549ed81a5f16aea642d0c'
# EXT_IDS = ['gcalenpjmijncebpfijmoaglllgpjagf', 'donenhhpaddpdppgajabfhcdbkpdngcj']
EXT_IDS = ['gcalenpjmijncebpfijmoaglllgpjagf']
OCTO_PROFILE_FOLDER = '8f443247d0c644329aa1c356b865c058'


def get_proxy_host(file_path):
    ip_list = []

    with engine.connect() as conn:
        used_ips = [a.registration_ip
                    for a in conn.execute(sa.text("""SELECT registration_ip FROM accounts WHERE used = 1""")).fetchall()
                    ]

    with open(file_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", line):
                if line.strip() not in used_ips:
                    ip_list.append(line)

    return random.choice(ip_list)


def get_profiles(title=False):
    payload = {}
    headers = {
        'X-Octo-Api-Token': conf.OCTO_API_TOKEN
    }
    if not title:
        # response = requests.request("GET", conf.OCTO_API_URL + f'?search={title}', headers=headers, data=payload)
        response = requests.request("GET", conf.OCTO_API_URL+'?page_len=100&page=0', headers=headers, data=payload)
    else:
        response = requests.request("GET", conf.OCTO_API_URL+f'?search={title}', headers=headers, data=payload)

    return response.json()


def get_profile(uuid):
    url = f"https://app.octobrowser.net/api/v2/automation/profiles/{uuid}"

    payload = {}
    headers = {
        'X-Octo-Api-Token': f'{conf.OCTO_API_TOKEN}'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    # print(response.text)
    return response.json()


def get_extensions():
    url = "https://app.octobrowser.net/api/v2/automation/teams/extensions?start=0&limit=25"

    payload = {}
    headers = {
        'X-Octo-Api-Token': f'{conf.OCTO_API_TOKEN}'
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)


def get_extension(uuid):
    url = f"https://app.octobrowser.net/api/v2/automation/teams/extension/{uuid}"

    payload = {}
    headers = {
        'X-Octo-Api-Token': f'{conf.OCTO_API_TOKEN}'
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)


def start_profile(uuid):
    payload = json.dumps({
        "uuid": uuid,
        "headless": True,
        "debug_port": True,
        "flags": [
            "--remote-debugging-address=0.0.0.0"
        ]
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", f'{conf.OCTO_LOCAL_API_URL}/start', headers=headers, data=payload)
    return response.json()


def stop_profile(uuid):
    payload = json.dumps({
        "uuid": uuid
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", f'{conf.OCTO_LOCAL_API_URL}/stop', headers=headers, data=payload)
    return response.json()


def add_profile(account):
    # TODO: exclude already used ip's (store in accounts table)
    proxy_ip = get_proxy_host('data/euip.txt').strip()
    payload = json.dumps({
        "title": f"{account.email}",
        "description": "",
        "start_pages": ["https://www.uefa.com"],
        # "languages": {
        #     "type": "manual",
        #     "data": [
        #         "[ru-RU] Russian (Russia)",
        #         "[en-US] English (United States)"
        #     ]
        # },
        "proxy": {
            "type": "https",
            "host": f"{proxy_ip}",
            "port": 7951,
            "login": conf.PROXY_LOGIN,
            "password": conf.PROXY_PASS
        },
        "storage_options": {
            "cookies": True,
            "passwords": True,
            "extensions": True,
            "localstorage": True,
            "history": False,
            "bookmarks": False
        },
        "fingerprint": {
            "os": "win",
            "languages": {
                "type": "ip"
            },
            "timezone": {
                "type": "ip"
            },
            "geolocation": {
                "type": "ip"
            },
            "cpu": 4,
            "ram": 8,
            "noise": {
                "webgl": True,
                "canvas": True,
                "audio": True,
                "client_rects": False
            },
            "webrtc": {
                "type": "ip"
            },
            "media_devices": {
                "video_in": 1,
                "audio_in": 1,
                "audio_out": 1
            }
        },
        "extensions": [
            "gcalenpjmijncebpfijmoaglllgpjagf@4.19.6181",
            "donenhhpaddpdppgajabfhcdbkpdngcj@0.63"
        ]
    })

    headers = {
        'Content-Type': 'application/json',
        'X-Octo-Api-Token': f'{conf.OCTO_API_TOKEN}'
    }

    response = requests.request("POST", conf.OCTO_API_URL, headers=headers, data=payload)
    res = response.json()
    # print(res)
    if res['success']:
        # TODO: import Tampermonkey script
        res['used_proxy_ip'] = proxy_ip
        try:
            start_response = start_profile(res['data']['uuid'])
            print(f'Start response: {start_response}')
            db_from = plyvel.DB('/home/andrey/.Octo Browser/tmp/ExtensionSettings/gcalenpjmijncebpfijmoaglllgpjagf')
            # goto /home/andrey/.Octo Browser/{basic_profile_id}/profiles and find file with name starts with
            # {"uuid":"8f443247d0c644329aa1c356b865c058"} from res["uuid"], remove LOCK file

            files = glob.glob(
                f'/home/andrey/.Octo Browser/2f781dc1de5549ed81a5f16aea642d0c/profiles/{start_response["uuid"]}*'
            )
            print(f'Files: {files}')
            with open(files[0], 'r') as f:
                path = f.read()
                db_to = {}
                db_keys = {
                    'gcalenpjmijncebpfijmoaglllgpjagf': [
                        b'@meta#55cb1c2a-beb6-493c-b099-718d4e8395b0',
                        b'@re#55cb1c2a-beb6-493c-b099-718d4e8395b0',
                        b'@source#55cb1c2a-beb6-493c-b099-718d4e8395b0',
                        b'@st#55cb1c2a-beb6-493c-b099-718d4e8395b0',
                        b'@uid#55cb1c2a-beb6-493c-b099-718d4e8395b0'
                    ],
                    'ckjmdkfabiikokiacihmnlolfnedipjh': [
                        b'libs',
                        b'settings',
                        b'sites'
                    ]
                }
                for ext_id in EXT_IDS:
                    print(f'{path}/Default/Local Extension Settings/{ext_id}')
                    print(os.path.exists(f"{path}/Default/Local Extension Settings/{ext_id}"))
                    i = 0
                    while not os.path.exists(f'{path}/Default/Local Extension Settings/{ext_id}') and i < 10:
                        print(f'Waiting for {path}/Default/Local Extension Settings/{ext_id}/LOCK')
                        i += 1
                        time.sleep(1)
                    if os.path.exists(f'{path}/Default/Local Extension Settings/{ext_id}'):
                        os.remove(f'{path}/Default/Local Extension Settings/{ext_id}/LOCK')
                        print('LOCK REMOVED')
                        db_to[ext_id] = plyvel.DB(f'{path}/Default/Local Extension Settings/{ext_id}/')
                        print('DB_TO connected')

                        for db_key in db_keys[ext_id]:
                            db_to[ext_id].put(db_key, db_from.get(db_key))
                        db_to[ext_id].close()

                    else:
                        print(f'{path}/Default/Local Extension Settings/{ext_id} NOT EXISTS')
                        stop_response = stop_profile(start_response['uuid'])
                        print(f'STOP Profile {stop_response}')
                        delete_profiles([start_response['uuid']])
                        print('DELETED profile')
                        raise FileNotFoundError
            db_from.close()
            stop_response = stop_profile(start_response['uuid'])
            print(f'STOP Profile {stop_response}')
        except Exception as e:
            print(f'Exception: {e}')
            raise e

    return res


def update_profile(uuid, account):
    proxy_ip = get_proxy_host('data/euip.txt').strip()
    payload = json.dumps({
        # "title": f"{account.email}",
        # "description": "",
        # "start_pages": ["https://www.uefa.com/"],
        # "languages": {
        #     "type": "manual",
        #     "data": [
        #         "[ru-RU] Russian (Russia)",
        #         "[en-US] English (United States)"
        #     ]
        # },
        "proxy": {
            "type": "https",
            "host": f"{proxy_ip}",
            # "host": '137.74.53.201',
            "port": 7951,
            "login": conf.PROXY_LOGIN,
            "password": conf.PROXY_PASS
        },
        "storage_options": {
            "cookies": True,
            "passwords": True,
            "extensions": True,
            "localstorage": True,
            "history": False,
            "bookmarks": False
        },
        "fingerprint": {
            "os": random.choice(['win', 'linux', 'mac']),
            "languages": {
                "type": "ip"
            },
            "timezone": {
                "type": "ip"
            },
            "geolocation": {
                "type": "ip"
            },
            "cpu": random.choice([2, 4, 8]),
            "ram": random.choice([4, 8, 16]),
            "noise": {
                "webgl": True,
                "canvas": True,
                "audio": True,
                "client_rects": False
            },
            "webrtc": {
                "type": "ip"
            },
            "media_devices": {
                "video_in": random.choice([0, 1]),
                "audio_in": random.choice([0, 1]),
                "audio_out": random.choice([0, 1])
            }
        }
    })

    headers = {
        'Content-Type': 'application/json',
        'X-Octo-Api-Token': f'{conf.OCTO_API_TOKEN}'
    }

    response = requests.request("POST", f'{conf.OCTO_API_URL}/{uuid}', headers=headers, data=payload)
    res = response.json()
    # print(res)
    if res['success']:
        res['used_proxy_ip'] = proxy_ip
    return res


def delete_profiles(ids):
    payload = json.dumps({
        "uuids": ids,
        "skip_trash_bin": True
    })
    headers = {
        'Content-Type': 'application/json',
        'X-Octo-Api-Token': conf.OCTO_API_TOKEN
    }

    response = requests.request("DELETE", conf.OCTO_API_URL, headers=headers, data=payload)

    print(response.text)
