from wander.mail import StoredMessage
from celery import Celery

celery = Celery('tasks', broker='mongodb://localhost:27017/database_name')

@celery.task
def pull(folder, messageid):
    '''
    Pulls a message from zimbra and stores it in Mongo
    '''
    print "Pull {}".format()

@celery.task
def push(messageid):
    '''
    Pulls a message from Mongo and pushs it into Google Apps
    '''
    pass
    