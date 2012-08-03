import sys
import imaplib
import mongoengine
from celery import Celery
from mongoengine.queryset import DoesNotExist
from gdata.apps.service import AppsForYourDomainException

from wander import celeryconfig
from wander import imap_connect
from wander.mail import StoredMessage
from wander.google import MailMigration

celery = Celery('tasks')
celery.config_from_object(celeryconfig)

@celery.task(default_retry_delay = 61)
def pull(settings, google_settings, user, folder, messageid):
    '''
    Pulls a message from zimbra and stores it in Mongo
    '''
    mongoengine.connect('stored_messages')
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

        message = StoredMessage(message_id = messageid, item_properties = item_properties, labels=folder.split('/'), username = user)
        try:
            message.save()
        except (mongoengine.base.ValidationError, mongoengine.queryset.OperationError) as e:
            print "Unexpected error:", e
            return

        push.delay(settings, google_settings, messageid, content)
    except (imap.error, imap.abort, imaplib.IMAP4.error, imaplib.IMAP4.abort) as e:
        print "Imap error: {}".format(e)
        # Celery can't pickle the imap errors
        sys.exc_clear()
        pull.retry()

@celery.task(default_retry_delay = 61)
def push(settings, google_settings, messageid, content):
    '''
    Pulls a message from Mongo and pushs it into Google Apps
    '''
    mongoengine.connect('stored_messages')

    try:
        message = StoredMessage.objects.get(message_id = messageid)
    except DoesNotExist:
        print "Message does not exist in mongo id: {}".format(messageid)

    try:
        migration = MailMigration(google_settings)
        migration.migrate(message.username, content, message.item_properties, message.labels)
        message.migrated = True
        message.save()
        
    except AppsForYourDomainException, e:
        if e['status'] == 503:
            push.retry()
        else:
            raise
    

    