title_like = True
try:
  import inspect
  from Screens.MessageBox import MessageBox
  title_like = 'title' in inspect.getargspec(MessageBox.__init__)[0] 
except:
  title_like = False

import base64
import json
import re
import time
import traceback
import urllib2
import zlib

from enigma import eServiceReference, eTimer

from Components.config import config
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox

PLUGIN_VERSION='6.2.0g'
PLUGIN_NAME='Subway'
PLUGIN_DESC='Subscription info'
PLUGIN_ICON='subway.png'
PLUGIN_PATH='Extensions/Subway'
SETUP_KEY='subway'
USER_AGENT='Enigma2 ' + PLUGIN_NAME + ' plugin (' + PLUGIN_VERSION + ') @oottppxx'
VTS_RE=r'.*//(?P<host>[%a-zA-Z0-9:.-]+)/play/(?P<stream>[0-9]+)\.(ts|m3u8)\?token=(?P<token>[a-zA-Z0-9+/=]+).*'
API_PHP='https://api.thehive.tv'
VAPI_INFO=r'%(PHP)s/users/me' % {'PHP': API_PHP}
TOKEN_PROMPT=r'%(PHP)s/users/token' % {'PHP': API_PHP}
TOKEN_REQ='{"username":"%(USER)s","password":"%(PWD)s"}'
XTS_RE=r'.*//(?P<host>[%a-zA-Z0-9:.-]+)(/live){0,1}/(?P<user>[^/]+)/(?P<pwd>[^/]+)/(?P<stream>[0-9]+).*'
XC_INFO='http://%(HOST)s/player_api.php?username=%(USER)s&password=%(PWD)s&action=user&sub=info'
TIME_FMT='%Y-%m-%d %H:%M:%S'

DEBUG=False
DEBUG_FILE='/tmp/subway-debug.log'
def debug(s):
  if DEBUG:
    f = open(DEBUG_FILE, 'a+')
    f.write(s)
    f.close()


def info(session, text=None, callback=None):
  if text:
    debug('ITEXT: %s' % text)
    TITLE={}
    if title_like:
      TITLE={'simple': True, 'title': PLUGIN_NAME}
    if callback:
      session.openWithCallback(callback, MessageBox, text, type=None, **TITLE)
    else:
      session.open(MessageBox, text, type=None, **TITLE)


def getJsonURL(url, post_data=None, token=None):
  request = urllib2.Request(url)
  request.add_header('User-Agent', USER_AGENT)
  if token:
    request.add_header('Authorization', 'Bearer %s' % token)
  request.add_header('Accept-Encoding', 'gzip')
  if post_data:
    response = urllib2.urlopen(request, data=post_data)
  else:
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
  data = json.loads(data)
  return data


def playTS(session, ts=None, service=None):
  message = ''
  user = ''
  status = ''
  create_date = ''
  create_date_2 = ''
  exp_date = ''
  auth = ''
  is_trial = ''
  active_cons = ''
  max_cons = ''
  formats = ''
  host = ''
  user = ''
  pwd = ''
  ui = {}
  try:
    ts = urllib2.unquote(ts)
  except:
    info(session, 'Malformed Service URL!\n(Can\'t Unquote.)')
    return True
  m = re.match(VTS_RE, ts, re.IGNORECASE)
  if m:
    host = m.group('host')
    stream = int(m.group('stream'))
    token = m.group('token')
    if token == 'BUZZZ':
      user = config.plugins.buzzz.user.value
      pwd = config.plugins.buzzz.pwd.value
      token = getJsonURL(TOKEN_PROMPT, post_data=TOKEN_REQ % {'USER': user, 'PWD': pwd})
      token = str(token.get('token', None))
    if token:
      ui = getJsonURL(VAPI_INFO, token=token)
      debug('%s\n' % str(ui))
#    if ui:
#      text = 'host: %s\n' % host
#      for k in sorted(ui.keys()):
#        text += '%s: %s\n' % (str(k), str(ui.get(k, None)))
#      debug('TEXT: %s' % text)
#      info(session, text=text)
#      return True
  m = re.match(XTS_RE, ts, re.IGNORECASE)
  if m:
    host = m.group('host')
    user = m.group('user')
    pwd = m.group('pwd')
    stream = int(m.group('stream'))
    ui = getJsonURL(XC_INFO % {'HOST': host, 'USER': user, 'PWD': pwd})
    ui = ui.get('user_info', {})
    debug('%s\n' % str(ui))
  if ui:
    host = 'Host: %s, ' % host
    message = ui.get('message', None)
    if not message:
      message = '~'
    message = 'Message: %s\n' % message
    user = 'User: %s\n' % ui.get('username', '~')
    status = 'Status: %s, ' % ui.get('status', '~')
    auth = 'Auth: %s, ' % ui.get('auth', '~')
    enabled = 'Enabled: %s\n' % ui.get('enabled', '~')
    exp_date = ui.get('exp_date', None)
    if exp_date:
      exp_date = 'Expires: %s\n' % time.strftime(TIME_FMT, time.gmtime(int(exp_date)))
    else:
      exp_date = ui.get('expiration', None)
      if exp_date:
        exp_date = 'Expires: %s\n' % time.strftime(TIME_FMT, time.gmtime(int(exp_date)))
      else:
        exp_date = 'Expires: ~\n'
    create_date = ui.get('created_at', None)
    if create_date:
      create_date = 'Created: %s\n' % time.strftime(TIME_FMT, time.gmtime(int(create_date)))
    else:
      create_date = 'Created: ~\n'
    create_date_2 = 'Created/2: %s, ' % ui.get('createdAt', '~')
    update_date = 'Updated: %s\n' % ui.get('updatedAt', '~')
    active_cons = 'Active Cons: %s, ' % ui.get('active_cons', '~')
    max_cons = 'Max Cons: %s, ' % ui.get('max_connections', '~')
    is_trial = 'Trial: %s, ' % ui.get('is_trial', '~')
    pkg = ui.get('package', None)
    if pkg:
      max_cons = 'Max Cons: %s, ' % pkg.get('maxConnections', '~')
      is_trial = 'Trial: %s, ' % pkg.get('trial', '~')
    formats = 'Formats: %s\n' % ui.get('allowed_output_formats', '~')
    text = (host + message
            + user
            + status + auth + enabled
            + exp_date
            + create_date
            + create_date_2 + update_date + is_trial
            + active_cons + max_cons + formats)
    text = str(text)
    debug('TEXT: %s' % text)
    info(session, text=text)
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
  try:
    if playTS(session, ts=ts, service=service_ref):
      return
  except:
    debug('%s\n' % traceback.format_exc())
  info(session, text='Unsupported Stream!')


def Plugins(**kwargs):
  return PluginDescriptor(
      name=PLUGIN_NAME,
      description=PLUGIN_DESC,
      where=PluginDescriptor.WHERE_PLUGINMENU,
      icon=PLUGIN_ICON,
      fnc=main)
