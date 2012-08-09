from mongoengine import *


class StoredMessage(Document):
    message_id = StringField(required = True)
    item_properties = ListField(StringField())
    folder = StringField()
    username = StringField()
    migrated = BooleanField(default=False)
    
    meta = {
        'indexes': [{ 'fields': ['message_id','username','folder'], 'unique': True },
                    ['username','folder'],
                    'username'],
    }
    
