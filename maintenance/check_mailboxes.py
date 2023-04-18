import os
import smtplib
import imaplib
import email
import time

import sqlalchemy as sa
# import time
import logging

from optparse import OptionParser
from email.mime.text import MIMEText

from common.functions import print_and_log
import conf

engine = sa.create_engine(conf.MYSQL_CONNECTION_STRING, isolation_level="AUTOCOMMIT")
logger = logging.getLogger('generate_personal_data')
handler = logging.FileHandler('logs/check_mailboxes.log')
handler.setFormatter(logging.Formatter(fmt='[%(asctime)s: %(levelname)s] %(message)s'))
logger.setLevel('DEBUG')
logger.addHandler(handler)


def send_emails():
    sent_emails = []
    with engine.connect() as conn:
        # TODO: remove clause "prime IS NULL"
        accounts = conn.execute(
            sa.text("""SELECT email FROM accounts WHERE email_verified = 0 AND prime IS NULL ORDER BY email""")
        ).fetchall()
        i = 0
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(conf.GMAIL_SMTP_USER, conf.GMAIL_SMTP_PASSWORD)

        for account in accounts:
            print_and_log(logger, f'Send email to {account.email}')
            try:
                # server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                # server.login(conf.GMAIL_SMTP_USER, conf.GMAIL_SMTP_PASSWORD)
                # server.connect()
                msg = MIMEText(f'Test for {account.email}')
                msg['Subject'] = f'Test for {account.email}'
                msg['From'] = f'{conf.GMAIL_SMTP_USER}'
                msg['To'] = account.email
                send_res = server.sendmail(conf.GMAIL_SMTP_USER, account.email, msg.as_string())
                # print(send_res)
                sent_emails.append(account.email)
                i += 1
                print(i)
                time.sleep(1)
                # server.quit()
                # Gmail limits per day = 500
                if i >= 80:
                    break
            except Exception as e:
                print(f'Exception: {e}')
                # server.quit()
                return sent_emails
        server.quit()
    return sent_emails


def receive_emails(accounts_list=[]):
    print_and_log(logger, 'Start receiving emails')
    with engine.connect() as conn:
        if len(accounts_list):
            acc_srt = ','.join([f"'{a}'" for a in accounts_list])
            where = f"WHERE email IN({acc_srt})"
        else:
            where = ''
        accounts = conn.execute(sa.text(f"""SELECT email FROM accounts {where}""")).fetchall()
        print_and_log(logger, f'Total accounts {len(accounts)}')
        received_emails = []

        server_chronisto = imaplib.IMAP4_SSL('mail.adm.tools', 993)
        server_chronisto.login('info@chronisto.com', '83zh5HSBd4')
        server_chronisto.select('INBOX')

        server = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        server.login('andrej.ofitserov@gmail.com', 'jpxqpiqxlhefnuru')
        server.list()
        server.select('INBOX')

        for account in accounts:
            print_and_log(logger, f'Receive for {account.email}')

            result, data = server.search(None, f'FROM {conf.GMAIL_SMTP_USER} SUBJECT "Test for {account.email}"')
            result_c, data_c = server_chronisto.search(None, f'SUBJECT "Test for {account.email}"')
            ids_c = data_c[0]

            ids = data[0]  # data is a list.
            id_list = ids.split()  # ids is a space separated string

            if len(id_list):
                print_and_log(logger, f'Mail received for {account.email}')
                latest_email_id = id_list[-1]  # get the latest
                # fetch the email body (RFC822) for the given ID
                result, data = server.fetch(latest_email_id, "(RFC822)")
                mail = email.message_from_bytes(data[0][1])
                if mail['subject'] == f'Test for {account.email}':
                    print_and_log(logger, f'Subject OK')
                    # mark as deleted
                    server.store(latest_email_id, '+FLAGS', '\\Deleted')
                    server_chronisto.store(ids_c, '+FLAGS', '\\Deleted')
                    received_emails.append(account.email)
                    conn.execute(sa.text(f'UPDATE accounts SET email_verified = 1 WHERE email = "{account.email}"'))
                else:
                    print_and_log(logger, f'WARNING: subject: {mail["subject"]}')
                server.expunge()
                server_chronisto.expunge()
                # server.close()
                # server.logout()
            else:
                print_and_log(logger, f'WARNING: email for {account.email} not found')
    server.close()
    server_chronisto.close()
    server.logout()
    server_chronisto.logout()
    return received_emails


def check_emails():
    print_and_log(logger, 'Start checking emails')
    sent = send_emails()
    received = receive_emails(sent)
    print_and_log(logger, f'Sent: {len(sent)}, received: {len(received)}')
    return len(sent) == len(received)


def main():
    usage = """
        python %prog --send
        python %prog --receive
        python %prog --check
    """

    parser = OptionParser(usage=usage)

    parser.add_option('--send', action='store_true', dest='send', default=False,
                      help='Send email for each account')
    parser.add_option('--receive', action='store_true', dest='receive', default=False,
                      help='Receive and check email for each account')
    parser.add_option('--check', action='store_true', dest='check', default=False,
                      help='Check email for each account')

    (options, args) = parser.parse_args()

    if options.send:
        res = send_emails()
        print_and_log(logger, f'Processed {len(res)} emails')
    elif options.receive:
        res = receive_emails()
        print_and_log(logger, f'Processed {len(res)} emails')
    elif options.check:
        res = check_emails()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
