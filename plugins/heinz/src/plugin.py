import sys
PY3K = sys.version_info >= (3, 0)

openatv_like = True
openvix = False
try:
  # This works in OpenATV (and similar code bases) but fails on OpenPLi.
  # The particular import might not be relevant for the actual plugin.
  from Screens.EpgSelection import SingleEPG
  ADJUST={'adjust': False}
except:
  from Screens.EpgSelection import EPGSelection
  SingleEPG = EPGSelection
  ADJUST={}
  openatv_like = False
# Quick fix for Vix
try:
  import boxbranding
  if "openvix" in boxbranding.getImageDistro().lower():
    from Screens.EpgSelection import EPGSelection
    SingleEPG = EPGSelection
    openatv_like = True
    openvix = True
except:
  pass
title_like = True
try:
  import inspect
  from Screens.MessageBox import MessageBox
  title_like = 'title' in inspect.getargspec(MessageBox.__init__)[0] 
except:
  title_like = False

import base64
import calendar
import json
import os
import re
import threading
import time
import traceback
try:
  import urllib2
except ImportError:
  import urllib
  import urllib.parse
  urllib.quote = urllib.parse.quote
  urllib.unquote = urllib.parse.unquote
  urllib.Request = urllib.request.Request
  urllib.urlopen = urllib.request.urlopen
  urllib2 = urllib

import zlib

from collections import OrderedDict

#from enigma import eEPGCache, eServiceReference, eTimer
from enigma import eServiceReference, eTimer

from Components.config import config, ConfigBoolean, ConfigNumber, ConfigSelection, ConfigSelectionNumber, ConfigSubsection, ConfigText
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.EpgList import EPGList, EPG_TYPE_SINGLE
from Components.Slider import Slider
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
#from Screens.EpgSelection import SingleEPG
from Screens.InfoBar import InfoBar
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
if openatv_like:
  from Screens.Setup import Setup
else:
  import Screens.Setup
  import xml.etree.cElementTree
  from Components.config import configfile


PLUGIN_VERSION='6.2.2x'
PLUGIN_MONIKER='[Hz]'
PLUGIN_NAME='Heinz'
PLUGIN_DESC='Poor man\'s "ketchup"'
PLUGIN_ICON='heinz.png'
PLUGIN_PATH='Extensions/Heinz'
if not openatv_like:
  PLUGIN_PATH='/usr/lib/enigma2/python/Plugins/' + PLUGIN_PATH
SETUP_KEY='heinz'

USER_AGENT='Enigma2 %s (%s) plugin @oottppxx' % (PLUGIN_NAME, PLUGIN_VERSION)
API_PHP='https://api.thehive.tv'
BUZZZ_TOKEN_PROMPT=r'%(PHP)s/users/token'
BUZZZ_TOKEN_REQ='{"username":"%(USER)s","password":"%(PWD)s"}'
BUZZZ_TOKEN=None
BUZZZ_TOKEN_REFRESHED_TIME=None
VAPI_CAT_PROMPT=r'%(UHOST)s/epg/categories'
VAPI_CAT_EPG=(r'%(UHOST)s/epg/channels?category_id=%(CAT)s&action=get_live_streams'
               '&start=99990000000000')
VAPI_EPG_GET=(r'%(UHOST)s/epg/channels?category_id=%(CAT)s&action=get_live_streams'
               '&start=%(START)s&end=%(END)s')
VTS_RE=r'.*(?P<host>http[^/]*//[%a-zA-Z0-9:.-]+)/play/(?P<stream>[0-9]+)\.(ts|m3u8)\?token=(?P<token>[a-zA-Z0-9+/=]+).*'
VCU_RE=(r'(?P<ptype>1|4097|5001|5002):0:1:0:0:0:0:0:0:0:(?P<host>http[^/]*//[%a-zA-Z0-9:.-]+)/play/dvr/'
         '(?P<start>[%a-zA-Z0-9:.-]+)/(?P<stream>[0-9]+)\.(?P<ctype>ts|m3u8)\?'
         'token=(?P<token>[a-zA-Z0-9+/=]+)&duration=(?P<duration>[0-9]+):(?P<sdn>.*)')
VCU_FMT=(r'%(PTYPE)s:0:1:0:0:0:0:0:0:0:%(QHOST)s/play/dvr/'
          '%(START)s/%(STREAM)s.%(CTYPE)s?'
          'token=%(TOKEN)s&duration=%(DURATION)s:%(SDN)s')
XTS_RE=r'.*(?P<host>http[^/]*//[%a-zA-Z0-9:.-]+)(/live){0,1}/(?P<user>[^/]+)/(?P<pwd>[^/]+)/(?P<stream>[0-9]+).*'
XAPI_EPG_PROMPT=(r'%(UHOST)s/player_api.php?username=%(USER)s&password=%(PWD)s&'
                  'action=get_live_streams&start=99990000000000')
XAPI_EPG_GET=(r'%(UHOST)s/player_api.php?username=%(USER)s&password=%(PWD)s&'
               'action=get_simple_data_table&stream_id=%(STREAM)s')
XCU_RE_OLD=(r'(?P<ptype>1|4097|5001|5002):0:1:0:0:0:0:0:0:0:(?P<host>http[^/]*//[%a-zA-Z0-9:.-]+)/streaming/timeshift.php\?'
             'username=(?P<user>[^/]+)&password=(?P<pwd>[^/]+)&'
             'stream=(?P<stream>[0-9]+)&start=(?P<start>[%a-zA-Z0-9:.-]+)&'
             'duration=(?P<duration>[0-9]+):(?P<sdn>.*)')
XCU_FMT_OLD=(r'%(PTYPE)s:0:1:0:0:0:0:0:0:0:%(QHOST)s/streaming/timeshift.php?'
              'username=%(USER)s&password=%(PWD)s&stream=%(STREAM)s&'
              'start=%(START)s&duration=%(DURATION)s:%(SDN)s')
XCU_RE_NEW=(r'(?P<ptype>1|4097|5001|5002):0:1:0:0:0:0:0:0:0:(?P<host>http[^/]*//[%a-zA-Z0-9:.-]+)/timeshift'
             '/(?P<user>[^/]+)/(?P<pwd>[^/]+)'
             '/(?P<duration>[0-9]+)/(?P<start>[%a-zA-Z0-9:.-]+)'
             '/(?P<stream>[0-9]+).(?P<ctype>ts|m3u8):(?P<sdn>.*)')
XCU_FMT_NEW=(r'%(PTYPE)s:0:1:0:0:0:0:0:0:0:%(QHOST)s/timeshift'
              '/%(USER)s/%(PWD)s/%(DURATION)s'
              '/%(START)s/%(STREAM)s.%(CTYPE)s:%(SDN)s')
