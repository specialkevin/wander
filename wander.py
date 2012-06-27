from ConfigParser import SafeConfigParser
import os.path
import requests
import argparse


def read_config():
  parser = SafeConfigParser()
  parser.read(os.path.expanduser('~/.wander.cfg'))
  return parser.items('zimbra')

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

def file_write(username, data_type, content):
  if data_type == 'contacts':
    filename = username+'_contacts.csv'
  elif data_type == 'calendar':
    filename = username+'_calendar.ics'
  else:
    return
  f = open(filename,'w')
  f.write(content)
  f.close()
  return

def get_user_contacts(username, settings):
  data_type = 'contacts'
  content = make_request(settings, username, data_type)
  file_write(username, data_type, content)
  return

def get_user_calendar(username, settings):
  data_type = 'calendar'
  content = make_request(settings, username, data_type)
  file_write(username, data_type, content)
  return

def parse_commands(settings):
  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers()

  parser_contacts = subparsers.add_parser('contacts')
  parser_contacts.add_argument('user')
  parser_contacts.set_defaults(func=get_user_contacts)

  parser_calendar = subparsers.add_parser('calendar')
  parser_calendar.add_argument('user')
  parser_calendar.set_defaults(func=get_user_calendar)

  args = parser.parse_args()
  args.func(args.user, settings)
  return

if  __name__ == "__main__":
  settings = dict(read_config())
  parse_commands(settings)
