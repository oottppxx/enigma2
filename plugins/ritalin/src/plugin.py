from __future__ import print_function

openatv_like = True
try:
  # This works in OpenATV (and similar code bases) but fails on OpenPLi.
  # The particular import might not be relevant for the actual plugin.
  from Screens.EpgSelection import SingleEPG
  ADJUST={'adjust': False}
except:
  ADJUST={}
  openatv_like = False
# Quick fix for Vix >= 5.x(?) and OpenBH >= 4.4
try:
  import boxbranding
  if "openvix" in boxbranding.getImageDistro().lower():
    openatv_like = True
  if "openbh" in boxbranding.getImageDistro().lower():
    openatv_like = True
except:
  pass
# Quick fix for OpenVision 11.2(?)
try:
  from Components import SystemInfo
  if "openvision" in SystemInfo.BoxInfo.getItem("distro").lower():
    openatv_like = True
except:
  pass

import time
import traceback

from enigma import iPlayableService

from Components.config import config, configfile, ConfigBoolean, ConfigSelection, ConfigSubsection, ConfigText
from Plugins.Plugin import PluginDescriptor
if openatv_like:
  from Screens.Setup import Setup
else:
  import Screens.Setup
  import xml.etree.cElementTree
#  from Components.config import configfile


PLUGIN_VERSION='6.2.0a'
PLUGIN_NAME='Ritalin'
PLUGIN_DESC='Service Spotting'
PLUGIN_ICON='ritalin.png'
PLUGIN_PATH='Extensions/Ritalin'
if not openatv_like:
  PLUGIN_PATH='/usr/lib/enigma2/python/Plugins/' + PLUGIN_PATH
SETUP_KEY='ritalin'

VERSION_DEF=PLUGIN_VERSION
VERSION_CHOICES=[(VERSION_DEF, VERSION_DEF)]
ENABLE_DEF=True
ENABLE=ENABLE_DEF
DEBUG_ACTIVE_DEF=False
DEBUG_ACTIVE=DEBUG_ACTIVE_DEF

SESSION=None
REGISTERED=False
VISIBLE_WIDTH=20

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
    iPlayableService.evUser: 'evUser',
  }
except:
  EVENT_STRINGS = {
    iPlayableService.evStart: 'evStart',
    iPlayableService.evEOF: 'evEOF',
  }

config.plugins.ritalin = ConfigSubsection()
config.plugins.ritalin.enable = ConfigBoolean(default=ENABLE_DEF)
config.plugins.ritalin.debug = ConfigBoolean(default=DEBUG_ACTIVE_DEF)
config.plugins.ritalin.version = ConfigSelection(default=VERSION_DEF, choices=VERSION_CHOICES)
if not openatv_like:
  SAVED_SETUP=Screens.Setup.setupdom

DEBUG_FILE='/tmp/ritalin-debug.log'

def DEBUG(s):
  if DEBUG_ACTIVE:
    t = time.ctime()
    f = open(DEBUG_FILE, 'a+')
    f.write('%s %s' % (t, s))
    f.close()
    print('%s %s' % (t,s))


def saveService():
  DEBUG('Service saving...\n')
  if SESSION:
    current = SESSION.nav.getCurrentlyPlayingServiceReference()
    if current:
      config.tv.lastservice.value = current.toString()
      config.tv.lastservice.save()
      DEBUG('WARNING: This can stress your flash, as it does one write per zap!!!')
      configfile.save()
      DEBUG('Service %s saved.\n' % current.toString())
    else:
      DEBUG('No service to save!\n')
    return
  DEBUG('Can\'t save service, no session!\n')


def serviceEvent(evt):
  DEBUG('-> %s\n' % EVENT_STRINGS.get(evt, 'UNKNOWN %d' % int(evt)))
  if SESSION:
    if (evt == iPlayableService.evStart):
      DEBUG('  handling...\n')
      if ENABLE:
        saveService()
      else:
        DEBUG('  ignoring: not enabled...\n')
    return
  DEBUG('No session!\n')


def reConfig():
  global ENABLE
  global DEBUG_ACTIVE
  ENABLE = config.plugins.ritalin.enable.value
  DEBUG_ACTIVE = config.plugins.ritalin.debug.value
  config.plugins.ritalin.save()
  if not openatv_like:
    configfile.save()


def onSetupClose(test=None):
  reConfig()
  if not openatv_like:
    Screens.Setup.setupdom = SAVED_SETUP


def autoStart(reason, **kwargs):
  DEBUG('ritalin autostart!\n')
  onSetupClose()


def sessionStart(reason, **kwargs):
  global REGISTERED
  global REC_REGISTERED
  global SESSION
  DEBUG('Session Start called...\n')
  SESSION=kwargs.get('session')
  if SESSION and not REGISTERED:
    DEBUG('  Session valid...\n')
    SESSION.nav.event.append(serviceEvent)
    REGISTERED = True
    DEBUG('  Registered play event watcher...\n')
  DEBUG('Session Start exited...\n')


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