XCU_RE=XCU_RE_OLD
XCU_FMT=XCU_FMT_OLD
DAY_SECONDS=24*60*60
STEP_TIMER_MS=250
TAIL_EXTRA_MINUTES_DEF=60
HEAD_EXTRA_MINUTES_DEF=10
RELOAD_OFFSET_MINUTES_DEF=2
SUPPORT_CACHE_INTERVAL_MINUTES_DEF=1440
EPG_CACHE_INTERVAL_MINUTES_DEF=15
PTYPE_DEF='4097'
PTYPE_CHOICES=[('1', 'DVB'), ('4097', 'IPTV'), ('5001', 'GSTREAMER'), ('5002', 'EXTPLAYER')]
CTYPE_DEF='m3u8'
CTYPE_CHOICES=[('ts', 'ts'), ('m3u8', 'm3u8')]
LOOKBACK_DEF=3
NEW_XCAPI_DEF=False
GENERATE_CURRENT_DEF=True
NUMERIC_SKIPS_DEF=True
STOP_AT_CURRENT_DEF=True
TIMELINE_SMOOTHNESS_DEF=17
INACTIVE_TIMER_SECONDS_DEF=5
FORCE_LOOKUP_DEF=False
LPO_MIN=-360
LPO_MAX=360
LO_STEP=30
PO_STEP=1
LPO_WRAP=True
LIST_OFFSET_DEF=0
PLAY_OFFSET_DEF=0
REC_TAIL_EXTRA_MINUTES_DEF=5
REC_HEAD_EXTRA_MINUTES_DEF=5
REC_DELAY_SECONDS_DEF=60
REC_DELAY_SECONDS_MIN=1
REC_CMD_DEF=('/usr/bin/ffmpeg -y -i \'URL\' -t DURATION -vcodec copy -acodec copy -f mp4 /media/hdd/movie/downloading.mp4'
             ' </dev/null >/dev/null 2>&1'
             ' && mv /media/hdd/movie/downloading.mp4 /media/hdd/movie/\'FILE\''
             ' >/dev/null 2>&1'
             ' && wget -O- -q \'http://localhost/web/message?text=FILE%0aDownload+Completed!&type=2&timeout=5\'')
DEBUG_DEF=False
RQUEUE_MAX=6
VISIBLE_WIDTH=40
VERSION_DEF=PLUGIN_VERSION
VERSION_CHOICES=[(VERSION_DEF, VERSION_DEF)]
TAIL_EXTRA_MINUTES=TAIL_EXTRA_MINUTES_DEF
HEAD_EXTRA_MINUTES=HEAD_EXTRA_MINUTES_DEF
RELOAD_OFFSET_MINUTES=RELOAD_OFFSET_MINUTES_DEF
SUPPORT_CACHE_INTERVAL_MINUTES=SUPPORT_CACHE_INTERVAL_MINUTES_DEF
EPG_CACHE_INTERVAL_MINUTES=EPG_CACHE_INTERVAL_MINUTES_DEF
PTYPE=PTYPE_DEF
CTYPE=CTYPE_DEF
LOOKBACK=LOOKBACK_DEF
NEW_XCAPI=NEW_XCAPI_DEF
GENERATE_CURRENT=GENERATE_CURRENT_DEF
STOP_AT_CURRENT=STOP_AT_CURRENT_DEF
NUMERIC_SKIPS=NUMERIC_SKIPS_DEF
TIMELINE_SMOOTHNESS=TIMELINE_SMOOTHNESS_DEF
INACTIVE_TIMER_SECONDS=INACTIVE_TIMER_SECONDS_DEF
FORCE_LOOKUP=FORCE_LOOKUP_DEF
LIST_OFFSET=LIST_OFFSET_DEF
PLAY_OFFSET=PLAY_OFFSET_DEF
REC_TAIL_EXTRA_MINUTES=REC_TAIL_EXTRA_MINUTES_DEF
REC_HEAD_EXTRA_MINUTES=REC_HEAD_EXTRA_MINUTES_DEF
REC_DELAY_SECONDS=REC_DELAY_SECONDS_DEF
REC_CMD=REC_CMD_DEF
DEBUG=DEBUG_DEF

config.plugins.heinz = ConfigSubsection()
config.plugins.heinz.tail_extra = ConfigNumber(default=TAIL_EXTRA_MINUTES_DEF)
config.plugins.heinz.head_extra = ConfigNumber(default=HEAD_EXTRA_MINUTES_DEF)
config.plugins.heinz.reload_offset = ConfigNumber(default=RELOAD_OFFSET_MINUTES_DEF)
config.plugins.heinz.support_cache_interval = ConfigNumber(default=SUPPORT_CACHE_INTERVAL_MINUTES_DEF)
config.plugins.heinz.epg_cache_interval = ConfigNumber(default=EPG_CACHE_INTERVAL_MINUTES_DEF)
config.plugins.heinz.ptype = ConfigSelection(default=PTYPE_DEF, choices=PTYPE_CHOICES)
config.plugins.heinz.ctype = ConfigSelection(default=CTYPE_DEF, choices=CTYPE_CHOICES)
config.plugins.heinz.lookback = ConfigNumber(default=LOOKBACK_DEF)
config.plugins.heinz.new_xcapi = ConfigBoolean(default=NEW_XCAPI_DEF)
config.plugins.heinz.generate_current = ConfigBoolean(default=GENERATE_CURRENT_DEF)
config.plugins.heinz.stopat_current = ConfigBoolean(default=STOP_AT_CURRENT_DEF)
config.plugins.heinz.numeric_skips = ConfigBoolean(default=NUMERIC_SKIPS_DEF)
config.plugins.heinz.timeline_smoothness = ConfigNumber(default=TIMELINE_SMOOTHNESS_DEF)
config.plugins.heinz.inactive_timer = ConfigNumber(default=INACTIVE_TIMER_SECONDS_DEF)
config.plugins.heinz.force_lookup = ConfigBoolean(default=FORCE_LOOKUP_DEF)
config.plugins.heinz.list_offset = ConfigSelectionNumber(default=LIST_OFFSET_DEF, min=LPO_MIN, max=LPO_MAX, stepwidth=LO_STEP, wraparound=LPO_WRAP)
config.plugins.heinz.play_offset = ConfigSelectionNumber(default=PLAY_OFFSET_DEF, min=LPO_MIN, max=LPO_MAX, stepwidth=PO_STEP, wraparound=LPO_WRAP)
config.plugins.heinz.rec_tail_extra = ConfigNumber(default=REC_TAIL_EXTRA_MINUTES_DEF)
config.plugins.heinz.rec_head_extra = ConfigNumber(default=REC_HEAD_EXTRA_MINUTES_DEF)
config.plugins.heinz.rec_delay = ConfigNumber(default=REC_DELAY_SECONDS_DEF)
config.plugins.heinz.rec_cmd = ConfigText(default=REC_CMD_DEF, fixed_size=False, visible_width=VISIBLE_WIDTH)
config.plugins.heinz.version = ConfigSelection(default=VERSION_DEF, choices=VERSION_CHOICES)
config.plugins.heinz.debug = ConfigBoolean(default=DEBUG_DEF)
if not openatv_like:
  SAVED_SETUP=Screens.Setup.setupdom

E_TIME_FMT='%Y-%m-%dT%H:%M:%S+00:00'
VEPG_TIME_FMT='%Y%m%d%H%M%S'
XEPG_TIME_FMT='%Y-%m-%d %H:%M:%S'
XCU_TIME_FMT='%Y-%m-%d%%3a%H-%M'
INFO_TIME_FMT='%Y/%m/%d, %H:%M'

DEBUG_FILE='/tmp/heinz-debug.log'
def debug(s):
  if DEBUG:
    try:
      f = open(DEBUG_FILE, 'a+')
      f.write(s)
      f.close()
    except:
      pass


URL_FILE='/tmp/heinz-url.log'
def logURL(s):
  try:
    f = open(URL_FILE, 'a+')
    f.write(s)
    f.close()
  except:
    debug(traceback.format_exc())


