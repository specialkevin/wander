import atom.data
import gdata.contacts.data
import gdata.contacts.client

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
        for contact in contacts:
            new_contact = gdata.contacts.data.ContactEntry()

            if contact['fullName']
                full_name = contact['fullName']
            else:
                if contact['middleName']:
                    full_name = contact['firstName'] + ' ' + contact['lastName']
                else:
                    full_name = ' '.join([contact['firstName'], contact['middleName'], contact['lastName']])

            firstName = contact['firstName'] if contact['firstName'] else firstName = ' '
            lastName = contact['lastName'] if contact['lastName'] else lastName = ' '
            
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
