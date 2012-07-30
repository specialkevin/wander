import gdata.contacts.data

import gdata.contacts.client
import gdata.data

class Contacts(object):
    def __init__(self, settings):
        self.gd_client = gdata.contacts.client.ContactsClient(source='wander')
        self.gd_client.ClientLogin(settings['email'], settings['google_password'], self.gd_client.source)

    def list_contacts(self):
        feed = self.gd_client.GetContacts()
        for i, entry in enumerate(feed.entry):
            if entry.name:
                print entry.name.full_name.text
        return

    def create_contact(self):
        new_contact = gdata.contacts.data.ContactEntry()
        new_contact.name = gdata.data.Name(
            given_name = gdata.data.GivenName(text='Jimbo'),
            family_name = gdata.data.FamilyName(text='Harrison'),
            full_name = gdata.data.FullName(text='Jimbo Harrison'))
        contact_entry = self.gd_client.CreateContact(new_contact)
        print 'Created Contact'
        return

def main(settings):
    try:
        sample = Contacts(settings)
    except gdata.client.BadAuthentication:
        print 'Bad Login Credentials'
        return
    sample.list_contacts()
    sample.create_contact()
    sample.list_contacts()