class State(object):
  _inst = None
  def __new__(cls):
    if State._inst is None:
      State._inst = object.__new__(cls)
      State._inst.session = None
      State._inst.cu_service = None
      State._inst.previous_service = None
      State._inst.vtype = True
      State._inst.paused = False
      State._inst.host = ''
      State._inst.user = ''
      State._inst.pwd = ''
      State._inst.token = ''
      State._inst.stream = ''
      State._inst.real_start = 0
      State._inst.real_duration = 0
      State._inst.watch_start = 0
      State._inst.program_title = ''
      State._inst.program_info = ''
      State._inst.cache_key = {}
      State._inst.cache_data = {}
      State._inst.data_lock = threading.Lock()
      State._inst.thread_lock = threading.Lock()
      State._inst.thread = None
      State._inst.rqueue = OrderedDict()
    return State._inst
S=State()


def Now():
  return int(time.time())


def eventTimeToEpoch(event_time):
  return int(calendar.timegm(time.strptime(event_time, E_TIME_FMT)))


def epochTimeToEvent(epoch_time):
  return time.strftime(E_TIME_FMT, time.gmtime(epoch_time))


def cuTimeToEpoch(cu_time):
  return int(calendar.timegm(time.strptime(cu_time, XCU_TIME_FMT)))


def epochTimeToCU(epoch_time):
  if S.vtype:
    return epoch_time
  return time.strftime(XCU_TIME_FMT, time.gmtime(epoch_time))


def epochTimeToEPG(epoch_time):
  return time.strftime(VEPG_TIME_FMT, time.gmtime(epoch_time))


def epochTimeToInfo(epoch_time):
  return time.strftime(INFO_TIME_FMT, time.gmtime(epoch_time))


def xEPGToEpoch(xepg_time):
  return int(calendar.timegm(time.strptime(xepg_time, XEPG_TIME_FMT)))


def epochTimeToXEPG(epoch_time):
  return time.strftime(XEPG_TIME_FMT, time.gmtime(epoch_time))

def hmDuration(seconds):
  minutes = int(seconds/60)
  hours = int(seconds/3600)
  if hours:
    minutes %= 60
    if minutes:
      return '%sh%sm' % (hours, minutes)
    else:
      return '%sh' % hours
  else:
    return '%sm' % minutes


def info(session, text=None, callback=None):
  if text:
    if not openatv_like and text[:4] != PLUGIN_MONIKER:
      text = PLUGIN_MONIKER + ' ' + text
    TITLE={}
    if title_like:
      TITLE={'simple': True, 'title': PLUGIN_NAME}
    if callback:
      session.openWithCallback(callback, MessageBox, text, type=None, **TITLE)
    else:
      session.open(MessageBox, text, type=None, **TITLE)


class myMessageBox(MessageBox):
  def __init__(self, session=None, text=None, type=None, simple=False, timeout=-1, timeout_callback=None,
               title=None, service=None, ok_actions=None, remap_ok_actions=None):
    TITLE={}
    if title_like:
      TITLE={'simple': True, 'title': title}
    MessageBox.__init__(self, session=session, text=text, type=type, timeout=timeout, **TITLE)
    self.service=service
    self.session=session
    self.timeout_callback = timeout_callback
    if ok_actions:
      self['actions'].contexts.extend(ok_actions[0])
      for a in ok_actions[1]:
        self['actions'].actions[a] = self.ok
    if remap_ok_actions:
      for a in remap_ok_actions:
        self['actions'].actions[a] = self.ok
    self.text = str(self.__dict__)

  def timeoutCallback(self):
    if self.timeout_callback:
      self.timeout_callback(session=self.session, service=self.service)
    self.close(True)

  # OpenViX doesn't have timeoutCallback hook, improvise :-)
  def stopTimer(self, reason=None):
    if reason is None:
      MessageBox.stopTimer(self)
    else:
      MessageBox.stopTimer(self, reason)
      if reason == 'Timeout!' and self.timeout_callback:
        self.timeout_callback(session=self.session, service=self.service)


def myInfo(session, text=None, callback=None, timeout=-1, timeout_callback=None, service=None,
           ok_actions=None, remap_ok_actions=None):
  if text:
    if not openatv_like and text[:4] != PLUGIN_MONIKER:
      text = PLUGIN_MONIKER + ' ' + text
    if callback:
      session.openWithCallback(callback, myMessageBox, text, type=None, simple=True, timeout=timeout,
                               timeout_callback=timeout_callback, title=PLUGIN_NAME, service=service,
                               ok_actions=ok_actions, remap_ok_actions=remap_ok_actions)
    else:
      session.open(myMessageBox, text, type=None, simple=True, timeout=timeout,
                   timeout_callback=timeout_callback, title=PLUGIN_NAME, service=service,
                   ok_actions=ok_actions, remap_ok_actions=remap_ok_actions)
  

def getBuzzzToken():
  global BUZZZ_TOKEN
  global BUZZZ_TOKEN_REFRESHED_TIME
  user = ''
  pwd = ''
  refresh = 0
  try:
    c = config.plugins.buzzz.content.stored_values
    user = urllib2.quote(c.get('user', ''))
    pwd = urllib2.quote(c.get('pwd', ''))
    refresh = int(c.get('refresh', 0))
    debug('bu/bp/br: %s/%s/%s\n' % (user, pwd, refresh))
  except:
    debug(traceback.format_exc())
    BUZZZ_TOKEN = ''
  if BUZZZ_TOKEN and BUZZZ_TOKEN_REFRESHED_TIME:
    if BUZZZ_TOKEN_REFRESHED_TIME+((refresh-1)*60+50)*60 < Now():
      # Cache time has passed, invalidate token.
      debug('INVALIDATE EXPIRED TOKEN!\n')
      BUZZZ_TOKEN = ''
  if not BUZZZ_TOKEN and refresh:
    debug('DYNAMIC BUZZZ TOKEN!\n')
    try:
      params = {'PHP': API_PHP, 'USER': user, 'PWD': pwd, 'TOKEN': ''}
      data = getJsonURL(BUZZZ_TOKEN_PROMPT % params, post_data=BUZZZ_TOKEN_REQ % params)
      BUZZZ_TOKEN = str(data.get('token', None))
      BUZZZ_TOKEN_REFRESHED_TIME = Now()
    except:
      debug(traceback.format_exc())
      BUZZZ_TOKEN = ''
  debug('token: %s\n' % BUZZZ_TOKEN)
  return BUZZZ_TOKEN


def getJsonURL(url, key=None, timestamp=None, cache=None, fondle_new=None,
               post_data=None, token=None):
  if not key:
    key = url+str(timestamp)
  else:
    key = key+str(timestamp)
  debug('k: %s + %s\n' % (url, str(timestamp)))
  if timestamp and cache and key == S.cache_key.get(cache, None):
    return S.cache_data.get(cache, None)
  request = urllib2.Request(url)
  request.add_header('User-Agent', USER_AGENT)
  if token:
    if token == 'BUZZZ':
      token = getBuzzzToken()
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
      decomp_data = dec_obj.decompress(res_data)
      if PY3K:
        decomp_data = decomp_data.decode('cp437')
      data += decomp_data
    else:
      try:
        data += res_data
      except:
        data += res_data.decode()
  data = json.loads(data)
  if timestamp and cache:
    S.cache_key[cache] = key
    S.cache_data[cache] = data
  if fondle_new:
    fondle_new(data)
  return data


