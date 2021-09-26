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

SESSION=None

import os
import threading
import traceback

from enigma import eTimer

from Components.config import config, ConfigBoolean, ConfigNumber, ConfigSelection, ConfigSubsection, ConfigText
from Plugins.Plugin import PluginDescriptor
if openatv_like:
  from Screens.Setup import Setup
else:
  import Screens.Setup
  import xml.etree.cElementTree
  from Components.config import configfile


PLUGIN_VERSION='6.2.0g'
PLUGIN_NAME='AutoOff'
PLUGIN_DESC='Stop On Standby'
PLUGIN_ICON='autooff.png'
PLUGIN_PATH='Extensions/AutoOff'
if not openatv_like:
  PLUGIN_PATH='/usr/lib/enigma2/python/Plugins/' + PLUGIN_PATH
SETUP_KEY='autooff'

VISIBLE_WIDTH=40
VERSION_DEF=PLUGIN_VERSION
VERSION_CHOICES=[(VERSION_DEF, VERSION_DEF)]
MIN_POLL_INTERVAL=5
POLL_INTERVAL_DEF=15
PORT_INTERVAL=POLL_INTERVAL_DEF
STOP_DELAY_DEF=0
STOP_DELAY=STOP_DELAY_DEF
RESUME_DEF=True
RESUME=RESUME_DEF
STANDBY_CMD_DEF=''
STANDBY_CMD=STANDBY_CMD_DEF
RESUME_CMD_DEF=''
RESUME_CMD=RESUME_CMD_DEF
BOOT_CMD_DEF=False
BOOT_CMD=BOOT_CMD_DEF
DEBUG_ACTIVE_DEF=False
DEBUG_ACTIVE=DEBUG_ACTIVE_DEF


config.plugins.autooff = ConfigSubsection()
config.plugins.autooff.poll_interval = ConfigNumber(default=POLL_INTERVAL_DEF)
config.plugins.autooff.stop_delay = ConfigNumber(default=STOP_DELAY_DEF)
config.plugins.autooff.resume = ConfigBoolean(default=RESUME_DEF)
config.plugins.autooff.standby_cmd = ConfigText(default=STANDBY_CMD_DEF, fixed_size=False, visible_width=VISIBLE_WIDTH)
config.plugins.autooff.resume_cmd = ConfigText(default=RESUME_CMD_DEF, fixed_size=False, visible_width=VISIBLE_WIDTH)
config.plugins.autooff.boot_cmd = ConfigBoolean(default=BOOT_CMD_DEF)
config.plugins.autooff.debug = ConfigBoolean(default=DEBUG_ACTIVE_DEF)
config.plugins.autooff.version = ConfigSelection(default=VERSION_DEF, choices=VERSION_CHOICES)
if not openatv_like:
  SAVED_SETUP=Screens.Setup.setupdom

DEBUG_FILE='/tmp/autooff-debug.log'

def DEBUG(s):
  if DEBUG_ACTIVE:
    f = open(DEBUG_FILE, 'a+')
    f.write(s)
    f.close()
    print s

SLEEP_TIME=2
THREAD=None


