from ConfigParser import SafeConfigParser
import os.path
import requests
import argparse
import imaplib
import time

import mongoengine
import gdata

import csv

from sys import stderr
from sys import exit
from sys import stdout

from fabric.api import run, env
from fabric.context_managers import settings, hide

from gdata.apps import client

import wander.google

def get_user_info(fabric_settings, user, desired_info):
    print 'Getting User Info from Zimbra for %s.\n' % user
    command = fabric_settings['zmprov_path'] + ' ga '+ user
    for i in desired_info:
        command = command + ' ' + i

    output = make_fabric_call(fabric_settings, command)
    output = output.splitlines()
    output.pop(0)
    info = {}
    info.update({'username' : user})
    for value in output:
        value = [x.strip() for x in value.split(':')]
        info.update({value[0] : value[1]})

    return info

def get_account_list(fabric_settings, username=None):
    command = fabric_settings['zmprov_path'] + ' -l gaa'
    output = make_fabric_call(fabric_settings, command)
    return output

def get_user_list_info(fabric_settings, user_list, desired_info):
    if user_list:
        output = []
        for user in user_list:
            output.append(get_user_info(fabric_settings, user, desired_info))
        return output
    else:
        stderr.write('OH NOES, No userlist\n')
        exit(1)

def get_usernames(fabric_settings):
    output = get_account_list(fabric_settings).splitlines()
    for i in output:
        output[output.index(i)] = i.split('@')[0]
    return output

def save_user_list_info(fabric_settings, user_list):
    if user_list:
        desired_info = ['givenName','sn','displayName']
        f = open('userinfo.csv','w')
        content = get_user_list_info(fabric_settings, user_list, desired_info)
        f.write('username,'+','.join(desired_info)+'\n')
        for i in content:
            line = ','.join(i.values())+'\n'
            f.write(line)
        f.close()
        return
    else:
        stderr.write('OH NOES, No userlist\n')
        exit(1)

def save_usernames(fabric_settings):
    return save('usernames', get_usernames(fabric_settings))

def save_account_list(fabric_settings, username=None):
    return save('accounts',get_account_list(fabric_settings))

def create_accounts(settings, username=None):
    google_apps = wander.google.Accounts(settings)
    errant_users = []
    if username:
        print 'Creating user account in Google for %s\n' % username
        user_info = get_user_info(settings, username, ['givenName', 'sn', 'displayName'])
        errant_users.append(google_apps.create_account(username, user_info, settings['temp_password']))
    else:
        user_info = get_user_list_info(settings, get_usernames(settings), ['givenName', 'sn', 'displayName'])
        for account in user_info:
            errant_users.append(google_apps.create_account(account['username'], account, settings['temp_password']))
    if not errant_users:
        for user in errant_users:
            print 'This account errored out and wasn\'t able to be created: %s\n' % user
    return

def make_fabric_call(fabric_settings, command):
    with settings(
        hide('stdout','running'),
        host_string = fabric_settings['server'], user = fabric_settings['zimbra_user'],
        key_filename = os.path.expanduser(fabric_settings['keypath'])
    ):
        print 'Running \' %s \' via Fabric.\n' % command
        output = run(command)
    return output

def read_user_list_file(path):
    f = open(path, 'r')
    content = f.readlines()
    f.close()
    content = [i.split('@')[0].strip() for i in content]
    return content

def read_config(section):
    parser = SafeConfigParser()
    parser.read(['/etc/wander.cfg', os.path.expanduser('~/wander.cfg'), os.path.expanduser('~/.wander.cfg')])
    return parser.items(section)

def make_request(settings, username, data_type):
    base_url = settings['server'] + ':' + settings['port'] + '/home/' + username
    if data_type == 'contacts':
        url = base_url + '/contacts'
    elif data_type == 'calendar':
        url = base_url + '/calendar'
    else:
        return
    r = requests.get(url, auth=(settings['username'],settings['password']))
    content = r.content
    return content

def save(data_type, content, username=None):
    if data_type == 'contacts' and username:
        filename = username+'_contacts.csv'
    elif data_type == 'calendar' and username:
        filename = username+'_calendar.ics'
    elif data_type == 'accounts':
        filename = 'accounts.txt'
    elif data_type == 'usernames':
        filename = 'usernames.txt'
        content = "\n".join(content)
    else:
        return
    f = open(filename,'w')
    f.write(content)
    f.close()
    return

def get_user_contacts(settings, username=None):
    data_type = 'contacts'
    if username:
        username = username[0]
        content = make_request(settings, username, data_type)
        save(data_type, content, username)
        filename = username+'_contacts.csv'
        data = csv.reader(open(filename))
        fields = data.next()
        contacts = []
        for row in data:
            items = zip(fields, row)
            item = {}
            for (name, value) in items:
                item[name] = value.strip()
            contacts.append(item)
        os.remove(filename)
        return contacts
    else:
        stderr.write('No username given\n')
        exit(1)

