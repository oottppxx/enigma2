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
import cgi
import os
import socket
import threading
import traceback
import time
import xml.etree.cElementTree

from collections import OrderedDict

from Components.config import config, ConfigNumber, ConfigSelection, ConfigSubsection, ConfigText
from Plugins.Plugin import PluginDescriptor
if openatv_like:
  from Screens.Setup import Setup
else:
  import Screens.Setup
  from Components.config import configfile

PLUGIN_VERSION='6.2.1d'
PLUGIN_NAME='MiracleWhip'
PLUGIN_DESC='Suls Remote Config Editor'
PLUGIN_ICON='miraclewhip.png'
PLUGIN_PATH='Extensions/MiracleWhip'
if not openatv_like:
  PLUGIN_PATH='/usr/lib/enigma2/python/Plugins/' + PLUGIN_PATH
SETUP_KEY='miraclewhip'

CSS="""<style>
body {
  background-color: black;
  color: lime; 
  font-family: Lucida Console,Lucida Sans Typewriter,monaco,Bitstream Vera Sans Mono,monospace;
}
hr {
  border-color: lime;
  width: 80%; 
  margin: 1em 0;
}
input[type=text] {
  background-color: black;
  color: lime;
  border: 2px solid lime;
  margin-right: 0.5em;
  font-size: 1em;
  font-family: Lucida Console,Lucida Sans Typewriter,monaco,Bitstream Vera Sans Mono,monospace;
}
input[type=text]:focus {
  width: 80%;
  font-size: 1.5em;
  outline: none;
}
input[type=submit] {
  background-color: lime;
  color: black;
  border: 2px solid lime;
  border-radius: 25px;
  margin: 0.5em 0;
  font-size: 1em;
  font-family: Lucida Console,Lucida Sans Typewriter,monaco,Bitstream Vera Sans Mono,monospace;
}
input[type=submit]:focus {
  outline: none;
  font-size: 1.5em;
}
</style>"""

HOST=''
VISIBLE_WIDTH=20
VERSION_DEF=PLUGIN_VERSION
VERSION_CHOICES=[(VERSION_DEF, VERSION_DEF)]
CONFIG_FILE_DEF='/etc/enigma2/e2m3u2bouquet/config.xml'
PORT_DEF=6677
CONFIG_FILE=CONFIG_FILE_DEF
PORT=PORT_DEF

config.plugins.miraclewhip = ConfigSubsection()
config.plugins.miraclewhip.config = ConfigText(default=CONFIG_FILE_DEF, fixed_size=False, visible_width=VISIBLE_WIDTH)
config.plugins.miraclewhip.port = ConfigNumber(default=PORT_DEF)
config.plugins.miraclewhip.version = ConfigSelection(default=VERSION_DEF, choices=VERSION_CHOICES)
if not openatv_like:
  SAVED_SETUP=Screens.Setup.setupdom

DEBUG_ACTIVE=False
DEBUG_FILE='/tmp/miraclewhip-debug.log'
def DEBUG(s):
  if DEBUG_ACTIVE:
    f = open(DEBUG_FILE, 'a+')
    f.write(s)
    f.close()
    print s

#BACKUP_PATH='/tmp'
BACKUP_PATH='/etc/enigma2/e2m3u2bouquet'
BACKUP_EXT='.whip-%s'
SLEEP_TIME=2
THREAD=None

CONFIG=OrderedDict()


class HTTPd(threading.Thread):
  def __init__(self):
    DEBUG('Init HTTPd!')
    self.httpd = None
    threading.Thread.__init__(self)

  def run(self):
    DEBUG('Run!')
    try:
      time.sleep(SLEEP_TIME)
      self.httpd = HTTPServer((HOST, PORT), requestHandler)
      self.httpd.serve_forever()
    except:
      DEBUG('Can\'t start server on %d port!' % PORT)

  def stop(self):
    DEBUG('STOP!')
    if self.httpd:
      self.httpd.socket.shutdown(socket.SHUT_RDWR)
      self.httpd.socket.close()


