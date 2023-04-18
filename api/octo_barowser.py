"""
docs: https://documenter.getpostman.com/view/1801428/UVC6i6eA#47754ded-22d0-4974-a4a5-7bfbf0edcb2f
"""
import sqlalchemy as sa
import requests
import json
import random
import re
import time
from datetime import timedelta

from maintenance import PersonalData

import conf


engine = sa.create_engine(conf.MYSQL_CONNECTION_STRING, isolation_level="AUTOCOMMIT")


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


def add_profile(account):
    # TODO: exclude already used ip's (store in accounts table)
    proxy_ip = get_proxy_host('data/euip.txt').strip()
    payload = json.dumps({
        "title": f"{account.email}",
        "description": "",
        "start_pages": ["https://www.uefa.com/"],
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
        "cookies": [
            {
                "domain": "https://uefa.com",
                "expirationDate": time.time() + timedelta(days=30).seconds,
                "hostOnly": False,
                "httpOnly": False,
                "name": "profile_name",
                "path": "/",
                "sameSite": "no_restriction",
                "secure": False,
                "value": f"{account.name}"
            },
            {
                "domain": ".uefa.com",
                "expirationDate": time.time() + timedelta(days=30).seconds,
                "hostOnly": False,
                "httpOnly": False,
                "name": "profile_surname",
                "path": "/",
                "sameSite": "no_restriction",
                "secure": False,
                "value": f"{account.surname}"
            },
            {
                "domain": ".uefa.com",
                "expirationDate": time.time() + timedelta(days=30).seconds,
                "hostOnly": False,
                "httpOnly": False,
                "name": "profile_email",
                "path": "/",
                "sameSite": "no_restriction",
                "secure": False,
                "value": f"{account.email}"
            },
            {
                "domain": ".uefa.com",
                "expirationDate": time.time() + timedelta(days=30).seconds,
                "hostOnly": False,
                "httpOnly": False,
                "name": "profile_birth_date",
                "path": "/",
                "sameSite": "no_restriction",
                "secure": False,
                "value": f"{account.birth_date}"
            },
            {
                "domain": ".uefa.com",
                "expirationDate": time.time() + timedelta(days=30).seconds,
                "hostOnly": False,
                "httpOnly": False,
                "name": "profile_address",
                "path": "/",
                "sameSite": "no_restriction",
                "secure": False,
                "value": f"{account.address}"
            },
            {
                "domain": ".uefa.com",
                "expirationDate": time.time() + timedelta(days=30).seconds,
                "hostOnly": False,
                "httpOnly": False,
                "name": "profile_phone",
                "path": "/",
                "sameSite": "no_restriction",
                "secure": False,
                "value": f"{account.phone}"
            },
        ],
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
        ]
    })

    headers = {
        'Content-Type': 'application/json',
        'X-Octo-Api-Token': f'{conf.OCTO_API_TOKEN}'
    }

    response = requests.request("POST", conf.OCTO_API_URL, headers=headers, data=payload)
    res = response.json()
    print(res)
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
