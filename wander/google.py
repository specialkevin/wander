import gdata.contacts.data
import gdata.contacts.client

class Contacts(object):
    def __init__(self, email, settings):
        self.gd_client = gdata.contacts.client.ContactsClient(source='wander')
        self.gd_client.ClientLogin(email, settings['google_password'], self.gd_client.source)

    def list_contacts(self):
        feed = self.gd_client.GetContacts()
        for entry in feed.entry:
            if entry.name:
                print entry.name.full_name.text
        return

