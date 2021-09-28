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
# Quick fix for Vix
try:
  import boxbranding
  if "openvix" in boxbranding.getImageDistro().lower():
    openatv_like = True
except:
  pass

import re
import time

from enigma import eTimer, iPlayableService, iRecordableService

from Components.config import config, ConfigBoolean, ConfigNumber, ConfigSelection, ConfigSubsection, ConfigText
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import InfoBar
from Screens.ChannelSelection import ChannelSelection
if openatv_like:
  from Screens.Setup import Setup
else:
  import Screens.Setup
  import xml.etree.cElementTree
  from Components.config import configfile


PLUGIN_VERSION='6.2.0o'
PLUGIN_NAME='QuarterPounder'
PLUGIN_DESC='A Tasty Treat 2'
PLUGIN_ICON='quarterpounder.png'
PLUGIN_PATH='Extensions/QuarterPounder'
if not openatv_like:
  PLUGIN_PATH='/usr/lib/enigma2/python/Plugins/' + PLUGIN_PATH
SETUP_KEY='quarterpounder'

VERSION_DEF=PLUGIN_VERSION
VERSION_CHOICES=[(VERSION_DEF, VERSION_DEF)]
ENABLE_DEF=True
ENABLE=ENABLE_DEF
GUI_CHECK_CHANNELS='Channels'
GUI_CHECK_INFOBAR='InfoBar'
GUI_CHECK_ANY='Any'
GUI_CHECK_IGNORE=' (ignore)'
GUI_CHECK_POSTPONE=' (postpone)'
GUI_CHECK_1=GUI_CHECK_CHANNELS+GUI_CHECK_IGNORE
GUI_CHECK_2=GUI_CHECK_CHANNELS+GUI_CHECK_POSTPONE
GUI_CHECK_3=GUI_CHECK_INFOBAR+GUI_CHECK_IGNORE
GUI_CHECK_4=GUI_CHECK_INFOBAR+GUI_CHECK_POSTPONE
GUI_CHECK_5=GUI_CHECK_ANY+GUI_CHECK_IGNORE
GUI_CHECK_6=GUI_CHECK_ANY+GUI_CHECK_POSTPONE
GUI_CHECK_DISABLE='Disable'
GUI_CHECK_DEF=GUI_CHECK_1
GUI_CHECK=GUI_CHECK_DEF
GUI_CHECK_CHOICES=[
    (GUI_CHECK_1, GUI_CHECK_1),
    (GUI_CHECK_2, GUI_CHECK_2),
    (GUI_CHECK_3, GUI_CHECK_3),
    (GUI_CHECK_4, GUI_CHECK_4),
    (GUI_CHECK_5, GUI_CHECK_5),
    (GUI_CHECK_6, GUI_CHECK_6),
    (GUI_CHECK_DISABLE, GUI_CHECK_DISABLE)
]
IGNORE_STRINGS_DEF='mp4,mkv'
IGNORE_STRINGS=IGNORE_STRINGS_DEF
RESTART_DELAY_DEF=0
RESTART_DELAY=RESTART_DELAY_DEF
RESTART_INDICATOR_1='Default'
RESTART_INDICATOR_NONE='None'
RESTART_INDICATOR_DEF=RESTART_INDICATOR_1
RESTART_INDICATOR=RESTART_INDICATOR_DEF
RESTART_INDICATOR_CHOICES=[
    (RESTART_INDICATOR_1, RESTART_INDICATOR_1),
    (RESTART_INDICATOR_NONE, RESTART_INDICATOR_NONE)
]
STUCK_HACK_DEF=''
STUCK_HACK=STUCK_HACK_DEF
STUCK_DELAY_DEF=2500
STUCK_DELAY=STUCK_DELAY_DEF
DEBUG_ACTIVE_DEF=False
DEBUG_ACTIVE=DEBUG_ACTIVE_DEF

SESSION=None
REGISTERED=False
REC_REGISTERED=False
try:
  IGNORE_RE = re.compile(str('|'.join(IGNORE_STRINGS.split(','))), flags=re.IGNORECASE)
except:
  IGNORE_RE=re.compile(str('|'.join(IGNORE_STRINGS_DEF.split(','))), flags=re.IGNORECASE)
