import atom.data
import gdata.contacts.data
import gdata.contacts.client
import gdata.apps.client

from sys import stdout

class Accounts(object):
    def __init__(self, settings):
        self.ga_client = gdata.apps.client.AppsClient(domain=settings['google_domain'])
        self.ga_client.ssl = True
        self.ga_client.ClientLogin(email=settings['google_admin'], password=settings['google_password'], source='apps')

    def get_account(self, user):
        return self.ga_client.RetrieveUser(user[0])

    def create_account(self, user, user_info, password):
        first_name = user_info['givenName']
        last_name = user_info['sn']
        display_name = user_info['displayName']
        self.ga_client.CreateUser(user_name=user, family_name = last_name, given_name = first_name, password = password)       
        return

class Contacts(object):
    def __init__(self, user, settings):
        email = user[0]+'@'+settings['google_domain']
        self.gd_client = gdata.contacts.client.ContactsClient(source='wander')
        self.gd_client.ClientLogin(email, settings['google_password'], self.gd_client.source)

    def list_contacts(self):
        feed = self.gd_client.GetContacts()
        for entry in feed.entry:
            if entry.name:
                print entry.name.full_name.text
        return

    def create_contacts(self, contacts):
        stdout.write('Migrating Contacts to Google....\n')
        for contact in contacts:
            new_contact = gdata.contacts.data.ContactEntry()

            if contact['fullName']:
                full_name = contact['fullName']
            else:
                if contact['middleName']:
                    full_name = contact['firstName'] + ' ' + contact['lastName']
                else:
                    full_name = ' '.join([contact['firstName'], contact['middleName'], contact['lastName']])

            firstName = contact['firstName'] if contact['firstName'] else ' '
            lastName = contact['lastName'] if contact['lastName'] else ' '
            
            if contact['fullName'] and contact['firstName'] and contact['lastName']:
                next
            else:
                new_contact.name = gdata.data.Name(
                    given_name = gdata.data.GivenName(text=firstName),
                    family_name = gdata.data.FamilyName(text=lastName),
                    full_name = gdata.data.FullName(text=full_name))
                del contact['firstName']
                del contact['lastName']
                if 'middleName' in contact:
                    del contact['middleName']
                del contact['fullName']

                if contact['email']:
                    new_contact.email.append(gdata.data.Email(address = contact['email'], 
                        primary = 'true', display_name = full_name, rel = gdata.data.OTHER_REL))
                    del contact['email']
                if 'email2' in contact and contact['email2']:
                    new_contact.email.append(gdata.data.Email(address = contact['email2'], 
                        display_name = full_name, rel = gdata.data.OTHER_REL))
                    del contact['email2']

                if 'homePhone' in contact and contact['homePhone']:
                    new_contact.phone_number.append(gdata.data.PhoneNumber(text = contact['homePhone'], 
                        rel = gdata.data.HOME_REL))
                    del contact['homePhone']

                if 'workPhone' in contact and contact['workPhone']:
                    new_contact.phone_number.append(gdata.data.PhoneNumber(text = contact['workPhone'], 
                        rel = gdata.data.WORK_REL))
                    del contact['workPhone']

                if 'mobilePhone' in contact and contact['mobilePhone']:
                    new_contact.phone_number.append(gdata.data.PhoneNumber(text = contact['mobilePhone'],
                        rel = gdata.data.MOBILE_REL))
                    del contact['mobilePhone']

                if 'company' in contact and contact['company']:
                    new_contact.organization = gdata.data.Organization(
                        org_name = gdata.data.OrgName(text = contact['company']),
                        rel = gdata.data.WORK_REL)
                    del contact['company']

                new_contact.content = atom.data.Content(text = '\n'.join(contact.values()))
    
                self.gd_client.CreateContact(new_contact)
        return
