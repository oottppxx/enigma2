openatv_like = True
try:
  # This works in OpenATV (and similar code bases) but fails on OpenPLi.
  # The particular import might not be relevant for the actual plugin.
  from Screens.EpgSelection import SingleEPG
  ADJUST={'adjust': False}
except:
  ADJUST={}
  openatv_like = False
# Quick fix for Vix
try:
  import boxbranding
  if "openvix" in boxbranding.getImageDistro().lower():
    openatv_like = True
except:
  pass
# For plugins without using SingleEPG only!
try:
  import boxbranding
  if 'openspa' in boxbranding.getImageDistro().lower():
    openatv_like = True
except:
  pass

import time
import traceback

from Components.config import config, ConfigBoolean, ConfigNumber, ConfigPassword, ConfigSelection, ConfigSubsection, ConfigText
from Plugins.Plugin import PluginDescriptor
if openatv_like:
  from Screens.Setup import Setup
else:
  import Screens.Setup
  import xml.etree.cElementTree
  from Components.config import configfile


PLUGIN_VERSION='6.2.0e'
PLUGIN_NAME='ColaCao'
PLUGIN_DESC='ColaCao en vez de ...'
PLUGIN_ICON='colacao.png'
PLUGIN_PATH='Extensions/ColaCao'
if not openatv_like:
  PLUGIN_PATH='/usr/lib/enigma2/python/Plugins/' + PLUGIN_PATH
SETUP_KEY='colacao'

VERSION_DEF=PLUGIN_VERSION
VERSION_CHOICES=[(VERSION_DEF, VERSION_DEF)]

CCPATH_DEF="/etc/CCcam.cfg"
OSPATH_DEF="/etc/tuxbox/config/oscam.server"
HOST1_DEF=""
PORT1_DEF=0
USER1_DEF=""
PASS1_DEF=""
HOST2_DEF=""
PORT2_DEF=0
USER2_DEF=""
PASS2_DEF=""
CCPATH=CCPATH_DEF
OSPATH=OSPATH_DEF
LINE_CHOICES=[("", "")]
HOST1=HOST1_DEF
PORT1=PORT1_DEF
USER1=USER1_DEF
PASS1=PASS1_DEF
HOST2=HOST2_DEF
PORT2=PORT2_DEF
USER2=USER2_DEF
PASS2=PASS2_DEF

DEBUG_ACTIVE_DEF=False
DEBUG_ACTIVE=DEBUG_ACTIVE_DEF
DEBUG_FILE='/tmp/colacao-debug.log'


def DEBUG(s):
  if DEBUG_ACTIVE:
    t = time.ctime()
    f = open(DEBUG_FILE, 'a+')
    f.write('%s %s' % (t, s))
    f.close()
    print '%s %s' % (t,s)


MIN_PORT=1
MAX_PORT=65535
CLINE='C: %s %d %s %s\n'
OLINE=('[reader]\nlabel = %s\nenable = 1\nprotocol = cccam\n'
       'device = %s,%d\nuser = %s\npassword = %s\n'
       'group = 1\ncccversion = 2.3.0\ncccmaxhops = 2\n'
       'ccckeepalive = 1\n'
       'disablecrccws_only_for = '
       '1802:000000;'
       '1850:000000;'
       '1868:000000;'
       '1884:000000;'
       '0500:030B00,050F00,050F00;'
       '098C:000000;'
       '098D:000000;'
       '09C4:000000'
       '\n\n')

VISIBLE_WIDTH=60

