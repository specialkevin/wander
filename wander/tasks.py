import sys
import imaplib
import smtplib
import email
import mongoengine
from celery import Celery
from mongoengine.queryset import DoesNotExist
from gdata.apps.service import AppsForYourDomainException
from pprint import pprint


from wander import celeryconfig
from wander import imap_connect
from wander import read_config
from wander.mail import StoredMessage
from wander.google import MailMigration

google_settings = dict(read_config('google'))


celery = Celery('tasks')
celery.config_from_object(celeryconfig)


migration = MailMigration(google_settings)
mongoengine.connect('stored_messages')

@celery.task(default_retry_delay = 61)
def pull(settings, google_settings, user, folder, messageid):
    '''
    Pulls a message from zimbra and stores it in Mongo
    '''

    try:
        imap = imap_connect(settings, user)
        imap.select(folder, True)
        result, data = imap.uid('fetch', messageid, '(RFC822 FLAGS)')
        imap.logout()
        content = data[0][1]
        flags = list(imaplib.ParseFlags(data[1]))
        item_properties = []
        if '\\Seen' not in flags:
            item_properties.append('IS_UNREAD')
        if folder.lower().startswith('sent '):
            item_properties.append('IS_SENT')

        # munge me some unicode
        content = content.decode('utf-8', errors='ignore')

        messages = StoredMessage.objects.filter(message_id = messageid, username = user, folder = folder)
        if len(messages) == 0:
            message = StoredMessage(message_id = messageid, item_properties = item_properties, folder=folder, username = user)
        else:
            message = messages[0]
            message.item_properties = item_properties
            message.folder = folder
        try:
            message.save()
        except mongoengine.base.ValidationError as e:
            print "Unexpected error:", e
            return

    except (imap.error, imap.abort, imaplib.IMAP4.error, imaplib.IMAP4.abort) as e:
        print "Imap error: {}".format(e)
        # Celery can't pickle the imap errors
        sys.exc_clear()
        pull.retry()

    try:
        migration.migrate(message.username, content.encode('utf-8'), message.item_properties, message.folder.split('/'))
        message.migrated = True
        message.save()

    except AppsForYourDomainException, e:
        if e.error_code == 503:
            pull.retry()
        elif 'Invalid RFC 822 Message' in str(e) or 'Permanent failure: BadAttachment' in str(e):
            # Try to forward message.
            if isinstance(content, unicode):
                msg_text = content.encode("ascii", "ignore")
            email_message = email.message_from_string(msg_text)
            # replace headers (could do other processing here)
            to_addr = "{}@{}".format(message.username, google_settings['google_domain'])
            email_message.replace_header("To", to_addr)

            # open authenticated SMTP connection and send email_message with
            # specified envelope from and to addresses
            smtp = smtplib.SMTP(settings['host'], 25)
            smtp.starttls()
            smtp.login(settings['admin'], settings['password'])
            smtp.sendmail(email_message.get('From'),to_addr, email_message.as_string())
            smtp.quit()
            message.migrated = True
            message.save()

        else:
            print "Unexpected Apps error: {}".format(e)
            sys.exc_clear()
            pull.retry()

    except:
        print "Unexpected error:{}".format(sys.exc_info())
        sys.exc_clear()
        pull.retry()

        

    