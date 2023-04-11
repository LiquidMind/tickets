import os
import smtplib
import imaplib
import email
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
        accounts = conn.execute(sa.text("""SELECT email FROM accounts WHERE email_verified = 0""")).fetchall()
        i = 0
        for account in accounts:
            print_and_log(logger, f'Send email to {account.email}')
            try:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.login(conf.GMAIL_SMTP_USER, conf.GMAIL_SMTP_PASSWORD)
            except Exception as e:
                print_and_log(logger, f'ERROR: {e}')
            msg = MIMEText(f'Test for {account.email}')
            msg['Subject'] = f'Test for {account.email}'
            msg['From'] = 'ofitserov.andrej@gmail.com'
            msg['To'] = account.email
            server.sendmail('ofitserov.andrej@gmail.com', account.email, msg.as_string())
            sent_emails.append(account.email)
            i += 1
            print(i)
            server.quit()
            # time.sleep(1)

    return sent_emails


def receive_emails():
    print_and_log(logger, 'Start receiving emails')
    with engine.connect() as conn:
        accounts = conn.execute(sa.text("""SELECT email FROM accounts""")).fetchall()
        print_and_log(logger, f'Total accounts {len(accounts)}')
        received_emails = []
        for account in accounts:
            print_and_log(logger, f'Receive for {account.email}')
            server = imaplib.IMAP4_SSL('imap.gmail.com', 993)
            server.login('andrej.ofitserov@gmail.com', 'jpxqpiqxlhefnuru')
            server.list()
            server.select('INBOX')

            result, data = server.search(None, f'FROM ofitserov.andrej@gmail.com SUBJECT "Test for {account.email}"')

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
                    received_emails.append(account.email)
                    conn.execute(sa.text(f'UPDATE accounts SET email_verified = 1 WHERE email = "{account.email}"'))
                else:
                    print_and_log(logger, f'WARNING: subject: {mail["subject"]}')
                server.expunge()
                server.close()
                server.logout()
            else:
                print_and_log(logger, f'WARNING: email for {account.email} not found')
    return received_emails


def check_emails():
    print_and_log(logger, 'Start checking emails')
    sent = send_emails()
    received = receive_emails()
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
