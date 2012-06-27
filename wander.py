from ConfigParser import SafeConfigParser
import os.path
import requests

def read_config():
  parser = SafeConfigParser()
  parser.read(os.path.expanduser('~/.wander.cfg'))
  return parser.items('zimbra')

def make_request(settings, username, data_after):
  base_url = settings['server'] + ':' + settings['port'] + '/home/' + username
  if data_after == 'contacts':
    url = base_url + '/contacts'
  elif data_after == 'calendar':
    url = base_url + '/calendar'
  else:
    return
  r = requests.get(url, auth=(settings['username'],settings['password']))
  content = r.content
  return content

def file_write(username, data_after, content):
  if data_after == 'contacts':
    filename = username+'_contacts.csv'
  elif data_after == 'calendar':
    filename = username+'_calendar.ics'
  else:
    return
  f = open(filename,'w')
  f.write(content)
  f.close()
  return

def get_user_contacts(username, settings):
  data_after = 'contacts'
  content = make_request(settings, username, data_after)
  file_write(username, data_after, content)
  return

def get_user_calendar(username, settings):
  data_after = 'calendar'
  content = make_request(settings, username, data_after)
  file_write(username, data_after, content)
  return


if  __name__ == "__main__":
  settings = dict(read_config())
  #print settings
  get_user_contacts('kharriss',settings)
  get_user_calendar('kharriss',settings)
