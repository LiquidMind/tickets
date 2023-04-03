# This is a sample Python script.
import logging
from optparse import OptionParser

from api import get_obj_id, add_subdomain, add_mailbox, get_mailboxes_list
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


def process_mailbox(mailbox, forward_to=None):
    answ = print_and_log(
        logger,
        f'mailbox will be added {mailbox}, forward to {forward_to}, continue (y/n)?\n',
        True
    )
    if answ:
        res = add_mailbox(mailbox, forward_to)
    else:
        res = {'result': True, 'messages': 'Aborted by user'}

    if not res['result']:
        logger.error(res['messages'])

    return res['result']


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
                      help='Add domains and default mailboxes for them from file, requires --file option')
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
        data = process_data(options.file)
        for d in data:
            domain = f'{d["country"]}.{conf.MAIN_DOMAIN}'
            res = process_domain(domain)
            if res:
                info_mailbox = f'info@{domain}'
                mires = process_mailbox(info_mailbox, forward_to=f'info@{conf.MAIN_DOMAIN}')
                print_and_log(logger, mires)
                mailbox = f'{d["name"]}@{domain}'
                mres = process_mailbox(mailbox, forward_to=info_mailbox)
                print_and_log(logger, mres)
            else:
                print_and_log(logger, f'Domain does not created: {res}')
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
    else:
        parser.print_help()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
