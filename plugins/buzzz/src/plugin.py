openatv_like = True
try:
  # This works in OpenATV (and similar code bases) but fails on OpenPLi.
  # The particular import might not be relevant for the actual plugin.
  from Screens.EpgSelection import SingleEPG
except:
  openatv_like = False
# Quick fix for Vix
try:
  import boxbranding
  if "openvix" in boxbranding.getImageDistro().lower():
    openatv_like = True
except:
  pass

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import base64
import json
import re
import socket
import time
import threading
import time
import traceback
import urllib2
import zlib

from Components.config import config, ConfigBoolean, ConfigNumber, ConfigPassword, ConfigSelection, ConfigSubsection, ConfigText
from Plugins.Plugin import PluginDescriptor
if openatv_like:
  from Screens.Setup import Setup
else:
  import Screens.Setup
  import xml.etree.cElementTree
  from Components.config import configfile

PLUGIN_VERSION='6.2.0e'
PLUGIN_NAME='Buzzz'
PLUGIN_DESC='The Hive EXTM3U generator'
PLUGIN_ICON='buzzz.png'
PLUGIN_PATH='Extensions/Buzzz'
if not openatv_like:
  PLUGIN_PATH='/usr/lib/enigma2/python/Plugins/' + PLUGIN_PATH
SETUP_KEY='buzzz'

HOST='127.0.0.1'
EXTM3U_HEADER='#EXTM3U'
EXTM3U_ENTRY='#EXTINF:-1 tvg-name="%(SDN)s" tvg-id="%(CID)s" tvg-logo="%(PICON)s" group-title="%(CAT)s",%(SDN)s'
API_PHP='https://api.thehive.tv'
TOKEN_PROMPT=r'%(PHP)s/users/token'
TOKEN_REQ='{"username":"%(USER)s","password":"%(PWD)s"}'
TOKEN=None
TOKEN_REFRESHED_TIME=None
VAPI_CAT_PROMPT=r'%(PHP)s/epg/categories'
VAPI_CAT_EPG=r'%(PHP)s/epg/channels?category_id=%(CAT)s&action=get_live_streams&start=99990000000000'
STREAM_URL='%(PHP)s/play/%(ID)s.%(TYPE)s?token=%(TOKEN)s'
STREAM_URL_STATIC='%s%s'
VISIBLE_WIDTH=20
VERSION_DEF=PLUGIN_VERSION
VERSION_CHOICES=[(VERSION_DEF, VERSION_DEF)]
USER_DEF=''
PWD_DEF=''
TYPE_DEF='m3u8'
TYPE_CHOICES=[('m3u8', 'm3u8'), ('ts', 'ts')]
PORT_DEF=9090
REFRESH_DEF=4
STATIC_DEF=False
DEBUG_DEF=False
USER=USER_DEF
PWD=PWD_DEF
TYPE=TYPE_DEF
PORT=PORT_DEF
REFRESH=REFRESH_DEF
STATIC=STATIC_DEF
DEBUG=DEBUG_DEF

config.plugins.buzzz = ConfigSubsection()
config.plugins.buzzz.user = ConfigText(default=USER_DEF, fixed_size=False, visible_width=VISIBLE_WIDTH)
config.plugins.buzzz.pwd = ConfigPassword(default=PWD_DEF, visible_width=VISIBLE_WIDTH)
config.plugins.buzzz.type = ConfigSelection(default=TYPE_DEF, choices=TYPE_CHOICES)
config.plugins.buzzz.port = ConfigNumber(default=PORT_DEF)
config.plugins.buzzz.refresh = ConfigNumber(default=REFRESH_DEF)
config.plugins.buzzz.static = ConfigBoolean(default=STATIC_DEF)
config.plugins.buzzz.debug = ConfigBoolean(default=DEBUG_DEF)
config.plugins.buzzz.version = ConfigSelection(default=VERSION_DEF, choices=VERSION_CHOICES)
if not openatv_like:
  SAVED_SETUP=Screens.Setup.setupdom

