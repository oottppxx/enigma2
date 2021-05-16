from __future__ import print_function

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

try:
  from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
except ImportError:
  from http.server import BaseHTTPRequestHandler, HTTPServer
import re
import json
import socket
import threading
import time
import traceback
import urllib
try:
  import urllib2
except ImportError:
  urllib2 = urllib
  urllib.Request = urllib.request.Request
  urllib.urlopen = urllib.request.urlopen
try:
  import urlparse
except ImportError:
  import urllib.parse
  urlparse = urllib.parse
  urllib.unquote = urllib.parse.unquote
import zlib

from Components.config import config, ConfigBoolean, ConfigNumber, ConfigSelection, ConfigSubsection
from Plugins.Plugin import PluginDescriptor
if openatv_like:
  from Screens.Setup import Setup
else:
  import Screens.Setup
  import xml.etree.cElementTree
  from Components.config import configfile


PLUGIN_VERSION='6.2.1m'
PLUGIN_NAME='Frenchs'
PLUGIN_DESC='Mustardy EXTM3U proxy'
PLUGIN_ICON='frenchs.png'
PLUGIN_PATH='Extensions/Frenchs'
if not openatv_like:
  PLUGIN_PATH='/usr/lib/enigma2/python/Plugins/' + PLUGIN_PATH
SETUP_KEY='frenchs'

USER_AGENT='Enigma2 %s (%s) plugin @oottppxx' % (PLUGIN_NAME, PLUGIN_VERSION)
#Default MARKER, used to be ' !!!'
MARKER=''
HOST='127.0.0.1'
API_PHP='https://api.thehive.tv'
TOKEN_PROMPT=r'%(PHP)s/users/token'
TOKEN_REQ='{"username":"%(USER)s","password":"%(PWD)s"}'
VAPI_MATCH=r'thehive\.tv'
VAPI_CAT_PROMPT=r'%(HOST)s/epg/categories'
VAPI_CAT_EPG=r'%(HOST)s/epg/channels?category_id=%(CAT)s&action=get_live_streams&start=99990000000000'
XAPI_EPG_PROMPT=(r'http://%(HOST)s/player_api.php?username=%(USER)s&password=%(PWD)s&'
                  'action=get_live_streams&start=99990000000000')
PORTAL_RE=r' portal-url=".*://(?P<host>[^"]*)"'
VISIBLE_WIDTH=20
VERSION_DEF=PLUGIN_VERSION
VERSION_CHOICES=[(VERSION_DEF, VERSION_DEF)]
PORT_DEF=7290
PORT=PORT_DEF
BUFFER_SIZE_MAX=256
BUFFER_SIZE_DEF=35
BUFFER_SIZE=BUFFER_SIZE_DEF
DEBUG_ACTIVE_DEF=False
DEBUG_ACTIVE=DEBUG_ACTIVE_DEF


config.plugins.frenchs = ConfigSubsection()
config.plugins.frenchs.port = ConfigNumber(default=PORT_DEF)
config.plugins.frenchs.bsize = ConfigNumber(default=BUFFER_SIZE_DEF)
config.plugins.frenchs.debug = ConfigBoolean(default=DEBUG_ACTIVE_DEF)
config.plugins.frenchs.version = ConfigSelection(default=VERSION_DEF, choices=VERSION_CHOICES)
if not openatv_like:
  SAVED_SETUP=Screens.Setup.setupdom

DEBUG_FILE='/tmp/frenchs-debug.log'

def DEBUG(s):
  if DEBUG_ACTIVE:
    f = open(DEBUG_FILE, 'a+')
    f.write(s)
    f.close()
    print(s)

SLEEP_TIME=2
THREAD=None


class HTTPd(threading.Thread):
  def __init__(self):
    DEBUG('Init HTTPd!\n')
    self.httpd = None
    threading.Thread.__init__(self)

  def run(self):
    DEBUG('Run!\n')
    try:
      time.sleep(SLEEP_TIME)
      self.httpd = HTTPServer((HOST, PORT), getHandler)
      self.httpd.serve_forever()
    except:
      DEBUG('Can\'t start server on %d port!\n' % PORT)

  def stop(self):
    DEBUG('STOP!\n')
    if self.httpd:
      self.httpd.socket.shutdown(socket.SHUT_RDWR)
      self.httpd.socket.close()