class requestHandler(BaseHTTPRequestHandler):
  def do_GET(self):
    DEBUG('Do GET!')
    
    data = self.configWorkCopy()
    if not data:
      DEBUG('GET 500!')
      self.send_response(500)
      return
    else:
      DEBUG('GET 200!')
      self.send_response(200)
      self.send_header('Content-type', 'text/html')
      self.end_headers()
      self.wfile.write(data)
    return

  def do_POST(self):
    if self.path == '/new':
      self.newSub()
      DEBUG('POST NEW 301!')
      self.send_response(301)
      self.send_header('Location', '/')
      self.end_headers()
      return
    elif self.path == '/update':
      self.updateConfig()
      DEBUG('POST UPDATE 301!')
      self.send_response(301)
      self.send_header('Location', '/')
      self.end_headers()
      return
    elif self.path == '/delete':
      try:
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers,
                                environ={'REQUEST_METHOD':'POST', 'CONTENT_TYPE':self.headers['Content-Type']})
        subname = form.getvalue('subname')
      except:
        subname = ''
      CONFIG.pop(subname, None)
      DEBUG('POST DELETE 301!')
      self.send_response(301)
      self.send_header('Location', '/')
      self.end_headers()
      return
    elif self.path == '/rollback':
      self.rollbackWorkCopy()
      DEBUG('POST ROLLBACK 301!')
      self.send_response(301)
      self.send_header('Location', '/')
      self.end_headers()
      return
    elif self.path == '/commit':
      self.commitToFile()
      DEBUG('POST COMMIT 301!')
      self.send_response(301)
      self.send_header('Location', '/')
      self.end_headers()
      return
    DEBUG('POST 500!')
    self.send_response(500)

  def newSub(self):
    global CONFIG
    DEBUG('NEW SUB!')
    CONFIG.pop('?', None)
    CONFIG['?'] = {}

  def commitToFile(self):
    now = time.time()
    xml = self.xmlizeConfig()
    backup_name = os.path.join(BACKUP_PATH, (os.path.basename(CONFIG_FILE)+BACKUP_EXT) % now)
    try:
      os.link(CONFIG_FILE, backup_name)
    except:
      DEBUG(str(traceback.format_exc()))
    try:
      f = open(CONFIG_FILE, 'wb')
      f.write(xml)
      f.close()
    except:
      DEBUG(str(traceback.format_exc()))

  def xmlizeConfig(self):
    xml = []
    xml.append('<config>')
    for subname, sub in CONFIG.iteritems():
      xml.append('  <supplier>')
      xml.append('    <name>%s</name>' % subname)
      xml.append('    <enabled>%s</enabled>' % CONFIG[subname].get('enabled', '1'))
      xml.append('    <settingslevel>%s</settingslevel>' % CONFIG[subname].get('settingslevel', 'expert'))
      xml.append('    <m3uurl><![CDATA[%s]]></m3uurl>' % CONFIG[subname].get('m3uurl', ''))
      xml.append('    <epgurl><![CDATA[%s]]></epgurl>' % CONFIG[subname].get('epgurl', ''))
      xml.append('    <username><![CDATA[%s]]></username>' % CONFIG[subname].get('username', ''))
      xml.append('    <password><![CDATA[%s]]></password>' % CONFIG[subname].get('password', ''))
      xml.append('    <providerupdate><![CDATA[%s]]></providerupdate>' % CONFIG[subname].get('providerupdate', ''))
      xml.append('    <iptvtypes>%s</iptvtypes>' % CONFIG[subname].get('iptvtypes', '0'))
      xml.append('    <streamtypetv>%s</streamtypetv>' % CONFIG[subname].get('streamtypetv', '1'))
      xml.append('    <streamtypevod>%s</streamtypevod>' % CONFIG[subname].get('streamtypevod', '4097'))
      xml.append('    <multivod>%s</multivod>' % CONFIG[subname].get('multivod', '0'))
      xml.append('    <allbouquet>%s</allbouquet>' % CONFIG[subname].get('allbouquet', '0'))
      xml.append('    <picons>%s</picons>' % CONFIG[subname].get('picons', '0'))
      xml.append('    <bouquettop>%s</bouquettop>' % CONFIG[subname].get('bouquettop', '0'))
      xml.append('    <xcludesref>%s</xcludesref>' % CONFIG[subname].get('xcludesref', '0'))
      xml.append('    <bouqueturl><![CDATA[%s]]></bouqueturl>' % CONFIG[subname].get('bouqueturl', ''))
      xml.append('    <bouquetdownload>%s</bouquetdownload>' % CONFIG[subname].get('bouquetdownload', '0'))
      xml.append('  </supplier>')
    xml.append('</config>')
    return '\n'.join(xml)


  def updateConfig(self):
    global CONFIG
    DEBUG('UPDATE CONFIG!')
    try:
      form = cgi.FieldStorage(fp=self.rfile, headers=self.headers,
                              environ={'REQUEST_METHOD':'POST', 'CONTENT_TYPE':self.headers['Content-Type']},
                              keep_blank_values=True) 
      subname = form.getvalue('subname')
    except:
      subname = ''
    DEBUG(str(form))
    DEBUG(str(CONFIG))
    if subname:
      form_keys = form.keys()
      checkboxes = ['enabled', 'settingslevel', 'multivod', 'picons', 'bouquettop',
                    'allbouquet', 'iptvtypes', 'xcludesref', 'bouquetdownload']
      for check in checkboxes:
        if not check in form_keys:
          CONFIG[subname][check] = '0'
      for key in form_keys:
        DEBUG(str(key))
        CONFIG[subname][key] = form.getvalue(key)
      if CONFIG[subname].get('settingslevel', '') == '0':
        CONFIG[subname]['settingslevel'] = 'simple'
      else:
        CONFIG[subname]['settingslevel'] = 'expert'
      if CONFIG[subname].get('bouquettop', '') == '1':
        CONFIG[subname]['bouquettop'] = '1'
      else:
        CONFIG[subname]['bouquettop'] = '0'
    new_name = CONFIG[subname].get('name', '')
    if new_name and subname != new_name:
      CONFIG.pop(new_name, None)
      CONFIG[new_name] = CONFIG[subname]
      CONFIG.pop(subname, None)

  def configWorkCopy(self):
    DEBUG('CONFIG WORK COPY!')
    if not len(CONFIG):
      self.rollbackWorkCopy()
    return '\r\n'.join(self.htmlizeConfig())

  def rollbackWorkCopy(self):
    global CONFIG
    DEBUG('ROLLBACK WORK COPY!')
    suppliers = OrderedDict()
    try:
      tree = xml.etree.cElementTree.ElementTree(file=CONFIG_FILE)
      for node in tree.findall('.//supplier'):
        supplier = {}
        for child in node:
          supplier[child.tag] = '' if child.text is None else child.text.strip()
        if supplier.get('name'):
          suppliers[supplier['name']] = supplier
    except:
      pass
    CONFIG = suppliers

  def htmlizeConfig(self):
    html = []
    html.append('<!DOCTYPE html>')
    html.append('<html>')
    html.append('<head>')
    html.append(CSS)
    html.append('</head>')
    html.append('<body>')
    html.append('<h2>Suls Remote Config Editor</h2>')
    html.append('To edit, on each sub, apply changes with <b>Update Work Copy</b> (or <b>Delete From Work Copy</b>), ONLY THEN <b>Commit To File</b>.<br>')
    html.append('For new subs, first <b>Add New</b> then <b>Update Work Copy</b>, afterwards proceed to edit as before.<br>')
    html.append('<h2>Configured Subs</h2>')
    html.append('<hr>')
    for subname, sub in CONFIG.iteritems():
      html.append('<h2>'+subname+'</h2>')
      sub_fields = self.htmlizeSub(sub=sub)
      sub_fields.append('<input type="hidden" name="subname" value="%s">' % subname)
      html.extend(self.htmlizePost(action='update', value='Update Work Copy', fields=sub_fields))
      html.extend(self.htmlizePost(action='delete', value='Delete %s From Work Copy' % subname,
                                   fields=['<input type="hidden" name="subname" value="%s">' % subname]))
      html.append('<hr>')
    html.extend(self.htmlizePost(action='new', value='Add New'))
    html.extend(self.htmlizePost(action='rollback', value='Rollback From File'))
    html.extend(self.htmlizePost(action='commit', value='Commit To File'))
    html.append('</body>')
    html.append('</html>')
    return html

  def htmlizeSub(self, sub=None):
    html = []
    TEXT_SIZE=60
    if sub:
      html.append('<input type="text" size="%s" name="name" value="%s">Name<br>' % (TEXT_SIZE, sub.get('name', '?')))
      enabled = ''
      if str(sub.get('enabled', '')) == '1':
        enabled = 'checked'
      html.append('<input type="checkbox" name="enabled" value="1" %s>Enabled<br>' % enabled)
      settingslevel = ''
      if str(sub.get('settingslevel', '')) == 'expert':
        settingslevel = 'checked'
      html.append('<input type="checkbox" name="settingslevel" value="1" %s>Settings level expert<br>' % settingslevel)
      html.append('<input type="text" size="%s" name="m3uurl" value="%s">M3U URL<br>' % (TEXT_SIZE, sub.get('m3uurl', '?')))
      html.append('<input type="text" size="%s" name="epgurl" value="%s">EPG URL<br>' % (TEXT_SIZE, sub.get('epgurl', '?')))
      html.append('<input type="text" size="%s" name="username" value="%s">Username<br>' % (TEXT_SIZE, sub.get('username', '?')))
      html.append('<input type="text" size="%s" name="password" value="%s">Password<br>' % (TEXT_SIZE, sub.get('password', '?')))
      multivod = ''
      if str(sub.get('multivod', '')) == '1':
        multivod = 'checked'
      html.append('<input type="checkbox" name="multivod" value="1" %s>Multi VOD<br>' % multivod)
      picons = ''
      if str(sub.get('picons', '')) == '1':
        picons = 'checked'
      html.append('<input type="checkbox" name="picons" value="1" %s>Picons<br>' % picons)
      bouquettop = ''
      if str(sub.get('bouquettop', '')) == '1':
        bouquettop = 'checked'
      html.append('<input type="checkbox" name="bouquettop" value="1" %s>IPTV bouquet top<br>' % bouquettop)
      allbouquet = ''
      if str(sub.get('allbouquet', '')) == '1':
        allbouquet = 'checked'
      html.append('<input type="checkbox" name="allbouquet" value="1" %s>Create all channels bouquet<br>' % allbouquet)
      iptvtypes = ''
      if str(sub.get('iptvtypes', '')) == '1':
        iptvtypes = 'checked'
      html.append('<input type="checkbox" name="iptvtypes" value="1" %s>All IPTV types enable<br>' % iptvtypes)
      html.append('<input type="text" size="%s" name="streamtypetv" value="%s">TV Stream Type<br>' % (TEXT_SIZE, sub.get('streamtypetv', '?')))
      html.append('<input type="text" size="%s" name="streamtypevod" value="%s">VOD Stream Type<br>' % (TEXT_SIZE, sub.get('streamtypevod', '?')))
      xcludesref = ''
      if str(sub.get('xcludesref', '')) == '1':
        xcludesref = 'checked'
      html.append('<input type="checkbox" name="xcludesref" value="1" %s>Override service refs<br>' % xcludesref)
      bouquetdownload = ''
      if str(sub.get('bouquetdownload', '')) == '1':
        bouquetdownload = 'checked'
      html.append('<input type="checkbox" name="bouquetdownload" value="1" %s>Check providers bouquet<br>' % bouquetdownload)
      html.append('<input type="text" size="%s" name="bouqueturl" value="%s">Bouquet URL<br>' % (TEXT_SIZE, sub.get('bouqueturl', '?')))
#      html.append('%s Provider update URL<br>' % str(sub.get('providerupdate', '?')))
    return html

  def htmlizePost(self, action=None, value=None, fields=None):
    html = []
    html.append('<form method="POST" action="/%s">' % action)
    if fields:
      html.extend(fields)
    html.append('<input type="submit" value="%s">' % value)
    html.append('</form>')
    return html


def reConfig():
  global CONFIG_FILE
  global PORT
  CONFIG_FILE = config.plugins.miraclewhip.config.value
  PORT = config.plugins.miraclewhip.port.value
  if PORT < 1024 or PORT > 65535:
    config.plugins.miraclewhip.port._value = PORT_DEF
    PORT = config.plugins.miraclewhip.port.value
  config.plugins.miraclewhip.save()
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
  print 'Miracle autostart!'
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

