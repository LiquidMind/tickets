# This is a sample Python script.
import logging
import time
from optparse import OptionParser

from api import get_obj_id, add_subdomain, add_mailbox, get_mailboxes_list, get_subdomains_list, edit_mailbox_subdomain
from common.functions import process_data, print_and_log

import conf
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


logger = logging.getLogger('api')
handler = logging.FileHandler('api.log')
handler.setFormatter(logging.Formatter(fmt='[%(asctime)s: %(levelname)s] %(message)s'))
logger.addHandler(handler)


def process_domain(domain):
    already_exists = get_obj_id(f'{domain}', 'host')
    print_and_log(
        logger,
        f'START CREATING {domain}'
    )
    if already_exists['result']:
        answ = print_and_log(logger, f'already exists {already_exists["result"]}, continue? \n', True)
        if not answ:
            return True

    # type A record creating
    answ = print_and_log(
        logger,
        f'Subdomain type A will be added {domain}, continue (y/n)?\n',
        True
    )
    if answ:
        res_a = add_subdomain(domain.replace(f'.{conf.MAIN_DOMAIN}', ''), 'A', conf.MAIN_DOMAIN_IP)
        print_and_log(logger, res_a)
    else:
        print_and_log(logger, 'Aborted by user')
        res_a = {'result': True, 'messages': 'Aborted by user'}

    if not res_a['result']:
        logger.error(res_a['messages'])

    # type MX record creating
    answ = print_and_log(
        logger,
        f'Subdomain type MX will be added {domain}, continue (y/n)?\n',
        True
    )
    if answ:
        res_mx = add_subdomain(domain.replace(f'.{conf.MAIN_DOMAIN}', ''), 'MX', conf.MAIN_DOMAIN_MX)
        print_and_log(logger, res_mx)
    else:
        res_mx = {'result': True, 'messages': 'Aborted by user'}

    if not res_mx['result']:
        logger.error(res_mx['messages'])

    return res_a['result'] and res_mx['result']


def process_mailbox(mailbox, check_domain=False, forward_to=None):
    answ = print_and_log(
        logger,
        f'mailbox will be added {mailbox}, forward to {forward_to}, continue (y/n)?\n',
        True
    )
    if answ:
        res = add_mailbox(mailbox, check_domain, forward_to)
    else:
        res = {'result': True, 'messages': 'Aborted by user'}

    if not res['result']:
        logger.error(res)

    return res


def add_new_mailboxes(source_file, add=False):
    with open(source_file) as f:
        new_mailboxes = set([l.strip() for l in f.readlines()])
    res_mailboxes = get_mailboxes_list()
    existing_mailboxes = []
    if res_mailboxes['result']:
        tmp = [v for k, v in res_mailboxes['response']['list'].items()]
        # print(len(tmp))
        for mailboxes in tmp:
            for mailbox in ([m['email_auto'] for m in mailboxes]):
                existing_mailboxes.append(mailbox)
    # print(len(existing_mailboxes))
    new_mailboxes.difference_update(set(existing_mailboxes))
    print_and_log(logger, 'Emails not presented in domain:')
    print_and_log(logger, new_mailboxes)
    if add and new_mailboxes is not None:
        for mailbox in new_mailboxes:
            res = add_mailbox(mailbox, check_domain=True)
            if not res['result']:
                logger.error("Can't add mailbox %s", res)
            else:
                print_and_log(logger, res)


def main():
    usage = """
        python %prog --add-domains --file data/countries.txt
        python %prog --new-emails [show, add] --file data/new_emails.txt
    """
    parser = OptionParser(usage=usage)

    parser.add_option('--add-domains', action='store_true', dest='add_domains', default=False,
                      help='Add domains from file, requires --file option')
    parser.add_option('--add-mailbox', action='store', dest='add_mailbox', default=None,
                      type='choice', choices=['show', 'add'],
                      help='Add default mailboxes for subdomains from file, requires --file option')
    parser.add_option('--update-subdomains', action='store_true', dest='update_subdomains', default=False,
                      help='Update subdomains, set [catch_non_exist=info@subdomain.domain.zone '
                           'and allow_custom_sender=1] parameters')
    parser.add_option('--new-emails', action='store', dest='new_emails', default=None,
                      type='choice', choices=['show', 'add'],
                      help='Compare specified list of emails with already presented for domain and show or add them')
    parser.add_option('--file', action='store', dest='file', default=False,
                      help='File path for process')

    (options, args) = parser.parse_args()

    if options.add_domains:
        if not options.file:
            parser.error('Running requires --file option')
        print(f'Add domains from {options.file}')
        data = process_data(options.file, separator=';')
        for d in data:
            domain = f'{d["subdomain"]}.{conf.MAIN_DOMAIN}'
            res = process_domain(domain)
            if not res:
                print_and_log(logger, f'Domain does not created: {res}')
    elif options.add_mailbox is not None:
        if not options.file:
            parser.error('Running requires --file option')
        print(f'Add new mailboxes from {options.file}')
        data = process_data(options.file, separator=';')
        for d in data:
            domain = f'{d["subdomain"]}.{conf.MAIN_DOMAIN}'
            info_mailbox = f'info@{domain}'
            if options.add_mailbox == 'add':
                mires = process_mailbox(info_mailbox, forward_to=f'info@{conf.MAIN_DOMAIN}')
                print_and_log(logger, mires)
            elif options.add_mailbox == 'show':
                print_and_log(logger, f'New mailbox will be added: {info_mailbox}')
            else:
                print_and_log(logger, 'New mailbox: Unknown option')

            # TODO: add option for enable/disable adding user's email
            # mailbox = f'{d["name"]}@{domain}'
            # mres = process_mailbox(mailbox, forward_to=info_mailbox)
            # print_and_log(logger, mres)
    elif options.new_emails == 'show':
        if not options.file:
            parser.error('Running requires --file option')
        print(f'Show new_emails from {options.file}')
        add_new_mailboxes(options.file, add=False)
    elif options.new_emails == 'add':
        if not options.file:
            parser.error('Running requires --file option')
        print(f'Show new_emails from {options.file}')
        add_new_mailboxes(options.file, add=True)
    elif options.update_subdomains:
        # TODO: handle errors correctly
        sub_res = get_subdomains_list()
        # print(sub_res)
        # return True
        if sub_res['result'] and len(sub_res['response']['list']):
            for key, subdomain in sub_res['response']['list'].items():
                if not int(subdomain['email_catch_non_existent']):
                    mail_res = get_obj_id(f'info@{key}', 'mailbox')
                    if mail_res['result']:
                        res = edit_mailbox_subdomain(subdomain["virtual_domain_id"], mail_res['response']['box_id'])
                        if res['result']:
                            print(f'UPDATING {key} with id {subdomain["virtual_domain_id"]}: {res["result"]}')
                            time.sleep(1)
                        else:
                            print(f'ERROR UPDATING {subdomain["virtual_domain_id"]}')
                            print(res)
                    else:
                        print(f'id for info@{key} not found')
                        print(mail_res)
        else:
            print(sub_res)
    else:
        parser.print_help()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