class getHandler(BaseHTTPRequestHandler):
  wbufsize = BUFFER_SIZE*2**20

  def do_GET(self):
    DEBUG('Do GET!\n')
    try:
      qd = urlparse.parse_qs(urlparse.urlparse(self.path).query)
      urls = qd.get('url', [])
      DEBUG('URL: "%s"\n' % urls)
      if not urls:
        raise Exception('No URL to fetch!')
      marker = urllib.unquote(qd.get('marker', [MARKER])[0])
      DEBUG('Marker: "%s"\n' % marker)
      prefix = urllib.unquote(qd.get('prefix', [''])[0])
      DEBUG('Prefix: %s\n' % prefix)
      vapi = urllib.unquote(qd.get('vapi', [''])[0])
      DEBUG('VAPI: %s\n' % vapi)
      clean = urllib.unquote(qd.get('clean', [''])[0])
      DEBUG('Clean: %s\n' % clean)
      alfa = urllib.unquote(qd.get('alfa', [''])[0])
      DEBUG('Alfa: %s\n' % alfa)
      first = True
      for url in urls:
        try:
          DEBUG('URL: "%s"\n' % url)
          url = urllib.unquote(url)
          DEBUG('URL: "%s"\n' % url)
          m3u = str(self.getURL(url=url, clean=clean))
          DEBUG('M3U length: %s\n' % len(m3u))
        except:
          DEBUG('M3U no data...\n')
          raise Exception('No M3U data!')
        if alfa:
          # This basically assumes a well behaved minimalistic m3u, so YMMV.
          t_m3u = [s.group() for s in re.finditer('#EXTINF[^\n]*\n[^\n]*\n', m3u, flags=re.MULTILINE)]
          t_m3u.sort(key=self.tvgSort)
          m3u = '#EXTM3U\n' + ''.join(t_m3u)
        if marker:
          host, user, pwd, vapi = self.parseOriginalURL(url=url, vapi=vapi)
          DEBUG('h,u,p,v: %s, %s, %s, %s\n' % (host, user, pwd, vapi))
          host = self.portalURL(host=host, m3u=m3u)
          DEBUG('h,u,p,v: %s, %s, %s, %s\n' % (host, user, pwd, vapi))
          channels = self.getCatchupChannels(host=host, user=user, pwd=pwd, vapi=vapi)
          DEBUG('Channels: %s\n' % channels)
          tvg_rep = {}
          eol_rep = {}
          if prefix:
            for c in channels:
              tvg_rep['tvg-name="%s"' % c] = 'tvg-name="%s"' % str(marker+c)
              eol_rep[',%s' % c] = ',%s' % str(marker+c)
          else:
            for c in channels:
              tvg_rep['tvg-name="%s"' % c] = 'tvg-name="%s"' % str(c+marker)
              eol_rep[',%s' % c] = ',%s' % str(c+marker)
          m3u = self.mulReplace(text=m3u, rep_dict={'\r': ''})
          m3u = self.mulReplace(text=m3u, rep_dict=tvg_rep)
          m3u = self.mulReplace(text=m3u, rep_dict=eol_rep, anchor_right=True)
        DEBUG('New M3U length: %s\n' % len(m3u))
        if first:
          DEBUG('200!\n')
          self.send_response(200)
          self.send_header('Content-type', 'text/plain')
          self.end_headers()
          first = False
        try:
          self.wfile.write(m3u)
        except:
          self.wfile.write(bytes(m3u, 'utf8'))
        self.wfile.flush()
    except:
      DEBUG('500!\n')
      DEBUG('%s\n' % traceback.format_exc())
      self.send_response(500)
    self.wfile.flush()
    self.wfile.close()
    return

  def tvgSort(self, element):
    cat = ''
    name = ''
    try:
      cat = re.search(r'group-title="([^"]*)"', element).groups()[0]
    except:
      pass
    try:
      name = re.search(r'tvg-name="([^"]*)"', element).groups()[0]
    except:
      pass
    return cat+name

  def mulReplace(self, text='', rep_dict={}, anchor_left=False, anchor_right=False):
    DEBUG('MUL REPLACE %s\n' % rep_dict)
    if not text:
      return ''
    if not rep_dict:
      return text
    escaped = '|'.join([re.escape(k) for k in sorted(rep_dict,key=len,reverse=True)])
    if anchor_left and anchor_right:
      escaped = '^(' + escaped + ')$'
    elif anchor_left:
      escaped = '^(' + escaped + ')'
    elif anchor_right:
      escaped = '(' + escaped + ')$'
    pattern = re.compile(escaped, flags=re.DOTALL|re.MULTILINE)
    return pattern.sub(lambda x: rep_dict[x.group(0)], text)

  def parseOriginalURL(self, url=None, vapi=False):
    DEBUG('PARSE URL: %s, %s\n' % (url, vapi))
    host = ''
    user = ''
    pwd = ''
    vapi = vapi
    if url:
      r = urlparse.urlparse(url)
      host = r.netloc
      if re.search(VAPI_MATCH, r.netloc):
        DEBUG('VAPI detected, forcing VAPI!\n')
        vapi = True
      if vapi:
        host = API_PHP
      qd = urlparse.parse_qs(r.query)
      user = qd.get('username', [''])[0]
      pwd = qd.get('password', [''])[0]
    return host, user, pwd, vapi

  def portalURL(self, host=None, m3u=None):
    DEBUG('PORTAL URL: %s\n' % host)
    if host is None or m3u is None:
      return host
    m = re.search(PORTAL_RE, m3u)
    if m:
      DEBUG('Portal detected, mutating host!\n')
      host = m.group('host')
    return host

  def getToken(self, user=None, pwd=None):
    token=''
    if user and pwd:
      params = {'PHP': API_PHP, 'USER': user, 'PWD': pwd, 'TOKEN': ''}
      data = json.loads(self.getURL(TOKEN_PROMPT % params, post_data=TOKEN_REQ % params))
      token = str(data.get('token', None))
    return token

  def getCatchupChannels(self, host='', user='', pwd='', vapi=False):
    DEBUG('GET CATCHUP CHANNELS: %s, %s, %s, %s\n' % (host, user, pwd, vapi))
    channels = []
    try:
      if host:
        data = []
        name = 'name'
        if not vapi:
          DEBUG('Using XAPI!\n')
          data = json.loads(self.getURL(XAPI_EPG_PROMPT % {
              'HOST': host, 'USER': user, 'PWD': pwd}))
        else:
          DEBUG('Using VAPI!\n')
          name = 'stream_display_name'
          token = self.getToken(user=user, pwd=pwd)
          if token:
            params = {'HOST': host, 'USER': user, 'PWD': pwd}
            categories = json.loads(self.getURL(
                VAPI_CAT_PROMPT % params, token=token))
            for cat in categories.iterkeys():
              params['CAT'] = str(cat)
              data.extend(json.loads(self.getURL(
                  VAPI_CAT_EPG % params, token=token)))
        if data:
          for d in data:
            if int('0'+str(d.get('tv_archive_duration', ''))):
              n = str(d.get(name, ''))
              if n:
                channels.append(n)
    except:
      DEBUG('Catchup data issue...\n')
      DEBUG('%s\n' % traceback.format_exc())
    return list(set(channels))

  def getURL(self, url=None, clean=None, post_data=None, token=None):
    DEBUG('GET URL: %s\n' % url)
    data = ''
    if url:
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
          try:
            data += res_data
          except:
            data += res_data.decode()
      if clean:
        if isinstance(data, unicode):
          DEBUG('UNICODE->ASCII->UNICODE!\n')
          data = data.encode('ascii', errors='replace').encode('utf8', errors='replace')
          DEBUG('UNICODE->ASCII->UNICODE!\n')
        if isinstance(data, str):
          DEBUG('ASCII<-ASCII->ASCII!\n')
          data = data.decode('ascii', errors='replace').encode('ascii', errors='replace')
          DEBUG('ASCII->UNICODE->ASCII!\n')
      DEBUG('END GETURL!\n')
      return data


def reConfig():
  global PORT
  global BUFFER_SIZE
  global DEBUG_ACTIVE
  PORT = config.plugins.frenchs.port.value
  if PORT < 1024 or PORT > 65535:
    config.plugins.frenchs.port._value = PORT_DEF
    PORT = config.plugins.frenchs.port.value
  BUFFER_SIZE = config.plugins.frenchs.bsize.value
  if BUFFER_SIZE > BUFFER_SIZE_MAX:
    config.plugins.frenchs.bsize._value = BUFFER_SIZE_MAX
    BUFFER_SIZE = BUFFER_SIZE_MAX
  DEBUG_ACTIVE = config.plugins.frenchs.debug.value
  config.plugins.frenchs.save()
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
  print('French\'s autostart!')
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
        pass


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
