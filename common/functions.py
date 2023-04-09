import urllib3
import json

import conf


def print_and_log(logger, msg, ask=False):
    logger.info(msg)
    if ask:
        answ = input(msg)
    else:
        print(msg)
    if ask and answ != 'y':
        print(f'ABORTED {ask} {answ}')
        logger.warning('ABORTED')
        return False
    return True


def send_post_request(url, data):
    http = urllib3.PoolManager()
    encoded_data = json.dumps(data).encode('utf-8')
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {conf.TOKEN}",
    }
    response = http.request('POST', url, headers=headers, body=encoded_data)
    resp_dict = json.loads(response.data.decode('utf-8'))
    resp_dict['status'] = response.status
    return resp_dict


def process_data(file_path, separator=':'):
    data = []
    with open(file_path) as f:
        lines = f.readlines()
    for line in lines:
        if line.startswith('#stop'):
            return data
        if line.startswith('#') or not len(line.strip()):
            continue

        tmp = line.strip().split(separator)
        data.append(
            {
                'subdomain': tmp[0].strip().replace(' ', '-').lower(),
                'name': tmp[1].strip().replace(' ', '.').lower()
             }
        )
    return data
