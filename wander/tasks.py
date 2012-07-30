from wander.celery import celery
from wander.mail import StoredMessage

@celery.task
def pull(messageid):
    '''
    Pulls a message from zimbra and stores it in Mongo
    '''
    pass

@celery.task
def push(messageid):
    '''
    Pulls a message from Mongo and pushs it into Google Apps
    '''
    pass
    