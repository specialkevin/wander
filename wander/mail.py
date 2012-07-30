from mongoengine import *


class StoredMessage(Document):
    message_id = StringField(required = True)
    item_properties = ListField(StringField())
    labels = ListField(StringField())
    username = StringField()

    meta = {
        'indexes': ['message_id']
    }
    
