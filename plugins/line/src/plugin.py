openatv_like = True
try:
  # This works in OpenATV (and similar code bases) but fails on OpenPLi.
  # The particular import might not be relevant for the actual plugin.
  from Screens.EpgSelection import SingleEPG
  ADJUST={'adjust': False}
except:
  ADJUST={}
  openatv_like = False

import time
import traceback

from enigma import eTimer, iPlayableService

from Components.config import config, ConfigBoolean, ConfigSelection, ConfigSubsection 
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import InfoBar
if openatv_like:
  from Screens.Setup import Setup
else:
  import Screens.Setup
  import xml.etree.cElementTree
  from Components.config import configfile


PLUGIN_VERSION='6.2.1c'
PLUGIN_NAME='Line'
PLUGIN_DESC='Hides & Toggles VBI Line'
PLUGIN_ICON='line.png'
PLUGIN_PATH='Extensions/Line'
if not openatv_like:
  PLUGIN_PATH='/usr/lib/enigma2/python/Plugins/' + PLUGIN_PATH
SETUP_KEY='line'

VERSION_DEF=PLUGIN_VERSION
VERSION_CHOICES=[(VERSION_DEF, VERSION_DEF)]
ENABLE_DEF=True
ENABLE=ENABLE_DEF
IPTV_DEF=False
IPTV=IPTV_DEF
DVBCTS_DEF=True
DVVCTS=DVBCTS_DEF
DEBUG_ACTIVE_DEF=False
DEBUG_ACTIVE=DEBUG_ACTIVE_DEF

SESSION=None
REGISTERED=False
VISIBLE_WIDTH=20

OLD_SHOW=None
CALL_OLD=True
TIMER=None

try:
  EVENT_STRINGS = {
    iPlayableService.evStart: 'evStart',
    iPlayableService.evEnd: 'evEnd',
    iPlayableService.evTunedIn: 'evTunedIn',
    iPlayableService.evTuneFailed: 'evTuneFailed',
    iPlayableService.evUpdatedEventInfo: 'evUpdatedEventInfo',
    iPlayableService.evUpdatedInfo: 'evUpdatedInfo',
    iPlayableService.evNewProgramInfo: 'evNewProgramInfo',
    iPlayableService.evSeekableStatusChanged: 'evSeekableStatusChanged',
    iPlayableService.evEOF: 'evEOF',
    iPlayableService.evSOF: 'evSOF',
    iPlayableService.evCuesheetChanged: 'evCuesheetChanged',
    iPlayableService.evUpdatedRadioText: 'evUpdatedRadioText',
    iPlayableService.evUpdatedRtpText: 'evUpdatedRtpText',
    iPlayableService.evUpdatedRassSlidePic: 'evUpdatedRassSlidePic',
    iPlayableService.evUpdatedRassInteractivePicMask: 'evUpdatedRassInteractivePicMask',
    iPlayableService.evVideoSizeChanged: 'evVideoSizeChanged',
    iPlayableService.evVideoFramerateChanged: 'evVideoFramerateChanged',
    iPlayableService.evVideoProgressiveChanged: 'evVideoProgressiveChanged',
    iPlayableService.evBuffering: 'evBuffering',
    iPlayableService.evGstreamerPlayStarted: 'evGstreamerPlayStarted',
    iPlayableService.evStopped: 'evStopped',
    iPlayableService.evHBBTVInfo: 'evHBBTVInfo',
    iPlayableService.evVideoGammaChanged: 'evVideoGammaChanged',
    iPlayableService.evUser: 'evUser'
  }
except:
  DEBUG('Not OpenATV or similar?\n')
  DEBUG(traceback.format_exc())
  EVENT_STRINGS = {
    iPlayableService.evStart: 'evStart',
    iPlayableService.evEOF: 'evEOF'
  }
  DEBUG('Using alternative strings...\n')

config.plugins.line = ConfigSubsection()
config.plugins.line.enable = ConfigBoolean(default=ENABLE_DEF)
config.plugins.line.iptv = ConfigBoolean(default=IPTV_DEF)
config.plugins.line.dvbcts = ConfigBoolean(default=DVBCTS_DEF)
config.plugins.line.debug = ConfigBoolean(default=DEBUG_ACTIVE_DEF)
config.plugins.line.version = ConfigSelection(default=VERSION_DEF, choices=VERSION_CHOICES)
if not openatv_like:
  SAVED_SETUP=Screens.Setup.setupdom

DEBUG_FILE='/tmp/line-debug.log'

def DEBUG(s):
  if DEBUG_ACTIVE:
    t = time.ctime()
    f = open(DEBUG_FILE, 'a+')
    f.write('%s %s' % (t, s))
    f.close()
    print '%s %s' % (t,s)