config.plugins.colacao = ConfigSubsection()
config.plugins.colacao.ccpath = ConfigText(default=CCPATH_DEF, fixed_size=False, visible_width=VISIBLE_WIDTH)
config.plugins.colacao.ospath = ConfigText(default=OSPATH_DEF, fixed_size=False, visible_width=VISIBLE_WIDTH)
config.plugins.colacao.line1 = ConfigSelection(default="", choices=LINE_CHOICES)
config.plugins.colacao.host1 = ConfigText(default=HOST1_DEF, fixed_size=False, visible_width=VISIBLE_WIDTH)
config.plugins.colacao.port1 = ConfigNumber(default=PORT1_DEF)
config.plugins.colacao.user1 = ConfigText(default=USER1_DEF, fixed_size=False, visible_width=VISIBLE_WIDTH)
config.plugins.colacao.pass1 = ConfigPassword(default=PASS1_DEF, visible_width=VISIBLE_WIDTH)
config.plugins.colacao.line2 = ConfigSelection(default="", choices=LINE_CHOICES)
config.plugins.colacao.host2 = ConfigText(default=HOST2_DEF, fixed_size=False, visible_width=VISIBLE_WIDTH)
config.plugins.colacao.port2 = ConfigNumber(default=PORT2_DEF)
config.plugins.colacao.user2 = ConfigText(default=USER2_DEF, fixed_size=False, visible_width=VISIBLE_WIDTH)
config.plugins.colacao.pass2 = ConfigPassword(default=PASS2_DEF, visible_width=VISIBLE_WIDTH)
config.plugins.colacao.debug = ConfigBoolean(default=DEBUG_ACTIVE_DEF)
config.plugins.colacao.version = ConfigSelection(default=VERSION_DEF, choices=VERSION_CHOICES)
if not openatv_like:
  SAVED_SETUP=Screens.Setup.setupdom


def reConfig():
  global CCPATH
  global OSPATH
  global HOST1
  global PORT1
  global USER1
  global PASS1
  global HOST2
  global PORT2
  global USER2
  global PASS2
  global DEBUG_ACTIVE

  try:
    CCPATH = str(config.plugins.colacao.ccpath.value)
    OSPATH = str(config.plugins.colacao.ospath.value)
    HOST1 = str(config.plugins.colacao.host1.value)
    PORT1 = config.plugins.colacao.port1.value
    USER1 = str(config.plugins.colacao.user1.value)
    PASS1 = str(config.plugins.colacao.pass1.value)
    HOST2 = str(config.plugins.colacao.host2.value)
    PORT2 = config.plugins.colacao.port2.value
    USER2 = str(config.plugins.colacao.user2.value)
    PASS2 = str(config.plugins.colacao.pass2.value)
    if PORT1 < MIN_PORT or PORT1 > MAX_PORT:
      config.plugins.colacao.port1._value = PORT1_DEF
      PORT1 = config.plugins.innocent.port1.value
    if PORT2 < MIN_PORT or PORT2 > MAX_PORT:
      config.plugins.colacao.port2._value = PORT2_DEF
      PORT2 = config.plugins.innocent.port2.value
    DEBUG_ACTIVE = config.plugins.colacao.debug.value
  except:
    DEBUG('%s\n' % traceback.format_exc())
  config.plugins.colacao.save()
  if not openatv_like:
    configfile.save()
  try:
    CLINES = [] 
    if CCPATH:
      if HOST1 and PORT1 and USER1 and PASS1:
        CLINES.append(CLINE % (HOST1, PORT1, USER1, PASS1))
      if HOST2 and PORT2 and USER2 and PASS2:
        CLINES.append(CLINE % (HOST2, PORT2, USER2, PASS2))
      with open(CCPATH, 'w') as f:
        f.writelines(CLINES)
  except:
    DEBUG('%s\n' % traceback.format_exc())
  try:
    OLINES = []
    if OSPATH:
      if HOST1 and PORT1 and USER1 and PASS1:
        OLINES.append(OLINE % ('line_1', HOST1, PORT1, USER1, PASS1))
      if HOST2 and PORT2 and USER2 and PASS2:
        OLINES.append(OLINE % ('line_2', HOST2, PORT2, USER2, PASS2))
      with open(OSPATH, 'w') as f:
        f.writelines(OLINES)
  except:
    DEBUG('%s\n' % traceback.format_exc())


def onSetupClose(test=None):
  reConfig()
  if not openatv_like:
    Screens.Setup.setupdom = SAVED_SETUP


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
          name=PLUGIN_NAME,
          description=PLUGIN_DESC,
          where=PluginDescriptor.WHERE_PLUGINMENU,
          icon=PLUGIN_ICON,
          fnc=main)]
