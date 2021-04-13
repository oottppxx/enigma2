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

PLUGIN_VERSION='6.2.0b'
PLUGIN_NAME='RDebrid'
PLUGIN_DESC='Real Debrid PoC'
PLUGIN_ICON='rdebrid.png'
PLUGIN_PATH='Extensions/RDebrid'
if not openatv_like:
  PLUGIN_PATH='/usr/lib/enigma2/python/Plugins/' + PLUGIN_PATH
SETUP_KEY='rdebrid'

HOST='127.0.0.1'
EXTM3U_HEADER='#EXTM3U'
EXTM3U_ENTRY='#EXTINF:-1 tvg-name="%(SDN)s" tvg-id="%(CID)s" tvg-logo="%(PICON)s" group-title="%(CAT)s",%(SDN)s'
API_BASE='https://api.real-debrid.com/rest/1.0'
PAPI_DOWNLOADS=r'%(BASE)s/downloads?auth_token=%(PAPI)s&limit=100&page=%(PAGE)s'
VISIBLE_WIDTH=20
VERSION_DEF=PLUGIN_VERSION
VERSION_CHOICES=[(VERSION_DEF, VERSION_DEF)]
PAPI_DEF=''
PORT_DEF=8268
DEBUG_DEF=False
PAPI=PAPI_DEF
PORT=PORT_DEF
DEBUG=DEBUG_DEF

config.plugins.rdebrid = ConfigSubsection()
config.plugins.rdebrid.papi = ConfigPassword(default=PAPI_DEF, fixed_size=False, visible_width=VISIBLE_WIDTH)
config.plugins.rdebrid.port = ConfigNumber(default=PORT_DEF)
config.plugins.rdebrid.debug = ConfigBoolean(default=DEBUG_DEF)
config.plugins.rdebrid.version = ConfigSelection(default=VERSION_DEF, choices=VERSION_CHOICES)
if not openatv_like:
  SAVED_SETUP=Screens.Setup.setupdom

DEBUG_FILE='/tmp/rdebrid-debug.log'
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
      debug('200!\n')
      data = self.genM3U(token=PAPI)
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

  def genM3U(self, token=None):
    m3u = []
    m3u.append(EXTM3U_HEADER)
    m3u.append('')
    data = []
    page = 1
    while page:
      params = {'BASE': API_BASE, 'PAPI': token, 'PAGE': page}
      new_data = []
      try:
        new_data = self.getJsonURL(PAPI_DOWNLOADS % params)
      except:
        debug('%s\n' % traceback.format_exc())
      if new_data:
        data.extend(new_data)
        page += 1
      else:
        page = 0
    for datum in data:
      id = datum.get('id', '')
      filename = datum.get('filename', '')
      url = datum.get('download', '')
      if id and filename and url:
        m3u.append(EXTM3U_ENTRY % {'ID':id, 'SDN':filename, 'PICON':'', 'CID':'', 'CAT':''})
        m3u.append(url)
    m3u.append('')
    debug('END GENM3U! %s\n' % str(m3u))
    return '\n'.join(m3u)


def reConfig():
  global PAPI
  global PORT
  global DEBUG
  PAPI = urllib2.quote(config.plugins.rdebrid.papi.value)
  PORT = config.plugins.rdebrid.port.value
  if PORT < 1024 or PORT > 65535:
    config.plugins.rdebrid.port._value = PORT_DEF
    PORT = config.plugins.rdebrid.port.value
  DEBUG = config.plugins.rdebrid.debug.value
  config.plugins.rdebrid.save()
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
  print 'rdebrid autostart!'
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