def uncoverVBILine():
  #
  # Note: this is a workaround, a proper fix would set the
  # would be much better done by making sur ethe sHideVBI
  # flag of the service isn't set.
  # See:
  # enigma2/lib/service/iservice.h
  # enigma2/lib/service/servicedvb.cpp
  #
  try:
    # To uncover the VBI line,
    # we have to hide the screen that potentially covers it.
    InfoBar.instance.hideVBILineScreen.hide()
  except:
    debug(traceback.format_exc())


class OnlineEPG(object):
  def __init__(self, host=None, user=None, pwd=None, stream=None):
    self.events = []
    self.qhost = host
    self.uhost = urllib2.unquote(host)
    self.user = user
    self.pwd = pwd
    self.stream = stream
    self.cat = None
    self.days = 0
    self.sdn = ''
    self.params = {'QHOST': self.qhost, 'UHOST': self.uhost, 'USER': self.user, 'PWD': self.pwd, 'STREAM': self.stream}

  def checkSupport(self):
    if SUPPORT_CACHE_INTERVAL_MINUTES:
      timestamp = int(Now()/(SUPPORT_CACHE_INTERVAL_MINUTES*60))
    else:
      timestamp = None
    epg = []
    if S.vtype:
      self.params['UHOST'] = API_PHP
      categories = getJsonURL(VAPI_CAT_PROMPT % self.params, timestamp=timestamp, cache='VCAT',
                              fondle_new=None, token=S.token)
      for cat in categories.iterkeys():
        self.params['CAT'] = str(cat)
        epg.extend(getJsonURL(VAPI_CAT_EPG % self.params, timestamp=timestamp, cache=str('VECAT'+str(cat)),
                              fondle_new=None, token=S.token))
    else:
      epg = getJsonURL(XAPI_EPG_PROMPT % self.params, timestamp=timestamp, cache=str(self.uhost+'XSUP'), fondle_new=None)
    now = Now()
    sid = 'id'
    sdn = 'stream_display_name'
    if not S.vtype:
      sid = 'stream_id'
      sdn = 'name'
    debug('Self stream: %s\n' % self.stream)
    for e in epg:
      debug('Epg ID: %s\n' % e[sid])
      if str(e[sid]) == str(self.stream):
        self.cat = str(e['category_id'])
        self.sdn = str(e[sdn])
        self.days = int('0'+str(e.get('tv_archive_duration', '')))
        if not self.days and FORCE_LOOKUP:
          self.days = LOOKBACK
        if S.vtype and self.days:
# Fuck XXXXXX folks always breaking shit...
# tv_archive_duration is no longer days but seconds
# although it doesn't match shit and some still have zero (Alibi)
# so no point with trying to optimize for it.
# and (self.days < LOOKBACK):
          self.days = LOOKBACK
        debug('Self cat: %s, days: %d\n' % (self.cat, self.days))
        if self.cat is not None and self.days > 0:
          debug('Setting RSDN...\n')
          self.params['CAT'] = self.cat
          self.params['SDN'] = self.sdn
          self.params['RSDN'] = self.sdn
          start = now - self.days*DAY_SECONDS
          self.params['START'] = epochTimeToEPG(start)
          self.params['END'] = epochTimeToEPG(now)
          return True
        return False
    return False

  def getEpg(self):
    if EPG_CACHE_INTERVAL_MINUTES:
      timestamp = int(Now()/(EPG_CACHE_INTERVAL_MINUTES*60))
    else:
      timestamp = None
    if S.vtype:
      self.params['UHOST'] = API_PHP
      epg = getJsonURL(VAPI_EPG_GET % self.params, key=str(self.cat), timestamp=timestamp, cache='VEPG',
                       token=S.token)
      for e in epg:
        if e['id'] == self.stream:
          for p in e['programs']:
            self.buildEvent(program=p)
          return
      return
    epg = getJsonURL(XAPI_EPG_GET % self.params, key=str(self.stream), timestamp=timestamp, cache=str(self.uhost+'XEPG'))
    with_current = False
    for e in epg['epg_listings']:
      if int(e['now_playing']) == 0:
        self.buildEvent(program=e)
      else:
        if GENERATE_CURRENT:
          self.buildEvent(program=e)
          with_current = True
        if STOP_AT_CURRENT:
          break
    if GENERATE_CURRENT and not with_current:
      # Generate our own _fake'ish_ current event here
      pass

  def fakeEPG(self):
    hour_3_seconds = 60*60*3 # 3 hour period in seconds
    now = int(Now()/(60*60)*(60*60)) # round to hour
    hour_3 = LOOKBACK*12 # 3 hour periods
    while hour_3:
      fake_time = now - hour_3 * hour_3_seconds
      program = {}
      program['title'] = 'No EPG: %s' % epochTimeToInfo(fake_time)
      program['desc'] = 'No EPG information provided!'
      if S.vtype:
        program['start'] = epochTimeToEvent(fake_time)
        program['stop'] = epochTimeToEvent(fake_time + hour_3_seconds)
      else:
        if PY3K and isinstance(program['title'], str):
          program['title'] = base64.b64encode(program['title'].encode('cp437'))
          program['description'] = base64.b64encode(program['desc'].encode('cp437'))
        else:
          program['title'] = base64.b64encode(program['title'])
          program['description'] = base64.b64encode(program['desc'])
        program['start_timestamp'] = fake_time
        program['stop_timestamp'] = fake_time + hour_3_seconds
        program['start'] = epochTimeToXEPG(fake_time)
      self.buildEvent(program=program)
      hour_3 -= 1

  def buildEvent(self, program=None):
    if program:
      debug('PROGRAM: %s\n' % str(program))
      if S.vtype:
        title = str(program['title'])
        desc = str(program['desc'])
        start = eventTimeToEpoch(str(program['start']))
        stop = eventTimeToEpoch(str(program['stop']))
        self.params['TOKEN'] = S.token
      else:
        title = base64.b64decode(program['title'])
        desc = base64.b64decode(program['description'])
        if isinstance(title, bytes):
          title = title.decode('cp437')
        if isinstance(desc, bytes):
          desc = desc.decode('cp437')
        title = str(title)
        desc = str(desc)
        start = int(program['start_timestamp'])
        stop = int(program['stop_timestamp'])
        tstart = xEPGToEpoch(str(program['start']))
        offset = tstart - start
        start += offset
        stop += offset
      original_duration = (stop-start)
      duration = original_duration + TAIL_EXTRA_MINUTES*60
      self.params['PTYPE'] = PTYPE
      self.params['CTYPE'] = CTYPE
      self.params['START'] = epochTimeToCU(start+PLAY_OFFSET*60)
      self.params['DURATION'] = duration
      self.params['SDN'] = '%s %s' % (PLUGIN_MONIKER, self.params['RSDN'])
      real_start = start+PLAY_OFFSET*60
      real_duration = duration
      stream = ''
      if S.vtype:
        stream = VCU_FMT % self.params
      else:
        if NEW_XCAPI:
          self.params['DURATION'] = int(duration/60)
          self.params['CTYPE'] = CTYPE
        stream = XCU_FMT % self.params
      self.events.append((stream,
          {'DESC': desc, 'RS': real_start, 'RD': real_duration, 'OD': original_duration, 'PT': title},
          start+LIST_OFFSET*60, duration, title))
      debug('APPENDED EVENT STREAM [ %s ]\n' % stream)

  def data(self):
    error = ''
    try:
      if not self.checkSupport():
        return error, self.events
    except:
      debug(traceback.format_exc())
      error = 'Matching But Unsupported Stream!\n(Transient Error Or Unsupported Provider?)'
      debug('SUP Exception! %(STREAM)s@%(UHOST)s' % self.params)
      return error, self.events
    try:
      self.getEpg()
    except:
      debug(traceback.format_exc())
      error = 'Unable To Retrieve EPG For Stream!\n(Transient Error?)'
      debug('EPG Exception! %(STREAM)s@%(UHOST)s' % self.params)
      return error, self.events
    if not self.events:
#      error = 'No EPG Events For Stream!\n(Transient Error?)'
      debug('Empty EPG! %(STREAM)s@%(UHOST)s' % self.params)
#      return error, self.events
      self.fakeEPG()
    debug('DATA: %s, %s\n' % (str(error), str(self.events)))
    return error, self.events


class myEvent(object):
  def __init__(self, index=None, epg=None):
    self.index = index
    self.epg = epg

  def getEventId(self):
    if self.index:
      return self.index
    return 0

  def getEventName(self):
    if self.epg:
      return self.epg[self.index][4]
    return ''

  def getBeginTime(self):
    if self.epg:
      return self.epg[self.index][2]
    return 0

  def getBeginTimeString(self):
    if self.epg:
      return str(self.epg[self.index][2])
    return '0'

  def getDuration(self):
    if self.epg:
      return self.epg[self.index][3]
    return 0

  def getShortDescription(self):
    return ''

  def getExtendedDescription(self):
    if self.epg:
      return self.epg[self.index][1]['DESC']
    return ''

  def getParentalData(self):
    return None

  def getGenreData(self):
    return None


class myEPGList(EPGList):
  def __init__(self, type=EPG_TYPE_SINGLE, selChangedCB=None, timer=None,
               time_epoch=120, overjump_empty=False, graphic=False, epg=None):
    if openatv_like:
      EPGList.__init__(self, type=type, selChangedCB=selChangedCB, timer=timer,
                       time_epoch=time_epoch, overjump_empty=overjump_empty, graphic=graphic)
    else:
      EPGList.__init__(self, type=type, selChangedCB=selChangedCB, timer=timer)
      self.skinAttributes = []
    if epg:
      self.list = epg
    else:
      self.list = []

  def getCurrentIndex(self):
    # Same as OpenATV def, so no "if openatv_like:"
    return self.instance.getCurrentIndex()

  def setCurrentIndex(self, index):
    # Same as OpenATV def, so no "if openatv_like:"
    if self.instance is not None:
      self.instance.moveSelectionTo(index)

  def fillSingleEPG(self, service):
    self.l.setList(self.list)
    self.instance.moveSelectionTo(len(self.list)-1)
    self.selectionChanged()

  # OpenVix quirks
  def fillEPG(self, service):
    self.fillSingleEPG(service)

  def getEventFromId(self, service=None, eventid=None):
    return myEvent(index=self.getCurrentIndex(), epg=self.list)

  def getExtra(self):
    if self.list:
      return self.list[self.getCurrentIndex()][1]
    else:
      return {'DESC': '', 'RS': 0, 'RD': 0, 'OD': 0, 'PT': ''}


class processRQueue(threading.Thread):
  def __init__(self):
    debug('Init processRQueue!\n') 
    threading.Thread.__init__(self)
    self.cmd = None
    self.timer = eTimer()
    self.timer.callback.append(self.unblock)

  def run(self):
    debug('processRQueue run!\n')
    while True:
      debug('processRQueue loop!\n')
      S.thread_lock.acquire()
      self.timer.start(REC_DELAY_SECONDS*1000, True)
      debug('processRQueue blocking at %s!\n' % str(Now()))
      S.thread_lock.acquire()
      debug('processRQueue unblocking at %s!\n' % str(Now()))
      try:
        S.data_lock.acquire()
        _, cmd = S.rqueue.popitem(last=False)
      except:
        cmd = ''
        debug('processRQueue stop!\n')
        S.thread = None
        S.data_lock.release()
        S.thread_lock.release()
        break
      else:
        S.data_lock.release()
      try:
        debug('processRQueue running %s!\n' % cmd)
        if cmd:
          cmd_status = os.system(cmd)
          debug('processRQueue status %s!\n' % str(cmd_status))
#          if cmd_status:
#            name_change = '.hzfail'
#          else:
#            name_change = ''
#          debug('processRQueue name_change %s!\n' % name_change)
#          fname = ''
#          m = re.match('.*[ =](?<fname>[0-9a-zA-Z/]*\.hzdownload).*')
#          debug('processRQueue fname %s!\n' % fname)
#          if m:
#            fname = m.group('fname')
#            new_name = re.sub('.hzdownload', name_change, fname)
#            debug('processRQueue new_name %s!\n' % new_name)
#            if fname:
#              os.rename(fname, new_name)
      except:
        debug(traceback.format_exc())
      S.thread_lock.release()

  def unblock(self):
    debug('processRQueue unblock!\n')
    S.thread_lock.release()


#class myButton(Button):
#  # Modified from OpenATV 6.0
#  def setText(self, text):
#    if not self.message:
#      try:
#        self.message = text
#        if self.instance:
#          self.instance.setText(self.message or '')
#      except:
#        debug(traceback.format_exc())
#        self.message = ''
#        self.instance.setText(self.message or '')


def vixService(service):
  if openvix and isinstance(service, eServiceReference):
      return service.toString()
  return service


class mySingleEPG(SingleEPG):
  def __init__(self, session, service, EPGtype='single', epg=None):
    overjump_value = None
    if openatv_like:
      SingleEPG.__init__(self, session, service=vixService(service), EPGtype=EPGtype)
      overjump_value = config.epgselection.overjump.value
    else:
      SingleEPG.__init__(self, session, service=service)
    if openvix:
      self.type = EPG_TYPE_SINGLE
    self.skinName = "EPGSelection"
    self.setTitle(PLUGIN_NAME)
    self['list'] = myEPGList(
        type=self.type, selChangedCB=self.onSelectionChanged,
        timer=session.nav.RecordTimer, time_epoch=None,
        overjump_empty=overjump_value, graphic=False, epg=epg)
    self['key_red'] = Button('Queue/Dequeue')
    self['key_green'] = Button('')
    self['key_yellow'] = Button('Log URL')
    self['key_blue'] = Button('Display Queue')
    self.session = session

  def OK(self):
    service_event, service_ref = self['list'].getCurrent()
    extra_info = self['list'].getExtra()
    S.real_start = extra_info['RS']
    S.real_duration = extra_info['RD']
    S.original_duration = extra_info['OD']
    S.program_title = extra_info['PT']
    S.program_info = extra_info['DESC']
    S.watch_start = Now()