DEBUG_FILE='/tmp/buzzz-debug.log'
def debug(s):
  if DEBUG:
    f = open(DEBUG_FILE, 'a+')
    f.write(s)
    f.close()
    print s

SLEEP_TIME=2
THREAD=None

def Now():
  return int(time.time())


class HTTPd(threading.Thread):
  def __init__(self):
    debug('Init HTTPd!\n')
    self.httpd = None
    threading.Thread.__init__(self)

  def run(self):
    debug('Run!\n')
    try:
      time.sleep(SLEEP_TIME)
      self.httpd = HTTPServer((HOST, PORT), getHandler)
      self.httpd.serve_forever()
    except:
      debug('Can\'t start server on %d port!\n' % PORT)
      debug('%s\n' % traceback.format_exc())

  def stop(self):
    debug('STOP!\n')
    if self.httpd:
      self.httpd.socket.shutdown(socket.SHUT_RDWR)
      self.httpd.socket.close()


class getHandler(BaseHTTPRequestHandler):
  wbufsize=1*2**20

  def do_GET(self):
    debug('Do GET!\n')
    try:
      debug(str(self.headers))
      if STATIC and re.search('BUZZZ', self.path):
        debug('302!\n')
        debug('From %s\n' % self.path)
        new_path = re.sub('BUZZZ', self.getToken(user=USER, pwd=PWD), self.path)
        debug('To %s\n' % new_path)
        location = STREAM_URL_STATIC % (API_PHP, new_path)
        debug(location)
        self.send_response(302)
        self.send_header('Location', location)
        self.end_headers()
        self.wfile.flush()
        self.wfile.close()
        return
      debug('200!\n')
      data = self.genM3U(user=USER, pwd=PWD, type=TYPE)
      self.send_response(200)
      self.send_header('Content-type', 'text/plain')
      self.end_headers()
      self.wfile.write(data)
    except:
      debug('500!\n')
      debug('%s\n' % traceback.format_exc())
      self.send_response(500)
    self.wfile.flush()
    self.wfile.close()
    return

  def getJsonURL(self, url=None, post_data=None, token=None):
    debug('GET URL: %s\n' % url)
    data = ''
    if url:
      request = urllib2.Request(url)
      request.add_header('User-Agent', 'Enigma2 Bouquet Script @oottppxx')
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
      debug('END GETJSONURL!\n')
      return json.loads(data)

  def getToken(self, user=None, pwd=None):
    global TOKEN
    global TOKEN_REFRESHED_TIME
    if not (user and pwd):
      debug('NO TOKEN, NO USER/PWD!\n')
      return ''
    if STATIC and TOKEN and TOKEN_REFRESHED_TIME:
      if TOKEN_REFRESHED_TIME+((REFRESH-1)*60+50)*60 < Now():
        # Cache time has passed, invalidate token.
        debug('INVALIDATE EXPIRED TOKEN!\n')
        TOKEN = ''
    else:
      # Might not be in STATIC mode, invalidate token for sure.
      debug('INVALIDATE TOKEN!\n')
      TOKEN = ''
    if not TOKEN:
      debug('DYNAMIC TOKEN!\n')
      params = {'PHP': API_PHP, 'USER': user, 'PWD': pwd, 'TOKEN': ''}
      data = self.getJsonURL(TOKEN_PROMPT % params, post_data=TOKEN_REQ % params)
      TOKEN = str(data.get('token', None))
      TOKEN_REFRESHED_TIME = Now()
    return TOKEN

  def genM3U(self, user=None, pwd=None, type=None):
    m3u = []
    m3u.append(EXTM3U_HEADER)
    m3u.append('')
    token = self.getToken(user=user, pwd=pwd)
    if token:
      data = []
      params = {'PHP': API_PHP, 'USER': user, 'PWD': pwd, 'TOKEN': token}
      categories = self.getJsonURL(VAPI_CAT_PROMPT % params, token=token)
      for cat in categories.iterkeys():
        params['CAT'] = str(cat)
        data.extend(self.getJsonURL(VAPI_CAT_EPG % params, token=token))
      channels = []
      for channel in data:
        id = str(channel.get('id'))
        sdn = ''
        picon = ''
        cat = ''
        if id:
          sdn = str(channel.get('stream_display_name', ''))
          picon = str(channel.get('stream_icon', ''))
          cid = str(channel.get('channel_id', ''))
          cat = str(channel.get('category_id', ''))
          cat = str(categories[cat])
          channels.append({'PHP': API_PHP, 'ID':id, 'SDN':sdn, 'PICON':picon, 'CID': cid, 'CAT': cat, 'TOKEN': token, 'TYPE': type})
      for c in channels:
        debug('c: %s\n' % str(c))
        m3u.append(EXTM3U_ENTRY % c)
        if STATIC:
          c['TOKEN'] = 'BUZZZ'
          c['PHP'] = 'http://127.0.0.1:%s' % PORT
        m3u.append(STREAM_URL % c)
        m3u.append('')
    debug('END GENM3U! %s\n' % str(m3u))
    return '\n'.join(m3u)


