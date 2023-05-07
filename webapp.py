import re
import imaplib
import email

from flask import Flask, jsonify, request
from flask_cors import CORS
from functools import wraps
from werkzeug.exceptions import BadRequest
from anyascii import anyascii

from api.accounts import get_free_accounts, update_account

import conf

app = Flask(__name__)
cors = CORS(app, resources={r'/api/*': {'origins': '*'}})


def json_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not request.is_json:
            return jsonify({'msg': 'Missing JSON in request'}), 400

        try:
            request.json
        except BadRequest:
            return jsonify({'msg': 'JSON is not valid'}), 400

        return f(*args, **kwargs)
    return wrapped


def get_email_body(message):
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/html":
                return part.get_payload(decode=True).decode()
    else:
        return message.get_payload(decode=True).decode()


@app.route('/api/test', methods=['GET', 'POST'])
def test():
    response = {'success': True}
    return jsonify(response), 200


@app.route('/api/get_account', methods=['POST'])
@json_required
def get_account():
    country = request.json.get('country', False)
    print(country)
    if country:
        clause = f'AND c.capital="{country}"'
    else:
        clause = ''

    account = get_free_accounts(clause=clause, limit=1)

    if len(account):
        if country != 'United Kingdom':
            pattern = r'^(.+),\s((\d{4}-\d{3})|(\d{5})).*$'
        else:
            pattern = r'^(.+)\s([A-Z,\d,\s]{5,7})$'
        address_parts = re.search(pattern, account[0].address)
        print(account[0].address)
        if address_parts is None or len(address_parts.groups()) < 2:
            return jsonify({'success': False, 'msg': 'bad address format'}), 400

        response = {
            'success': True,
            'account': {
                'id': account[0].id,
                'name': account[0].name,
                'surname': account[0].surname,
                'country': account[0].capital,
                'city': account[0].location,
                'address': address_parts.group(1),
                'postcode': address_parts.group(2).strip(),
                'personal_id': account[0].personal_id,
                'email': account[0].email,
                'password': account[0].password,
                'phone': account[0].phone,
                'birth_day': account[0].birth_date.strftime('%d'),
                'birth_month': account[0].birth_date.strftime('%m'),
                'birth_year': account[0].birth_date.strftime('%Y'),
            }
        }
        return jsonify(response), 200
    return jsonify({'success': False, 'msg': 'Not found'}), 404


@app.route('/api/check_email', methods=['POST'])
@json_required
def check_email():
    account = request.json.get('account', False)
    print(account)
    server = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    server.login('andrej.ofitserov@gmail.com', 'jpxqpiqxlhefnuru')
    # server.list()
    server.select('INBOX')
    subj = 'UEFA – please confirm your email address'
    print(f'FROM no-reply@uefa.com TO {account["email"]} SUBJECT {anyascii(subj)}')
    result, data = server.search(None, f'FROM no-reply@uefa.com TO {account["email"]} SUBJECT "{anyascii(subj)}"')

    if len(data):
        ids = data[0]  # data is a list.
        if len(ids) > 1:
            id_list = ids.split()  # ids is a space separated string
            last_id = id_list[-1]
        else:
            last_id = data[0]

        mresult, mdata = server.fetch(last_id, "(RFC822)")
        server.close()
        mail = email.message_from_bytes(mdata[0][1])
        msg = get_email_body(mail)
        pattern = r'href=["\'](https:\/\/accounts\.eu1\.gigya\.com\/accounts\.verifyEmail[^"\']*)["\']'
        matches = re.findall(pattern, msg, re.IGNORECASE)
        url = matches[0]
        response = {'success': True, 'url': url}
        return jsonify(response), 200
    else:
        server.close()
        response = {'success': False, 'msg': 'mail not found'}
        return jsonify(response), 401


if __name__ == '__main__':
    app.run(debug=True)
