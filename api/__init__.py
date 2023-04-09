from common.functions import send_post_request

import conf


def add_subdomain(name, record_type, data):
    post = {
        'domain_id': conf.DOMAIN_ID,
        'priority': 0,
        'type': record_type,
        'data': data,
        'record': name,
    }
    response = send_post_request(conf.API_URL_ADD_SUBDOMAIN, post)
    return response


def add_mailbox(mailbox: str, check_domain=False, forward_to=None):
    mail_parts = mailbox.split('@')
    name = mail_parts[0]
    domain = mail_parts[1]
    country = domain.replace(f'.{conf.MAIN_DOMAIN}', '')
    if check_domain:
        domain_exists = get_obj_id(domain, 'host')
        if not domain_exists['result']:
            return domain_exists

    if name == 'info':
        pwd = f'Pwd4info.{country}'
        forward_to = f'info@{conf.MAIN_DOMAIN}'
    elif forward_to is None:
        pwd = f'Pwd4{name}'
        forward_to = f'info@{domain}'

    post = {
        'account_id': conf.DOMAIN_ACCOUNT_ID,
        'login': f'{name}@{domain}',
        'password': pwd,
        'autoresponder_enabled': 0,
        'autoresponder_text': '',
        'autoresponder_title': '',
        'box_limit': 0,
        'box_quota': 0,
        'check_spam_level': 2,
        'copy': 1,
        'forward_to': [forward_to],
        'redirect': 1,
        'virtual_domain_id': 0,
    }
    response = send_post_request(conf.API_URL_ADD_MAILBOX, post)
    return response


def get_obj_id(obj_name, obj_type):
    post = {
        'name': obj_name,
        'type': obj_type
    }
    response = send_post_request('https://adm.tools/action/get_id', post)
    return response


def get_mailboxes_list():
    post = {
        'account_id': conf.DOMAIN_ACCOUNT_ID
    }
    response = send_post_request(conf.API_URL_MAILBOXES_LIST, post)

    return response


def get_subdomains_list():
    """
    https://adm.tools/user/api/#/tab-sandbox/hosting/virtual/list
    """
    post = {
        'account_id': conf.DOMAIN_ACCOUNT_ID
    }
    response = send_post_request(conf.API_URL_DOMAINS_LIST, post)
    return response


def edit_mailbox_subdomain(virtual_domain_id, catch_non_exist, allow_custom_sender=1):
    """
    https://adm.tools/user/api/#/tab-sandbox/hosting/mail/settings
    """
    post = {
        'virtual_domain_id': virtual_domain_id,
        'catch_non_exist': catch_non_exist,
        'allow_custom_sender': allow_custom_sender
    }
    response = send_post_request(conf.API_URL_MAIL_SETTINGS, post)
    return response
