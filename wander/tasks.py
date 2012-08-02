import sys
import imaplib
import mongoengine
from celery import Celery
from mongoengine.queryset import DoesNotExist

from wander import celeryconfig
from wander import imap_connect
from wander.mail import StoredMessage

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
    result, data = imap.uid('fetch', messageid, '(RFC822 FLAGS)')
    content = data[0][1]
    flags = list(imaplib.ParseFlags(data[1]))
    item_properties = []
    if '\\Seen' not in flags:
        item_properties.append('IS_UNREAD')
    return
    
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
    try:
        message = StoredMessage.objects.get(message_id = messageid)
    except DoesNotExist:
        print "Message does not exist in mongo id: {}".format(messageid)

    

    