RESTART_TIME=0
STUCK_PREVIOUS=None
STUCK_RE=''
STUCK_TIMER=eTimer()
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
  REC_EVENT_STRINGS = {
    iRecordableService.evStart: 'recEvStart',
    iRecordableService.evEnd: 'recEvEnd',
    iRecordableService.evTunedIn: 'recEvTuneIn',
    iRecordableService.evTuneFailed: 'recEvTuneFailed',
    iRecordableService.evRecordRunning: 'recEvRecordRunning',
    iRecordableService.evRecordStopped: 'recEvRecordStopped',
    iRecordableService.evNewProgramInfo: 'recEvNewProgramInfo',
    iRecordableService.evRecordFailed: 'recEvRecordFailed',
    iRecordableService.evRecordWriteError: 'recEvRecordWriteError',
    iRecordableService.evNewEventInfo: 'recEvNewEventInfo',
    iRecordableService.evRecordAborted: 'recEvRecordAborted',
    iRecordableService.evGstRecordEnded: 'recEvGstRecordEnded',
  }
except:
  EVENT_STRINGS = {
    iPlayableService.evStart: 'evStart',
    iPlayableService.evEOF: 'evEOF',
  }
  REC_EVENT_STRINGS = {
    iRecordableService.evStart: 'recEvStart',
    iRecordableService.evEnd: 'recEvEnd',
  }

config.plugins.quarterpounder = ConfigSubsection()
config.plugins.quarterpounder.enable = ConfigBoolean(default=ENABLE_DEF)
config.plugins.quarterpounder.gui_check = ConfigSelection(default=GUI_CHECK_DEF, choices=GUI_CHECK_CHOICES)
config.plugins.quarterpounder.ignore_strings = ConfigText(default=IGNORE_STRINGS_DEF, fixed_size=False, visible_width=VISIBLE_WIDTH)
config.plugins.quarterpounder.restart_delay = ConfigNumber(default=RESTART_DELAY_DEF)
config.plugins.quarterpounder.restart_indicator = ConfigSelection(default=RESTART_INDICATOR_DEF, choices=RESTART_INDICATOR_CHOICES)
config.plugins.quarterpounder.stuck_hack = ConfigText(default=STUCK_HACK_DEF, fixed_size=False, visible_width=VISIBLE_WIDTH)
config.plugins.quarterpounder.stuck_delay = ConfigNumber(default=STUCK_DELAY_DEF)
config.plugins.quarterpounder.debug = ConfigBoolean(default=DEBUG_ACTIVE_DEF)
config.plugins.quarterpounder.version = ConfigSelection(default=VERSION_DEF, choices=VERSION_CHOICES)
if not openatv_like:
  SAVED_SETUP=Screens.Setup.setupdom

DEBUG_FILE='/tmp/quarterpounder-debug.log'

def DEBUG(s):
  if DEBUG_ACTIVE:
    t = time.ctime()
    f = open(DEBUG_FILE, 'a+')
    f.write('%s %s' % (t, s))
    f.close()
    print('%s %s' % (t,s))


def restartService():
  ods = None
  DEBUG('Service restarting...\n')
  if SESSION:
    previous = SESSION.nav.getCurrentlyPlayingServiceReference()
    if previous is None:
      DEBUG('Can\'t restart service, it was correctly stopped!\n')
      return
    if IGNORE_RE.search(previous.toString()):
      DEBUG('Matched ignore strings, ignoring service...\n')
      return
    if GUI_CHECK != GUI_CHECK_DISABLE:
      DEBUG('Dialog Stack: %s\n' % SESSION.dialog_stack)
      DEBUG('Current Dialog: %s, Shown: %s\n' % (SESSION.current_dialog, SESSION.current_dialog.shown))
      bypass_restart = False
      if GUI_CHECK_CHANNELS in GUI_CHECK:
        if isinstance(SESSION.current_dialog, ChannelSelection):
          DEBUG('Channels GUI check, bypassing restart...\n')
          bypass_restart = True
      else:
        for dialog, shown in SESSION.dialog_stack:
          if isinstance(dialog, InfoBar) or GUI_CHECK_ANY in GUI_CHECK:
            DEBUG('InfoBar or Any GUI check, bypassing restart...\n')
            bypass_restart = True
      if bypass_restart:
        if GUI_CHECK_IGNORE in GUI_CHECK:
          DEBUG('GUI interaction detected, ignoring restart...\n')
          return
        else:
          DEBUG('GUI interaction detected, postponing restart...\n')
          STUCK_TIMER.start(1000, True)
          return
    SESSION.nav.stopService()
    DEBUG('Stopped current service, will restart...\n')
    if previous:
      if RESTART_INDICATOR in [PLUGIN_NAME, RESTART_INDICATOR_NONE]:
        DEBUG('Disabling InfoBar on restart...\n')
        ods = InfoBar.instance.doShow
        InfoBar.instance.doShow = lambda:True
      SESSION.nav.playService(previous, **ADJUST)
      if RESTART_INDICATOR in [PLUGIN_NAME, RESTART_INDICATOR_NONE]:
        DEBUG('Enabling InfoBar after restart...\n')
        InfoBar.instance.doShow = ods
      DEBUG('Service %s restarted.\n' % previous.toString())
    else:
      DEBUG('No service to restart!\n')
    return
  DEBUG('Can\'t restart service, no session!\n')


