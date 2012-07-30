from wander import imap_connect
from wander import auth_google

from mongoengine import *


class StoredMessage(Document):
    message_id = StringField(required = True)
    item_properties = ListField(StringField())
    labels = ListField(StringField())
    username = StringField()

    meta = {
        'indexes': {'fields': ['message_id'],
                    'unique': True}
    }
    
