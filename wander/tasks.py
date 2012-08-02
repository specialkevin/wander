from wander.mail import StoredMessage
from celery import Celery
import imaplib
import mongoengine

from wander import celeryconfig
from wander import imap_connect
import sys

celery = Celery('tasks')
celery.config_from_object(celeryconfig)
@celery.task
def pull(settings, user, folder, messageid):
    '''
    Pulls a message from zimbra and stores it in Mongo
    '''
    mongoengine.connect('stored_messages')
    try:
        imap = imap_connect(settings, user)
    except imaplib.IMAP4.error, e:
        print "Unexpected error:", e
        return
    imap.select(folder, True)
    result, data = imap.uid('fetch', messageid, '(RFC822)')
    content = data[0][1]

    # munge me some unicode
    content = content.decode('utf-8', errors='ignore')

    message = StoredMessage(message_id = messageid, item_properties = [], labels=folder.split('/'), username = user)
    try:
        message.save()
    except mongoengine.base.ValidationError, e:
        print "Unexpected error:", e

    push.delay(messageid, content)


@celery.task
def push(messageid, content):
    '''
    Pulls a message from Mongo and pushs it into Google Apps
    '''
    pass

    