def reConfig():
  global USER
  global PWD
  global TYPE
  global PORT
  global REFRESH
  global STATIC
  global DEBUG
  USER = urllib2.quote(config.plugins.buzzz.user.value)
  PWD = urllib2.quote(config.plugins.buzzz.pwd.value)
  TYPE = config.plugins.buzzz.type.value
  PORT = config.plugins.buzzz.port.value
  if PORT < 1024 or PORT > 65535:
    config.plugins.buzzz.port._value = PORT_DEF
    PORT = config.plugins.buzzz.port.value
  REFRESH = config.plugins.buzzz.refresh.value
  if REFRESH < 1 or REFRESH > 24:
    config.plugins.buzzz.refresh._value = REFRESH_DEF
    REFRESH = config.plugins.buzzz.refresh.value
  STATIC = config.plugins.buzzz.static.value
  DEBUG = config.plugins.buzzz.debug.value
  config.plugins.buzzz.save()
  if not openatv_like:
    configfile.save()


def onSetupClose(test=None):
  global THREAD
  reConfig()
  if THREAD:
    THREAD.stop()
  THREAD=HTTPd()
  THREAD.daemon=True
  THREAD.start()
  if not openatv_like:
    Screens.Setup.setupdom = SAVED_SETUP


def autostart(reason, **kwargs):
  print 'Buzzz autostart!'
  onSetupClose()


def main(session, **kwargs):
  global SAVED_SETUP
  reConfig()
  if session:
    if openatv_like:
      session.openWithCallback(onSetupClose, Setup, setup=SETUP_KEY, plugin=PLUGIN_PATH)
    else:
      try:
        setup_file = file(PLUGIN_PATH + '/setup.xml', 'r')
        new_setupdom = xml.etree.cElementTree.parse(setup_file)
        setup_file.close()
        SAVED_SETUP = Screens.Setup.setupdom
        Screens.Setup.setupdom = new_setupdom
        session.openWithCallback(onSetupClose, Screens.Setup.Setup, SETUP_KEY)
        Screens.Setup.setupdom = SAVED_SETUP
      except:
        debug('%s\n' % traceback.format_exc())


def Plugins(**kwargs):
  return [
      PluginDescriptor(
          where=PluginDescriptor.WHERE_AUTOSTART,
          fnc=autostart),
      PluginDescriptor(
          name=PLUGIN_NAME,
          description=PLUGIN_DESC,
          where=PluginDescriptor.WHERE_PLUGINMENU,
          icon=PLUGIN_ICON,
          fnc=main)]
