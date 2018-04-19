import json
import re
import urllib2
import zlib

from enigma import eTimer, eServiceReference

from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen


VAPI_GET_SERVERS=r'http://vapi.vaders.tv/user/server?action=getServers&username=%(USER)s&password=%(PWD)s'
VAPI_GET_USER_SERVER=r'http://vapi.vaders.tv/user/server?action=getUserServer&username=%(USER)s&password=%(PWD)s'
VAPI_SERVER_CHANGE=r'http://vapi.vaders.tv/user/server?action=serverChange&username=%(USER)s&password=%(PWD)s&serverIp=%(SERVER)s'
TS_RE=r'.*/live/(?P<user>[a-zA-Z0-9]+)/(?P<pwd>[a-zA-Z0-9]+)/[0-9]+\.(ts|m3u8).*'

DEBUG=True
DEBUG_FILE='/tmp/balancer-debug.log'
def debug(s):
  if DEBUG:
    f = open(DEBUG_FILE, 'a+')
    f.write(s)
    f.close()


def info(session, text=None, callback=None):
  if text:
    if callback:
      session.openWithCallback(callback, MessageBox, text, MessageBox.TYPE_INFO, simple=True)
    else:
      session.open(MessageBox, text, MessageBox.TYPE_INFO, simple=True)
  

def getJsonURL(url):
  request = urllib2.Request(url)
  request.add_header('Accept-Encoding', 'gzip')
  response = urllib2.urlopen(request)
  gzipped = response.info().get('Content-Encoding') == 'gzip'
  data = ''
  dec_obj = zlib.decompressobj(16+zlib.MAX_WBITS)
  while True:
    res_data = response.read()
    if not res_data:
      break
    if gzipped:
      data += dec_obj.decompress(res_data)
    else:
      data += res_data
  return json.loads(data)


def getServers(user=None, pwd=None):
  servers = {'AUTO': '0'}
  if not user or not pwd:
    return None
  try:
    data = getJsonURL(VAPI_GET_SERVERS % {'USER': user, 'PWD': pwd})
  except:
    return servers
  for datum in data:
    servers[str(datum['server_name'])] = str(datum['server_ip'])
  return servers


def getUserServer(user=None, pwd=None):
  if not user or not pwd:
    return None
  try:
    data = getJsonURL(VAPI_GET_USER_SERVER % {'USER': user, 'PWD': pwd})
    return str(data['name'])
  except:
    return 'AUTO'


def serverChange(user=None, pwd=None, server=None):
  if not user or not pwd or not server:
    return False
  try:
    return str(getJsonURL(VAPI_SERVER_CHANGE % {'USER': user, 'PWD': pwd, 'SERVER': server})) == 'OK'
  except:
    return False


class ServerSelectionScreen(Screen):
  skin = """<screen position="center,center" size="200,400">
            <widget source="myText" render="Label" position="25,25" size="150,50" font="Regular;25"/>
            <widget name="myList" position="25,100" size="150,275"/>
            </screen>"""
  def __init__(self, session, title=None, user=None, pwd=None):
    self.session = session
    Screen.__init__(self, session)
    if title:
      Screen.setTitle(self, title=title)
    self.user = user
    self.pwd = pwd
    self.servers = getServers(user=self.user, pwd=self.pwd)
    if not self.servers:
      info('Error retrieving possible servers')
      self.servers = {'AUTO': '0'}
    self.user_server = getUserServer(user=self.user, pwd=self.pwd)
    if not self.user_server:
      info('Error retrieving current server')
      self.user_server = '?'
    debug('user_server : %s\n' % self.user_server)
    self.server_names = self.servers.keys()
    self.server_names.sort()
    debug('server_names: %s\n' % self.server_names)
    self.myList =  MenuList(self.server_names)
    self['myText'] = StaticText(self.user_server)
    self['myList'] = self.myList
    self['myActionMap'] = ActionMap(['WizardActions'],
        {
          'back': self.exit,
          'ok': self.ok,
       }, -1)

  def exit(self):
    self.close()

  def ok(self):
    current = self.myList.getCurrent()
    if serverChange(user=self.user, pwd=self.pwd, server=self.servers[current]):
      self.user_server = getUserServer(user=self.user, pwd=self.pwd)
      if not self.user_server:
        info('Error retrieving current server')
        self.exit()
      self['myText'].setText(self.user_server)
    else:
      info('Error changing server to %s, please retry' % current)
    debug('ok pressed, cur: %s\n' % current)


def selectFromTS(session, ts=None, service=None):
  m = re.match(TS_RE, ts, re.IGNORECASE)
  if m:
    user = m.group('user')
    pwd = m.group('pwd')
    debug('u: %s, p: %s\n' % (user, pwd))
    session.open(ServerSelectionScreen, title='Balancer', user=user, pwd=pwd)
    return True
  return False


def main(session, **kwargs):
  service_ref = session.nav.getCurrentlyPlayingServiceReference()
  if service_ref:
    ts = service_ref.toString()
    debug('Current stream[ %s ]\n' % ts)
  else:
    info(session, text='No Current Stream!')
    return
  if selectFromTS(session, ts=ts, service=service_ref):
    return
  info(session, text='Unsupported Stream!')


def Plugins(**kwargs):
  return PluginDescriptor(
      name='Balancer', description='Load balancer selector',
      where=PluginDescriptor.WHERE_PLUGINMENU, icon='balancer.png', fnc=main)

