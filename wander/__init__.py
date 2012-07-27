from ConfigParser import SafeConfigParser
import os.path
import requests
import argparse
import imaplib

from fabric.api import run, env
from fabric.context_managers import settings, hide

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
        print 'OH NOES'
        return

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
        print 'OH NOES'
        return

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
        content = make_request(settings, username, data_type)
        save(data_type, content, username)
        return
    else:
        print "OH NOES"
        return

def get_user_calendar(settings, username=None):
    data_type = 'calendar'
    if username:
        content = make_request(settings, username, data_type)
        save(data_type, content, username)
        return
    else:
        print "OH NOES"
        return

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
        imap = imap_connect(settings, username)
        print imap.list()
        return
    else:
        print "OH NOES, YOU NEED TO ENTER A USER TO MIGRATE"
        return