# Needs eServiceReferenceDVB, not eServiceReference?
#    epg = eEPGCache.getInstance()
#    epg.submitEventData((service_ref,), S.watch_start, S.real_duration, S.program_title, S.program_info, S.program_info, 1)
    S.cu_service = service_ref.ref.toString()
    debug('Pre now playing CU: %s\n' % S.cu_service)
    S.cu_service = S.cu_service.rsplit(':', 1)[0] + ':' + PLUGIN_MONIKER + ' ' + S.program_title
    debug('Now playing CU: %s\n' % S.cu_service)
    self.session.nav.playService(eServiceReference(S.cu_service), **ADJUST)
    uncoverVBILine()
    if openatv_like:
      self.closeEventViewDialog()
    self.close(True)
  
  # OpenPLi OK key assignment
  def eventSelected(self):
    self.OK()

  def createSetup(self):
    global SAVED_SETUP
    if openatv_like:
      self.closeEventViewDialog()
    if openatv_like:
      self.session.openWithCallback(self.onSetupClose, Setup, setup=SETUP_KEY, plugin=PLUGIN_PATH)
    else:
      try:
        setup_file = file(PLUGIN_PATH + '/setup.xml', 'r')
        new_setupdom = xml.etree.cElementTree.parse(setup_file)
        setup_file.close()
        SAVED_SETUP = Screens.Setup.setupdom
        Screens.Setup.setupdom = new_setupdom
        self.session.openWithCallback(self.onSetupClose, Screens.Setup.Setup, SETUP_KEY)
        Screens.Setup.setupdom = SAVED_SETUP
      except:
        pass

  # OpenPLi menu key assignment 
  def furtherOptions(self):
    self.createSetup()

  # VTi menu key assignment
  def menuClicked(self):
    self.createSetup()

  def onSetupClose(self, test=None):
    self.close(True)

  def recButtonPressed(self):
    service_event, service_ref = self['list'].getCurrent()
    extra_info = self['list'].getExtra()
#    record('%s ::: %s ::: %s\n' % (extra_info['PT'], epochTimeToInfo(int(extra_info['RS'])), service_ref.ref.toString()))
    url = urllib2.unquote(re.sub('.*http', 'http', re.sub(':[^:]*$', '', service_ref.ref.toString())))
    debug('URL: %s\n' % url)
    pt = extra_info['PT']
    rd = 'duration=%s' % str(extra_info['RD'])
    od = extra_info['OD']
    debug('OD: %s\n' % str(od))
    rs = extra_info['RS']
    rscu = str(epochTimeToCU(rs))
    rsi = epochTimeToInfo(rs)
    rs = str(epochTimeToCU(rs - REC_HEAD_EXTRA_MINUTES*60))
    url = re.sub(rscu, rs, url)
    duration = str(int((od/60+REC_HEAD_EXTRA_MINUTES+REC_TAIL_EXTRA_MINUTES)*60))
    url = re.sub(rd, 'duration=%s' % duration, url)
    k = '%s (%s)' % (pt, rsi)
    fname = re.sub('__', '_', re.sub('[^a-zA-Z0-9-]', '_', re.sub('/', '-', '%s %s' % (pt, rsi)))) + '.mp4'
    cmd = re.sub('URL', url, re.sub('DURATION', duration, re.sub('FILE', fname, REC_CMD)))
    debug('CMD: %s\n' % cmd)
    S.data_lock.acquire()
    if len(S.rqueue.keys()) >= RQUEUE_MAX:
      msg = 'Sorry, Too Many Events To Queue!\nTry The Pro Version.'
    else:
      if k in S.rqueue.keys():
        S.rqueue.pop(k, None)
        msg = '%s\nRemoved From Recording Queue!' % k 
      else:
        S.rqueue[k] = cmd
        msg = '%s\nAdded To Recording Queue!\n(At Least %s Second(s) To Start)' % (k, REC_DELAY_SECONDS)
        if not S.thread:
          S.thread = processRQueue()
          S.thread.daemon = True
          S.thread.start()
    S.data_lock.release()
    myInfo(self.session, msg)

  def redButtonPressed(self):
    self.recButtonPressed()

  def redButtonPressedLong(self):
    self.recButtonPressed()

  # OpenPLi red key assignment
  def zapTo(self):
    self.recButtonPressed()

  def setTimerButtonText(self, text=None):
    return

  def greenButtonPressed(self):
    return

  def greenButtonPressedLong(self):
    self.greenButtonPressed()

  def yellowButtonPressed(self):
    service_event, service_ref = self['list'].getCurrent()
    url = urllib2.unquote(re.sub('.*http', 'http', re.sub(':[^:]*$', '', service_ref.ref.toString())))+'\n'
    extra_info = self['list'].getExtra()
    extra = '%s, %s\n' % (extra_info['PT'], epochTimeToInfo(int(extra_info['RS'])))
    logURL('### ' + extra + url)
    msg = extra + url + 'Logged To %s\n(Includes %s Tail Extra Minutes But No Head Extra!)' % (URL_FILE, str(TAIL_EXTRA_MINUTES))
    myInfo(self.session, msg)

  def yellowButtonPressedLong(self):
    self.yellowButtonPressed()

  def blueButtonPressed(self):
    S.data_lock.acquire()
    k = '\n'.join(S.rqueue.keys())
    S.data_lock.release()
    if not k:
      k = 'Empty!'
    msg = 'Recording Queue\n\n%s' % k
    myInfo(self.session, msg)

  def blueButtonPressedLong(self):
    self.blueButtonPressed()

def playTS(session, ts=None, service=None):
  debug('PLAYTS()\n')
  S.previous_service = service
#  try:
#    ts = urllib2.unquote(ts)
#  except:
#    debug(traceback.format_exc())
#    info(session, 'Malformed Service URL!\n(Can\'t Unquote.)')
#    return True
  debug('CS: [ %s ]\n' % ts)
  m = re.match(VTS_RE, ts, re.IGNORECASE)
  if m:
    debug('MATCHED VTS_RE\n')
    S.vtype = True
    S.host = m.group('host')
    S.stream = int(m.group('stream'))
    S.token = m.group('token')
    error, epg = OnlineEPG(host=S.host, user=S.user, pwd=S.pwd, stream=S.stream).data()
    debug('ONLINE_EPG_RET: %s, %s\n' % (str(error), str(epg)))
    if not error and not epg:
      info(session, text='No Ketchup For You!\n(This Stream Doesn\'t Support It.)')
      debug('No Ketchup for %s@%s!' % (S.stream, urllib2.unquote(S.host)))
    elif error:
      info(session, text=error)
    else:
#      session.open(mySingleEPG, service=service, epg=epg)
      session.openWithCallback(adjustCUCallback, mySingleEPG, service=service, epg=epg)
    return True
  m = re.match(XTS_RE, ts, re.IGNORECASE)
  if m:
    debug('MATCHED XTS_RE\n')
    S.vtype = False
    S.host = m.group('host')
    S.user = m.group('user')
    S.pwd = m.group('pwd')
    S.stream = int(m.group('stream'))
    error, epg = OnlineEPG(host=S.host, user=S.user, pwd=S.pwd, stream=S.stream).data()
    debug('ONLINE_EPG_RET: %s, %s\n' % (str(error), str(epg)))
    if not error and not epg:
      info(session, text='No Ketchup For You!\n(This Stream Doesn\'t Support It.)')
      debug('No Ketchup for %s@%s!' % (S.stream, urllib2.unquote(S.host)))
    elif error:
      info(session, text=error)
    else:
#      session.open(mySingleEPG, service=service, epg=epg)
      session.openWithCallback(adjustCUCallback, mySingleEPG, service=service, epg=epg)
    return True
  debug('DID NOT MATCH [VX]TS_RE\n')
  return False


def adjustCUCallback(*ret):
  debug('ADJUSTCUCALLBACK()\n')
  adjustCU(session=S.session, ts=S.cu_service)