def migrate_contacts(settings, username=None):
    stdout.write('Getting Contacts from Zimbra for %s\n' % username)
    zimbra_contacts = get_user_contacts(settings, username)
    try: 
        stdout.write('Opening Connection to Google\n')
        google_contacts = wander.google.Contacts(username, settings)
    except gdata.client.BadAuthentication:
        stderr.write('Bad Login Credentials for Google Apps.\n')
        exit(1)

    google_contacts.create_contacts(zimbra_contacts)

    return

def print_user_contacts(settings, username=None):
    zimbra_contacts = get_user_contacts(settings, username)
    for contact in zimbra_contacts:
        print contact.keys()
        if contact['fullName'] == '':
            if contact['middleName'] == '':
                full_name = contact['firstName'] + ' ' + contact['lastName']
            else:
                full_name = contact['firstName'] + ' ' + contact['middleName'] + ' ' + contact['lastName']
        else:
            full_name = contact['fullName']
        print 'Full Name: %s' % full_name
        #print 'First Name: %s' % contact['firstName']
        #print 'Last Name: %s' % contact['lastName']
        print 'email: %s' % contact['email']
        print 'Home Phone: %s' % contact['homePhone']
        print 'Work Phone: %s' % contact['workPhone']
        print
    print "============================"
    print "CONTACTS FROM GOOGLE"
    print "============================"
    try:
        #email = username[0]+'@'+settings['google_domain']
        google_contacts = wander.google.Contacts(username, settings)
    except gdata.client.BadAuthentication:
        stderr.write('Bad Login Credentials for Google Apps.\n')
        exit(1)
    print google_contacts.list_contacts()
       
def get_user_calendar(settings, username=None):
    data_type = 'calendar'
    if username:
        username = username[0]
        content = make_request(settings, username, data_type)
        save(data_type, content, username)
        return
    else:
        stderr.write('No username given\n')
        exit(1)
        

def login_plain(imap, user, password, authuser=None):
    def plain_callback(response):
        if authuser is None:
            return "%s\00%s\x00%s" % (user, user, password)
        else:
            return "%s\x00%s\x00%s" % (user, authuser, password)
    return imap.authenticate('PLAIN', plain_callback)

def imap_connect(settings, user):
    imapconn = imaplib.IMAP4_SSL(settings['host'], 993)
    login_plain(imapconn, user, settings['password'], settings['admin'])
    return imapconn

def get_mail(settings, google_settings, userfile):
    '''
    For each user, get a list of message ids and send them to celery to process
    '''
    from wander.tasks import pull
    from wander.mail import StoredMessage

    mongoengine.connect('stored_messages')

    
    with open(userfile[0]) as f:
        count = 0
        for user in f.readlines():
            user = user.strip()
            
            error_count = 0
            while True:
                if error_count > 9:
                    break
                try:
                    imap = imap_connect(settings, user)
                    response_code, raw_folder_list = imap.list()
                except (imap.error, imap.abort, imaplib.IMAP4.error, imaplib.IMAP4.abort) as e:
                    print "Got imap error for user: {} : {}".format(user, e)
                    error_count += 1
                    try:
                        imap.logout()
                    except:
                        pass
                    time.sleep(1)
                    continue
                break

            if error_count > 9:
                continue
                
                
            for folder in raw_folder_list:
                # parse
                folder = folder.split('"')[1::2][1]
                if folder in ['Contacts', 'Chats', 'Emailed Contacts']:
                    continue

                messages = StoredMessage.objects.filter(username = user, folder=folder)
                completed_messages = [message.message_id for message in messages if message.migrated]                    
                error = False
                while True:
                    # Get all the message uids
                    try:
                        if error:
                            imap = imap_connect(settings, user)
                        imap.select(folder, True)
                        response_code, ids = imap.uid('search', None, 'ALL')
                        for messageid in ids[0].split():
                            if messageid not in completed_messages:
                                print "Starting import on message number {}\r".format(count),
                                pull.delay(settings, google_settings, user, folder, messageid)
                                count += 1
                        error = False
                    except (imap.error, imap.abort, imaplib.IMAP4.error, imaplib.IMAP4.abort) as e:
                        print "Got imap error: {}".format(e)
                        error = True
                        imap.logout()
                        time.sleep(1)
                        continue
                    break
                
                    
    print "Started import on total {}".format(count)

            
def auth_google(settings):
    google_client = client.AppsClient(domain=settings['domain'])
    google_client.ssl = True
    google_client.ClientLogin(email=settings['email'], password=settings['password'], source='apps')
    return google_client