def toggleLine():
  DEBUG('Toggle Line...\n')
  try:
    if InfoBar.instance.hideVBILineScreen.shown:
      InfoBar.instance.hideVBILineScreen.hide()
    else:
      OLD_SHOW()
  except:
    DEBUG('  Something went wrong!\n')
    DEBUG(traceback.format_exc())


def iptv(ref):
  for marker in ['://', '%3A//', '%3a//']:
    if marker in ref:
      return True
  return False


def serviceEvent(evt):
  DEBUG('-> %s\n' % EVENT_STRINGS.get(evt, 'UNKNOWN %d' % int(evt)))
  global CALL_OLD
  if SESSION:
    if (evt == iPlayableService.evStart):
      DEBUG('  handling...\n')
      ref = SESSION.nav.getCurrentlyPlayingServiceReference().toString()
      try:
        if iptv(ref):
          DEBUG('  IPTV!\n')
          SETTING = IPTV
        else:
          DEBUG('  DVBCTS!\n')
          SETTING = DVBCTS
        if SETTING:
          DEBUG('  Hiding artifacts, showing coverage!\n')
          OLD_SHOW()
          CALL_OLD=True
        else:
          DEBUG('  Uncovering artifacts, hiding coverage!\n')
          InfoBar.instance.hideVBILineScreen.hide()
          CALL_OLD=False
      except:
        DEBUG('  Something went wrong!\n')
        DEBUG(traceback.format_exc())
    return
  DEBUG('No session!\n')


def reConfig():
  global ENABLE
  global IPTV
  global DVBCTS
  global DEBUG_ACTIVE
  ENABLE = config.plugins.line.enable.value
  IPTV = config.plugins.line.iptv.value
  DVBCTS = config.plugins.line.dvbcts.value
  DEBUG_ACTIVE = config.plugins.line.debug.value
  config.plugins.line.save()
  if not openatv_like:
    configfile.save()


def onSetupClose(test=None):
  reConfig()
  if not openatv_like:
    Screens.Setup.setupdom = SAVED_SETUP


def openSetup(session):
  global SAVED_SETUP
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
        DEBUG('COULDN\'T SAVE SETUP!\n')
        DEBUG(traceback.format_exc())


def fromPluginBrowser(session):
  DEBUG('fromPluginBrowser()\n')
  if session:
    DEBUG('%s\n' % session.dialog_stack)
    if session.dialog_stack:
      DEBUG('Returning true!\n')
      return True
  DEBUG('Returning false!\n')
  return False


def new_show():
  DEBUG('New Show...\n')
  if CALL_OLD and OLD_SHOW:
    DEBUG('  Calling old show!\n')
    OLD_SHOW()


def pollInfoBarInstance():
  DEBUG('Poll info bar!\n')
  global OLD_SHOW
  if InfoBar.instance:
    DEBUG('  Found instance, cancel timer!\n')
    TIMER.stop()
    if not OLD_SHOW:
      DEBUG('  Saving old show() and setting new show()!\n')
      OLD_SHOW = InfoBar.instance.hideVBILineScreen.show
      InfoBar.instance.hideVBILineScreen.show = new_show


def autoStart(reason, **kwargs):
  DEBUG('Auto Start...\n')
  onSetupClose()
  global TIMER
  TIMER = eTimer()
  TIMER.callback.append(pollInfoBarInstance)
  TIMER.start(1000, False)


def sessionStart(reason, **kwargs):
  global REGISTERED
  global SESSION
  DEBUG('Session Start...\n')
  SESSION=kwargs.get('session')
  if SESSION and not REGISTERED:
    DEBUG('  Session valid...\n')
    SESSION.nav.event.append(serviceEvent)
    REGISTERED = True
    DEBUG('  Registered eventwatcher...\n')
  DEBUG('Session Start exited...\n')


def main(session, **kwargs):
  if session:
    reConfig()
    if fromPluginBrowser(session):
      DEBUG('OPENING SETUP!\n')
      openSetup(session)
      return
    DEBUG('Toggle line!\n')
    toggleLine()


def Plugins(**kwargs):
  return [
      PluginDescriptor(
          where=PluginDescriptor.WHERE_AUTOSTART,
          fnc=autoStart),
      PluginDescriptor(
          where=PluginDescriptor.WHERE_SESSIONSTART,
          fnc=sessionStart),
      PluginDescriptor(
          name=PLUGIN_NAME,
          description=PLUGIN_DESC,
          where=PluginDescriptor.WHERE_PLUGINMENU,
          icon=PLUGIN_ICON,
          fnc=main)]
