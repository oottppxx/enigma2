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
title_like = True
try:
  import inspect
  from Screens.MessageBox import MessageBox
  title_like = 'title' in inspect.getargspec(MessageBox.__init__)[0] 
except:
  title_like = False

import time

from enigma import eServiceReference

from Components.config import config, configfile, ConfigBoolean, ConfigSelection, ConfigSubsection, ConfigText
from Plugins.Plugin import PluginDescriptor
from Screens.ChannelSelection import ChannelSelection, service_types_tv
from Screens.MessageBox import MessageBox
if openatv_like:
  from Screens.Setup import Setup
else:
  import Screens.Setup
  import xml.etree.cElementTree
  from Components.config import configfile

PLUGIN_VERSION='6.2.0c'
PLUGIN_MONIKER='[Lv]'
PLUGIN_NAME='Love'
PLUGIN_DESC='Current2Fav'
PLUGIN_ICON='love.png'
PLUGIN_PATH='Extensions/Love'
if not openatv_like:
  PLUGIN_PATH='/usr/lib/enigma2/python/Plugins/' + PLUGIN_PATH
SETUP_KEY='love'

VERSION_DEF=PLUGIN_VERSION
VERSION_CHOICES=[(VERSION_DEF, VERSION_DEF)]
BOUQUET_DEF='userbouquet.favourites.tv'
BOUQUET=BOUQUET_DEF
SILENT_DEF=False
SILENT=SILENT_DEF
DEBUG_ACTIVE_DEF=False
DEBUG_ACTIVE=DEBUG_ACTIVE_DEF

VISIBLE_WIDTH=40

config.plugins.love = ConfigSubsection()
config.plugins.love.bouquet = ConfigText(default=BOUQUET_DEF, fixed_size=False, visible_width=VISIBLE_WIDTH)
config.plugins.love.silent = ConfigBoolean(default=SILENT_DEF)
config.plugins.love.debug = ConfigBoolean(default=DEBUG_ACTIVE_DEF)
config.plugins.love.version = ConfigSelection(default=VERSION_DEF, choices=VERSION_CHOICES)
if not openatv_like:
  SAVED_SETUP=Screens.Setup.setupdom

DEBUG_FILE='/tmp/love-debug.log'
def DEBUG(s):
  if DEBUG_ACTIVE:
    try:
      t = time.ctime()
      f = open(DEBUG_FILE, 'a+')
      f.write('%s %s' % (t, s))
      f.close()
      print '%s %s' % (t,s)
    except:
      pass

def info(session, text=None, callback=None):
  if session and text:
    if not openatv_like and text[:4] != PLUGIN_MONIKER:
      text = PLUGIN_MONIKER + ' ' + text
    TITLE={}
    if title_like:
      TITLE={'simple': True, 'title': PLUGIN_NAME}
    if callback:
      session.openWithCallback(callback, MessageBox, text, type=None, **TITLE)
    else:
      session.open(MessageBox, text, type=None, **TITLE)

def reConfig():
  global BOUQUET
  global SILENT
  global DEBUG_ACTIVE
  BOUQUET = config.plugins.love.bouquet.value
  SILENT = config.plugins.love.silent.value
  DEBUG_ACTIVE = config.plugins.love.debug.value
  config.plugins.love.save()
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
        pass

def addFavourite(session):
  if session:
    DEBUG('ADDING FAVOURITE!\n')
    try:
      service = session.nav.currentlyPlayingServiceReference
      ref = eServiceReference('%s FROM BOUQUET "%s" ORDER BY bouquet' % (service_types_tv, BOUQUET))
      ChannelSelection.instance.addServiceToBouquet(ref, service)
      if not SILENT:
        info(session, text='Saved Channel!')
    except:
      DEBUG('SOMETHING WRONG!\n')
      try:
        if not SILENT:
          info(session, text='Something Went Wrong!\nBad Bouquet?')
      except:
        DEBUG('SOMETHING VERY WRONG!\n')

def fromPluginBrowser(session):
  if session:
    DEBUG('%s\n' % session.dialog_stack)
    if session.dialog_stack:
      DEBUG('RETURNING TRUE!\n')
      return True
  DEBUG('RETURNING FALSE!\n')
  return False

def main(session, **kwargs):
  if session:
    reConfig()
    if fromPluginBrowser(session):
      DEBUG('OPENING SETUP!\n')
      openSetup(session)
      return
    DEBUG('ADDING FAVOURITE!\n')
    addFavourite(session)

def Plugins(**kwargs):
  return PluginDescriptor(
      name=PLUGIN_NAME,
      description=PLUGIN_DESC,
      where=PluginDescriptor.WHERE_PLUGINMENU,
      icon=PLUGIN_ICON,
      fnc=main)