def adjustCU(session, ts=None):
  debug('ADJUSTCU()\n')
  if not session or not ts:
    return False
  params = {}
  debug('CS: [ %s ]\n' % ts)
  m = re.match(VCU_RE, ts)
  if m:
    debug('MATCHED VCU_RE\n')
    params['TOKEN'] = m.group('token')
    params['CTYPE'] = m.group('ctype')
    S.vtype = True
  else:
    m = re.match(XCU_RE, ts)
    if m:
      debug('MATCHED XCU_RE\n')
      params['USER'] = m.group('user')
      params['PWD'] = m.group('pwd')
      S.vtype = False
  if m:
    params['PTYPE'] = m.group('ptype')
    params['QHOST'] = m.group('host')
    params['UHOST'] = urllib2.unquote(m.group('host'))
    params['STREAM'] = m.group('stream')
# Adjust S.program_title, as we could have exited
# 2 catchups and then resumed the first one.
    params['START'] = m.group('start')
    if S.vtype:
      S.real_start = int(params['START'])
    else:
      S.real_start = cuTimeToEpoch(params['START'])
    S.watch_start = Now()
    params['DURATION'] = m.group('duration')
    if NEW_XCAPI:
      params['DURATION'] = str(int(m.group('duration'))*60)
      params['CTYPE'] = CTYPE
    S.real_duration = int(params['DURATION'])
    S.original_duration = S.real_duration
    S.program_title = m.group('sdn')
    params['SDN'] = S.program_title
    session.open(CUSelectionScreen, title=S.program_title, params=params)
    return True
  debug('DID NOT MATCH [VX]CU_RE\n')
  return False


class CUSelectionScreen(Screen):
  skin = """<screen position="center,center" size="50%,75">
            <widget source="myText" render="Label" position="25,5" size="e-50,50" font="Regular;25"/>
            <widget name="mySlider" position="25,40" size="e-50,25" borderWidth="2"/>
            </screen>"""
  def __init__(self, session, title=None, params=None):
    self.session = session
    Screen.__init__(self, session)
    if title:
      Screen.setTitle(self, title=urllib2.unquote(title))
    self.params = params
    self.min = -HEAD_EXTRA_MINUTES
    self.max = int(S.real_duration/60)
    elapsed = int((Now() - S.watch_start)/60)
    elapsed = min(self.max, elapsed)
    self.cur = max(self.min, elapsed)
    debug('SLIDER INIT: %s\n' % str(self.max))
    self.slider = Slider(0, self.max)
    self.step = 1
    self.changed = False
    self['myText'] = StaticText('')
    self['mySlider'] = self.slider
    self['myActionMap'] = ActionMap(['HeinzTimelineActions'],
        {
          'one': self.one,
          'two': self.two,
          'three': self.three,
          'four': self.four,
          'five': self.five,
          'six': self.six,
          'seven': self.seven,
          'eight': self.eight,
          'nine': self.nine,
          'zero': self.zero,
          'exit': self.cancel,
          'left': self.rewind,
          'right': self.forward,
          'info': self.info,
          'pause': self.pause,
          'stop': self.stop,
          'ok': self.ok,
          'red': uncoverVBILine,
       }, -1)
    self.stepTimer = eTimer()
    self.updateTimer = eTimer()
    self.updateTimer.callback.append(self.update)
    self.updateTimer.start(1, True)
    self.inactiveTimer = eTimer()
    if INACTIVE_TIMER_SECONDS:
      self.inactiveTimer.callback.append(self.cancel)
      self.inactiveTimer.start(INACTIVE_TIMER_SECONDS*1000, True)
    
  def update(self):
    if not self.changed:
      elapsed = int((Now() - S.watch_start)/60)
      elapsed = min(self.max, elapsed)
      self.cur = max(self.min, elapsed)
    self['myText'].setText('%d .. %d (~)' % (self.cur, self.max))
    self.slider.setValue(max(0, self.cur))

  def stepAdvance(self):
    if self.stepTimer.isActive():
      self.step += self.step
      if TIMELINE_SMOOTHNESS:
        self.step = int(min(self.max/TIMELINE_SMOOTHNESS, self.step))
      else:
        self.step = min(self.max, self.step)
      self.step = max(1, self.step)
    else:
      self.step = 1
    self.stepTimer.start(STEP_TIMER_MS, True)
    return self.step

  def cancel(self):
#    self.close()
    self.hide()
    elapsed = int((Now() - S.watch_start)/60)
    elapsed = min(self.max, elapsed)
    self.cur = max(self.min, elapsed)
    self.changed = False

  def skipBackward(self, n=0):
    self.update()
    self.show()
    self.changed = True
    if self.cur > self.min:
      self.cur -= n
      self.cur = max(self.min, self.cur)
      self.update()
    if INACTIVE_TIMER_SECONDS:
      self.inactiveTimer.start(INACTIVE_TIMER_SECONDS*1000, True)

  def skipForward(self, n=0):
    self.update()
    self.show()
    self.changed = True
    if self.cur < self.max:
      self.cur += n
      self.cur = min(self.max, self.cur)
      self.update()
    if INACTIVE_TIMER_SECONDS:
      self.inactiveTimer.start(INACTIVE_TIMER_SECONDS*1000, True)

  def rewind(self):
    self.skipBackward(n=self.stepAdvance())

  def forward(self):
    self.skipForward(n=self.stepAdvance())

  def numericForward(self, n=0):
    self.skipForward(n=n)
    if NUMERIC_SKIPS:
      self.show()
      self.ok()

  def one(self):
    self.numericForward(n=1)

  def two(self):
    self.numericForward(n=2)

  def three(self):
    self.numericForward(n=3)

  def four(self):
    self.numericForward(n=4)

  def five(self):
    self.numericForward(n=5)

  def six(self):
    self.numericForward(n=6)

  def seven(self):
    self.numericForward(n=7)

  def eight(self):
    self.numericForward(n=8)

  def nine(self):
    self.numericForward(n=9)

  def zero(self):
    self.numericForward(n=10)

  def pause(self):
    debug('Pausing...\n')
    if not self.changed:
      debug('Really pausing...\n')
      if PTYPE == '1':
        self.session.nav.stopService()
      else:
        self.session.nav.pause(p=1)
      myInfo(self.session, text='Paused...', callback=self.unpause,
             ok_actions=(['HeinzTimelineActions'], ['pause']),
             remap_ok_actions=['down'])
    debug('Exit pausing...\n')

  def unpause(self, *ret):
    debug('Unpausing...\n')
    rd = S.real_duration
    new_duration = rd - self.cur*60
    new_duration = min((self.max - self.min)*60, new_duration)
    new_duration = max(0, new_duration)
    self.params['DURATION'] = new_duration
    new_start_time = S.real_start + rd - new_duration
    self.params['START'] = epochTimeToCU(new_start_time)
    S.watch_start = Now() - (rd - new_duration)
    if PTYPE == '1':
      if S.vtype:
        self.session.nav.playService(eServiceReference(str(VCU_FMT % self.params)), **ADJUST)
      else:
        if NEW_XCAPI:
          self.params['DURATION'] = int(new_duration/60)
          self.params['CTYPE'] = CTYPE
        self.session.nav.playService(eServiceReference(str(XCU_FMT % self.params)), **ADJUST)
    else:
      self.session.nav.pause(p=0)
    uncoverVBILine()
    debug('Exit unpausing...\n')

  def stop(self):
    try:
      self.update()
      rd = S.real_duration
      new_duration = rd - self.cur*60
      new_duration = min((self.max - self.min)*60, new_duration)
      new_duration = max(0, new_duration)
      self.params['DURATION'] = new_duration
      new_start_time = S.real_start + rd - new_duration
      self.params['START'] = epochTimeToCU(new_start_time)
      S.watch_start = Now() - (rd - new_duration)
      # Swap RSDN for program title here, for zap history purposes...
      self.params['SDN'] = S.program_title
      if S.vtype:
        srr = eServiceReference(str(VCU_FMT % self.params))
      else:
        if NEW_XCAPI:
          self.params['DURATION'] = int(new_duration/60)
          self.params['CTYPE'] = CTYPE
        srr = eServiceReference(str(XCU_FMT % self.params))
      InfoBar.instance.servicelist.addToHistory(srr)
    except:
      debug(traceback.format_exc())
    if S.previous_service:
      self.session.nav.playService(S.previous_service, **ADJUST)
      try:
#        InfoBar.instance.servicelist.historyBack()
        InfoBar.instance.servicelist.addToHistory(S.previous_service)
      except:
        debug(traceback.format_exc())
    S.cu_service = None
    self.close()

  def info(self):
    text = S.program_title + '\n'
    text += epochTimeToInfo(S.real_start) + ' UTC\n'
    text += hmDuration(S.original_duration) + '\n\n'
    text += S.program_info
    info(self.session, text=text)

  def ok(self):
    if not self.shown:
      self.update()
      self.show()
      if INACTIVE_TIMER_SECONDS:
        self.inactiveTimer.start(INACTIVE_TIMER_SECONDS*1000, True)
      return
    rd = S.real_duration
    new_duration = rd - self.cur*60
    if not self.changed:
      new_duration += RELOAD_OFFSET_MINUTES*60
      self.skipBackward(n=RELOAD_OFFSET_MINUTES)
    new_duration = min((self.max - self.min)*60, new_duration)
    new_duration = max(0, new_duration)
    self.params['DURATION'] = new_duration
    new_start_time = S.real_start + rd - new_duration
    self.params['START'] = epochTimeToCU(new_start_time)
    S.watch_start = Now() - (rd - new_duration)
    if S.vtype:
      self.session.nav.playService(eServiceReference(str(VCU_FMT % self.params)), **ADJUST)
      debug('Play V: %s\n' % str(VCU_FMT % self.params))
    else:
      if NEW_XCAPI:
        self.params['DURATION'] = int(new_duration/60)
        self.params['CTYPE'] = CTYPE
      self.session.nav.playService(eServiceReference(str(XCU_FMT % self.params)), **ADJUST)
      debug('Play X: %s\n' % str(XCU_FMT % self.params))
    uncoverVBILine()
    self.cancel()


def reConfig():
  global TAIL_EXTRA_MINUTES
  global HEAD_EXTRA_MINUTES
  global RELOAD_OFFSET_MINUTES
  global SUPPORT_CACHE_INTERVAL_MINUTES
  global EPG_CACHE_INTERVAL_MINUTES
  global PTYPE
  global CTYPE
  global LOOKBACK
  global NEW_XCAPI
  global XCU_RE
  global XCU_FMT
  global GENERATE_CURRENT
  global STOP_AT_CURRENT
  global NUMERIC_SKIPS
  global TIMELINE_SMOOTHNESS
  global INACTIVE_TIMER_SECONDS
  global FORCE_LOOKUP
  global LIST_OFFSET
  global PLAY_OFFSET
  global REC_TAIL_EXTRA_MINUTES
  global REC_HEAD_EXTRA_MINUTES
  global REC_DELAY_SECONDS
  global REC_CMD
  global DEBUG
  TAIL_EXTRA_MINUTES = int(config.plugins.heinz.tail_extra.value)
  HEAD_EXTRA_MINUTES = int(config.plugins.heinz.head_extra.value)
  RELOAD_OFFSET_MINUTES = int(config.plugins.heinz.reload_offset.value)
  SUPPORT_CACHE_INTERVAL_MINUTES = int(config.plugins.heinz.support_cache_interval.value)
  EPG_CACHE_INTERVAL_MINUTES = int(config.plugins.heinz.epg_cache_interval.value)
  PTYPE = config.plugins.heinz.ptype.value
  CTYPE = config.plugins.heinz.ctype.value
  LOOKBACK = int(config.plugins.heinz.lookback.value)
  NEW_XCAPI = config.plugins.heinz.new_xcapi.value
  if NEW_XCAPI:
    XCU_RE = XCU_RE_NEW
    XCU_FMT = XCU_FMT_NEW
  else:
    XCU_RE = XCU_RE_OLD
    XCU_FMT = XCU_FMT_OLD
  GENERATE_CURRENT = config.plugins.heinz.generate_current.value
  STOP_AT_CURRENT = config.plugins.heinz.stopat_current.value
  NUMERIC_SKIPS = config.plugins.heinz.numeric_skips.value
  TIMELINE_SMOOTHNESS = int(config.plugins.heinz.timeline_smoothness.value)
  INACTIVE_TIMER_SECONDS = int(config.plugins.heinz.inactive_timer.value)
  FORCE_LOOKUP = config.plugins.heinz.force_lookup.value
  LIST_OFFSET = int(config.plugins.heinz.list_offset.value)
  PLAY_OFFSET = int(config.plugins.heinz.play_offset.value)
  REC_TAIL_EXTRA_MINUTES = int(config.plugins.heinz.rec_tail_extra.value)
  REC_HEAD_EXTRA_MINUTES = int(config.plugins.heinz.rec_head_extra.value)
  REC_DELAY_SECONDS = int(config.plugins.heinz.rec_delay.value)
  if REC_DELAY_SECONDS < REC_DELAY_SECONDS_MIN:
    REC_DELAY_SECONDS = REC_DELAY_SECONDS_MIN
    config.plugins.heinz.rec_delay.value = REC_DELAY_SECONDS_MIN
  REC_CMD=config.plugins.heinz.rec_cmd.value
  if not REC_CMD:
    REC_CMD = REC_CMD_DEF
    config.plugins.heinz.rec_cmd.value = REC_CMD_DEF
  DEBUG = config.plugins.heinz.debug.value
  config.plugins.heinz.save()
  if not openatv_like:
    configfile.save()


def EPGMenuByTimeout(session=None, service=None):
  global SAVED_SETUP
  if session:
    if openatv_like:
      session.open(Setup, setup=SETUP_KEY, plugin=PLUGIN_PATH)
    else:
      try:
        setup_file = file(PLUGIN_PATH + '/setup.xml', 'r')
        new_setupdom = xml.etree.cElementTree.parse(setup_file)
        setup_file.close()
        SAVED_SETUP = Screens.Setup.setupdom
        Screens.Setup.setupdom = new_setupdom
        session.open(Screens.Setup.Setup, SETUP_KEY)
        Screens.Setup.setupdom = SAVED_SETUP
      except:
        pass


def main(session, **kwargs):
  S.session = session
  reConfig()
  service_ref = session.nav.getCurrentlyPlayingServiceReference()
  if service_ref:
    ts = service_ref.toString()
    debug('CS: [ %s ]\n' % ts)
  else:
    info(session, text='No Current Stream!')
    return
  if adjustCU(session, ts=ts):
    return
  if playTS(session, ts=ts, service=service_ref):
    return
  myInfo(session, text='Unsupported Stream!\n(Wait For Setup)',
         timeout=11, timeout_callback=EPGMenuByTimeout, service=service_ref)


def Plugins(**kwargs):
  return PluginDescriptor(
      name=PLUGIN_NAME,
      description=PLUGIN_DESC,
      where=PluginDescriptor.WHERE_PLUGINMENU,
      icon=PLUGIN_ICON,
      fnc=main)
