from ConfigParser import SafeConfigParser
import os.path
import requests
import argparse
import imaplib

import csv

from sys import stderr
from sys import exit

from fabric.api import run, env
from fabric.context_managers import settings, hide

from gdata.apps import client

def get_user_info(fabric_settings, user, desired_info):
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
    command = fabric_settings['zmprov_path'] + ' -l    gaa'
    output = make_fabric_call(fabric_settings, command)
    return output

def get_user_list_info(fabric_settings, user_list, desired_info):
    if user_list:
        output = []
        for i in user_list:
            output.append(get_user_info(fabric_settings, i, desired_info))
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

def make_fabric_call(fabric_settings, command):
    with settings(
        hide('stdout','running'),
        host_string = fabric_settings['server'], user = fabric_settings['zimbra_user'],
        key_filename = os.path.expanduser(fabric_settings['keypath'])
    ):
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

def print_user_contacts(settings, username=None):
    print get_user_contacts(settings, username)
       
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

def get_mail(settings, username):
    if username:
        username = username[0]
        imap = imap_connect(settings, username)
        print imap.list()
        return
    else:
        stderr.write("OH NOES, no user given\n")
        exit(1)

def auth_google(settings):
    google_client = client.AppsClient(domain=settings['domain'])
    google_client.ssl = True
    google_client.ClientLogin(email=settings['email'], password=settings['password'], source='apps')
    return google_client