STUCK_TIMER.callback.append(restartService)


def serviceRecEvent(evt):
  EVENT_TIME = int(time.time())
  DEBUG('-> %s\n' % REC_EVENT_STRINGS.get(evt, 'UNKNOWN (REC) %d' % int(evt)))
  if SESSION:
#    if (evt == iPlayableService.evStart):
#      DEBUG('  handling (rec)...\n')
    return
  DEBUG('No session!\n')

def serviceEvent(evt):
  global RESTART_TIME
  global STUCK_PREVIOUS
  EVENT_TIME = int(time.time())
  DEBUG('-> %s\n' % EVENT_STRINGS.get(evt, 'UNKNOWN %d' % int(evt)))
  if SESSION:
    if (evt == iPlayableService.evStart):
      DEBUG('  handling...\n')
      if STUCK_HACK and STUCK_RE:
        previous = STUCK_PREVIOUS
        STUCK_PREVIOUS = SESSION.nav.getCurrentlyPlayingServiceReference().toString()
        if previous != STUCK_PREVIOUS:
          if STUCK_RE.search(STUCK_PREVIOUS):
            DEBUG('  restarting hack...\n')
            STUCK_TIMER.start(STUCK_DELAY, True)
            return
      RESTART_TIME=int(time.time())
      return
    if (evt == iPlayableService.evEOF):
      DEBUG('  handling...\n')
      if ENABLE and ((EVENT_TIME-RESTART_TIME) >= RESTART_DELAY):
        restartService()
      else:
        DEBUG('  Ignoring: not enabled and/or still backing off...\n')
      return
    return
  DEBUG('No session!\n')


def reConfig():
  global ENABLE
  global GUI_CHECK
  global IGNORE_STRINGS
  global IGNORE_RE
  global RESTART_DELAY
  global RESTART_INDICATOR
  global STUCK_HACK
  global STUCK_RE
  global STUCK_DELAY
  global DEBUG_ACTIVE
  ENABLE = config.plugins.quarterpounder.enable.value
  GUI_CHECK = config.plugins.quarterpounder.gui_check.value
  IGNORE_STRINGS = config.plugins.quarterpounder.ignore_strings.value
  if not IGNORE_STRINGS:
    IGNORE_STRINGS = IGNORE_STRINGS_DEF
    config.plugins.quarterpounder.ignore_strings._value = IGNORE_STRINGS_DEF
  try:
    IGNORE_RE = re.compile(str('|'.join(IGNORE_STRINGS.split(','))), flags=re.IGNORECASE)
  except:
    IGNORE_RE=re.compile(str('|'.join(IGNORE_STRINGS_DEF.split(','))), flags=re.IGNORECASE)
    config.plugins.quarterpounder.ignore_strings._value = IGNORE_STRINGS_DEF
  RESTART_DELAY = config.plugins.quarterpounder.restart_delay.value
  RESTART_INDICATOR = config.plugins.quarterpounder.restart_indicator.value
  STUCK_HACK = config.plugins.quarterpounder.stuck_hack.value
  if STUCK_HACK:
    try:
      STUCK_RE = re.compile(str('|'.join(STUCK_HACK.split(','))), flags=re.IGNORECASE)
    except:
      STUCK_RE=''
  STUCK_DELAY = config.plugins.quarterpounder.stuck_delay.value
  DEBUG_ACTIVE = config.plugins.quarterpounder.debug.value
  config.plugins.quarterpounder.save()
  if not openatv_like:
    configfile.save()


def onSetupClose(test=None):
  reConfig()
  if not openatv_like:
    Screens.Setup.setupdom = SAVED_SETUP


def autoStart(reason, **kwargs):
  DEBUG('quarterpounder autostart!\n')
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
    SESSION.nav.event.append(serviceRecEvent)
    REC_REGISTERED = True
    DEBUG('  Registered record event watcher...\n')
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