class Poller(threading.Thread):
  def __init__(self):
    DEBUG('Init Poller!\n')
    self.poll_timer = eTimer()
    self.poll_timer.callback.append(self.poll)
    self.stop_timer = eTimer()
    self.stop_timer.callback.append(self.serviceStop)
    self.stopped = False
    self.previous = None
    threading.Thread.__init__(self)

  def run(self):
    DEBUG('Run!\n')
    try:
      DEBUG('Running... %s\n' % SESSION)
      self.poll_timer.start(POLL_INTERVAL*1000, False)
    except:
      DEBUG('%s\n' % traceback.format_exc())

  def stop(self):
    DEBUG('Stopping...\n')
    self.poll_timer.stop()
    DEBUG('STOP!\n')

  def poll(self):
    DEBUG('Polling... %s\n' % SESSION)
    if SESSION:
      try:
        standby = SESSION.screen['Standby'].getBoolean()
      except:
        DEBUG('%s\n' % traceback.format_exc())
        return
      if standby and not self.stopped:
        DEBUG('Stop service timer starting...\n')
        self.stop_timer.start(STOP_DELAY*1000, True)
        return
      if not standby and self.stopped:
        if self.previous and RESUME:
          DEBUG('Resuming service...\n')
          SESSION.nav.playService(self.previous, **ADJUST)
          DEBUG('Service resumed...\n')
        else:
          DEBUG('No service to resume or resume disabled!\n')
        if RESUME_CMD:
          try:
            DEBUG('Resume command exit status: %s\n' % str(os.system(RESUME_CMD)))
          except:
            DEBUG('Error while invoking resume command!\n')
            DEBUG('%s\n' % traceback.format_exc())
        self.stopped = False

  def serviceStop(self):
    DEBUG('Service stopping...\n')
    if SESSION:
      try:
        standby = SESSION.screen['Standby'].getBoolean()
      except:
        DEBUG('%s\n' % traceback.format_exc())
        return
      if standby and not self.stopped:
        if STANDBY_CMD:
          try:
            DEBUG('Standby command exit status: %s\n' % str(os.system(STANDBY_CMD)))
          except:
            DEBUG('Error while invoking standby command!\n')
            DEBUG('%s\n' % traceback.format_exc())
        self.previous = SESSION.nav.getCurrentlyPlayingServiceReference()
        if self.previous:
          DEBUG('Service %s stopping, for real...\n' % self.previous.toString())
          SESSION.nav.stopService()
          DEBUG('Service stopped!\n')
        else:
          DEBUG('No service to stop!\n')
        self.stopped = True
      return
    DEBUG('Can\'t stop service, no session!\n')


def reConfig():
  global POLL_INTERVAL
  global STOP_DELAY
  global RESUME
  global STANDBY_CMD
  global RESUME_CMD
  global BOOT_CMD
  global DEBUG_ACTIVE
  POLL_INTERVAL = config.plugins.autooff.poll_interval.value
  if POLL_INTERVAL < MIN_POLL_INTERVAL:
    config.plugins.autooff.poll_interval._value = MIN_POLL_INTERVAL
    POLL_INTERVAL = config.plugins.autooff.poll_interval.value
  STOP_DELAY = config.plugins.autooff.stop_delay.value
  if STOP_DELAY > (POLL_INTERVAL-MIN_POLL_INTERVAL):
    config.plugins.autooff.stop_delay._value = POLL_INTERVAL-MIN_POLL_INTERVAL
    STOP_DELAY = config.plugins.autooff.stop_delay.value
  RESUME = config.plugins.autooff.resume.value
  STANDBY_CMD = config.plugins.autooff.standby_cmd.value
  RESUME_CMD = config.plugins.autooff.resume_cmd.value
  BOOT_CMD = config.plugins.autooff.boot_cmd.value
  DEBUG_ACTIVE = config.plugins.autooff.debug.value
  config.plugins.autooff.save()
  if not openatv_like:
    configfile.save()


def onSetupClose(test=None):
  global THREAD
  reConfig()
  if THREAD:
    THREAD.stop()
  THREAD=Poller()
  THREAD.daemon=True
  THREAD.start()
  if not openatv_like:
    Screens.Setup.setupdom = SAVED_SETUP


def bootCmd():
  if RESUME_CMD and BOOT_CMD:
    DEBUG('Resume command on GUI (re)start...\n')
    try:
      DEBUG('Resume command exit status: %s\n' % str(os.system(RESUME_CMD)))
    except:
      DEBUG('Error while invoking resume command!\n')
      DEBUG('%s\n' % traceback.format_exc())


def autoStart(reason, **kwargs):
  print 'AutoOff autostart!'
  onSetupClose()


def sessionStart(reason, **kwargs):
  global SESSION
  SESSION=kwargs.get('session')
  bootCmd()


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
