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
import urllib2
import zlib

from collections import OrderedDict

from enigma import eServiceReference, eTimer

from Components.config import config, configfile, ConfigBoolean, ConfigNumber, ConfigSelection, ConfigSubsection, ConfigText
from Components.ActionMap import ActionMap
from Components.EpgList import EPGList, EPG_TYPE_SINGLE
from Components.MenuList import MenuList
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

PLUGIN_VERSION='6.2.2o'
PLUGIN_MONIKER='[Ab]'
PLUGIN_NAME='Absolut'
PLUGIN_DESC='VODka'
PLUGIN_ICON='absolut.png'
PLUGIN_PATH='Extensions/Absolut'
if not openatv_like:
  PLUGIN_PATH='/usr/lib/enigma2/python/Plugins/' + PLUGIN_PATH
SETUP_KEY='absolut'
VTS_RE=r'.*//(?P<host>[%a-zA-Z0-9:.-]+)/play(/vod){0,1}/(?P<stream>[0-9]+)\.([^.]*\.){0,1}(ts|m3u8)\?token=(?P<token>[a-zA-Z0-9+/=]+).*'
VAPI_MOVIE_CAT_GET=r'http://vapi.vaders.tv/vod/genres?username=%(USER)s&password=%(PWD)s'
VAPI_MOVIE_GET=r'http://vapi.vaders.tv/vod/streams/movie?username=%(USER)s&password=%(PWD)s&pageSize=10000'
VAPI_SERIES_GET=r'http://vapi.vaders.tv/vod/streams/tv?username=%(USER)s&password=%(PWD)s&pageSize=10000'
VAPI_SERIES_INFO_GET=r'http://vapi.vaders.tv/vod/streams/tv/%(ID)s?username=%(USER)s&password=%(PWD)s&pageSize=10000'
VVOD_FMT=r'%(PTYPE)s:0:1:0:0:0:0:0:0:0:http%%3a//vapi.vaders.tv/play/vod/%(STREAM)s.%(EXT)s.%(CTYPE)s%%3ftoken=%(TOKEN)s:%(SDN)s'
VTOKEN_FMT=r'{"username": "%(USER)s", "password": "%(PWD)s"}'
XTS_RE=r'.*//(?P<host>[%a-zA-Z0-9:.-]+)((/live){0,1}|/movie|/series)/(?P<user>[^/]+)/(?P<pwd>[^/]+)/(?P<stream>[0-9]+).*'
XAPI_MOVIE_GET=(r'http://%(HOST)s/player_api.php?username=%(USER)s&password=%(PWD)s&'
                     'action=get_vod_streams')
XAPI_MOVIE_CAT_GET=(r'http://%(HOST)s/player_api.php?username=%(USER)s&password=%(PWD)s&'
                     'action=get_vod_categories')
XAPI_SERIES_GET=(r'http://%(HOST)s/player_api.php?username=%(USER)s&password=%(PWD)s&'
                  'action=get_series')
XAPI_SERIES_CAT_GET=(r'http://%(HOST)s/player_api.php?username=%(USER)s&password=%(PWD)s&'
                      'action=get_series_categories')
XAPI_SERIES_INFO_GET=(r'http://%(HOST)s/player_api.php?username=%(USER)s&password=%(PWD)s&'
                      'action=get_series_info&series_id=%(ID)s')
XVOD_FMT=r'%(PTYPE)s:0:1:0:0:0:0:0:0:0:http%%3a//%(HOST)s/%(XTYPE)s/%(USER)s/%(PWD)s/%(STREAM)s.%(EXT)s:%(SDN)s'
CACHE_NAME='VOD'
FORCE_ALPHA_DEF=True
IGNORE_THE_DEF='the,an,a'
CACHE_INTERVAL_MINUTES_DEF=1440
CACHE_CLEAR_DEF=False
PTYPE_DEF='4097'
PTYPE_CHOICES=[('1', 'DVB'), ('4097', 'IPTV'), ('5001', 'GSTREAMER'), ('5002', 'EXTPLAYER')]
CTYPE_DEF='m3u8'
CTYPE_CHOICES=[('ts', 'ts'), ('m3u8', 'm3u8')]
REC_DELAY_SECONDS_DEF=60
REC_DELAY_SECONDS_MIN=1
REC_CMD_DEF=('/usr/bin/ffmpeg -y -i \'URL\' -vcodec copy -acodec copy -f mp4 /media/hdd/movie/downloading.mp4'
             ' </dev/null >/dev/null 2>&1'
             ' && mv /media/hdd/movie/downloading.mp4 /media/hdd/movie/\'FILE\''
             ' >/dev/null 2>&1'
             ' && wget -O- -q \'http://localhost/web/message?text=FILE%0aDownload+Completed!&type=2&timeout=5\'')
DEBUG_DEF=False
RQUEUE_MAX=12
VISIBLE_WIDTH=40
VERSION_DEF=PLUGIN_VERSION
VERSION_CHOICES=[(VERSION_DEF, VERSION_DEF)]
FORCE_ALPHA=FORCE_ALPHA_DEF
IGNORE_THE=IGNORE_THE_DEF
CACHE_INTERVAL_MINUTES=CACHE_INTERVAL_MINUTES_DEF
CACHE_CLEAR=CACHE_CLEAR_DEF
PTYPE=PTYPE_DEF
CTYPE=CTYPE_DEF
REC_DELAY_SECONDS=REC_DELAY_SECONDS_DEF
REC_CMD=REC_CMD_DEF
DEBUG=DEBUG_DEF
EPG_FILTER_DEF='.*'
EPG_FILTER_DEF_TEXT='All Categories'
EPG_FILTER=EPG_FILTER_DEF
E_TIME_FMT='%Y-%m-%dT%H:%M:%S+00:00'
SS_E_TIME_FMT='%Y-%m-%d %H:%M:%S'
VEPG_TIME_FMT='%Y%m%d%H%M%S'
INFO_TIME_FMT='%Y/%m/%d, %H:%M'
MYEPG_TIME_FMT='%a %d/%m, %H:%M'

config.plugins.absolut = ConfigSubsection()
config.plugins.absolut.force_alpha = ConfigBoolean(default=FORCE_ALPHA_DEF)
config.plugins.absolut.ignore_the = ConfigText(default=IGNORE_THE_DEF)
config.plugins.absolut.cache_interval = ConfigNumber(default=CACHE_INTERVAL_MINUTES_DEF)
config.plugins.absolut.cache_clear = ConfigBoolean(default=CACHE_CLEAR_DEF)
config.plugins.absolut.ptype = ConfigSelection(default=PTYPE_DEF, choices=PTYPE_CHOICES)
config.plugins.absolut.ctype = ConfigSelection(default=CTYPE_DEF, choices=CTYPE_CHOICES)
config.plugins.absolut.rec_delay = ConfigNumber(default=REC_DELAY_SECONDS_DEF)
config.plugins.absolut.rec_cmd = ConfigText(default=REC_CMD_DEF, fixed_size=False, visible_width=VISIBLE_WIDTH)
config.plugins.absolut.debug = ConfigBoolean(default=DEBUG_DEF)
config.plugins.absolut.version = ConfigSelection(default=VERSION_DEF, choices=VERSION_CHOICES)
if not openatv_like:
  SAVED_SETUP=Screens.Setup.setupdom

def compileIgnoreRegex():
  global IGNORE_THE
  regex = None
  try:
    regex = re.compile('^(?P<BEG>[^a-z0-9]*(%s){0,1}[^a-z0-9]+)[a-z0-9]' % '|'.join(IGNORE_THE.split(',')), flags=re.IGNORECASE)
  except:
    IGNORE_THE = ''
  return regex

IGNORE_THE_REGEX = compileIgnoreRegex()

def ignoreThe(title=None):
  if title and IGNORE_THE:
    try:
      m = IGNORE_THE_REGEX.search(title)
      if m:
        title = title[len(m.group('BEG')):]
    except:
      pass
  if not title:
    title = ' '
  return title


DEBUG_FILE='/tmp/absolut-debug.log'
def debug(s):
  if DEBUG:
    f = open(DEBUG_FILE, 'a+')
    f.write(s)
    f.close()


class State(object):
  _inst = None
  def __new__(cls):
    if State._inst is None:
      State._inst = object.__new__(cls)
      State._inst.sl = None
      State._inst.previous_service = None
      State._inst.previous_vod_string = None
      State._inst.vtype = False
      State._inst.proto = ''
      State._inst.host = ''
      State._inst.user = ''
      State._inst.pwd = ''
      State._inst.token = ''
      State._inst.cat = ''
      State._inst.cache_key = {}
      State._inst.cache_data = {}
      State._inst.epg_levels = []
      State._inst.data_lock = threading.Lock()
      State._inst.thread_lock = threading.Lock()
      State._inst.thread = None
      State._inst.rqueue = OrderedDict()
    return State._inst
S=State()


def Now():
  return int(time.time())


def eventTimeToEpoch(event_time):
  if S.vtype:
    return int(calendar.timegm(time.strptime(event_time, E_TIME_FMT)))
  return int(calendar.timegm(time.strptime(event_time, SS_E_TIME_FMT)))


def epochTimeToCU(epoch_time):
  return epoch_time


def epochTimeToEPG(epoch_time):
  return time.strftime(VEPG_TIME_FMT, time.gmtime(epoch_time))


def epochTimeToInfo(epoch_time):
  return time.strftime(INFO_TIME_FMT, time.gmtime(epoch_time))


def epochTimeToMyEPG(epoch_time):
  return time.strftime(MYEPG_TIME_FMT, time.gmtime(epoch_time))


def xEPGToEpoch(xepg_time):
  return int(calendar.timegm(time.strptime(xepg_time, XEPG_TIME_FMT)))


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
               title=None, service=None):
    TITLE={}
    if title_like:
      TITLE={'simple': True, 'title': title}
    MessageBox.__init__(self, session=session, text=text, type=type, timeout=timeout, **TITLE)
    self.service=service
    self.session=session
    self.timeout_callback = timeout_callback

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


def myInfo(session, text=None, callback=None, timeout=-1, timeout_callback=None, service=None):
  if text:
    if not openatv_like and text[:4] != PLUGIN_MONIKER:
      text = PLUGIN_MONIKER + ' ' + text
    if callback:
      session.openWithCallback(callback, myMessageBox, text, type=None, simple=True, timeout=timeout,
                               timeout_callback=timeout_callback, title=PLUGIN_NAME, service=service)
    else:
      session.open(myMessageBox, text, type=None, simple=True, timeout=timeout,
                   timeout_callback=timeout_callback, title=PLUGIN_NAME, service=service)
  

def getJsonURL(url, key=None, timestamp=None, cache=None, fondle_new=None):
  if not key:
    key = url+str(timestamp)
  else:
    key = key+str(timestamp)
  debug('k: %s + %s\n' % (url, str(timestamp)))
  if timestamp and cache and key == S.cache_key.get(cache):
    return S.cache_data.get(cache)
  request = urllib2.Request(url)
  request.add_header('User-Agent', 'Enigma2 Absolut plugin @oottppxx')
  request.add_header('Accept-Encoding', 'gzip')
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
  data = json.loads(data)
  if timestamp and cache:
    S.cache_key[cache] = key
    S.cache_data[cache] = data
  if fondle_new:
    fondle_new(data)
  return data


class OnlineEPG(object):
  def __init__(self, host=None, user=None, pwd=None, stream=None):
    self.movies = []
    self.series = []
    self.top_movies = []
    self.top_series = []
    self.top = []
    self.top_level = []
    self.events = self.movies
    self.host = urllib2.quote(host)
    self.user = user
    self.pwd = pwd
    self.stream = stream
    self.cat = None
    self.days = 0
    self.params = {'HOST': self.host, 'USER': self.user, 'PWD': self.pwd, 'STREAM': self.stream}

  def checkSupport(self):
    timestamp = None
    if CACHE_INTERVAL_MINUTES:
      timestamp = Now()/(CACHE_INTERVAL_MINUTES*60)

    self.top_level = []
    if S.vtype:
      try:
        vod_cat = getJsonURL(VAPI_MOVIE_CAT_GET % self.params, timestamp=timestamp,
                             cache=CACHE_NAME+self.params['HOST']+'movie_cat', fondle_new=None)
      except:
        debug(traceback.format_exc())
        vod_cat = []
      cat_dict = {}
      for vc in vod_cat:
        cat_dict[str(vc)] = str(vod_cat[vc]).capitalize()
      try:
        vod = getJsonURL(VAPI_MOVIE_GET % self.params, timestamp=timestamp,
                         cache=CACHE_NAME+self.params['HOST'], fondle_new=None)
        vod = vod['results']
      except:
        debug(traceback.format_exc())
        vod = []
      for p in vod:
        #cat = ','.join(sorted([cat_dict.get(x) for x in p.get('genres', []) if cat_dict.get(x)]))
        genres = p.get('genres')
        if genres:
          cat = cat_dict.get(genres[0], '')
        if not cat:
          cat = 'N/A'
        self.buildVAPIMovieEvent(program=p, cat=cat)

      if self.events:
        self.top_level.append('MOVIES')
        self.top_movies = self.buildTopEvents(programs=self.movies, cat='MOVIES')

      try:
        series = getJsonURL(VAPI_SERIES_GET % self.params, timestamp=timestamp,
                            cache=CACHE_NAME+self.params['HOST']+'series', fondle_new=None)
        series = series['results']
      except:
        debug(traceback.format_exc())
        series = []

      self.events = self.series
      for s in series:
        #cat = ','.join(sorted([cat_dict.get(x) for x in s.get('genres', []) if cat_dict.get(x)]))
        genres = s.get('genres')
        if genres:
          cat = cat_dict.get(genres[0], '')
        if not cat:
          cat = 'N/A'
        self.buildVAPISeriesEvent(program=s, cat=cat)

      if self.events:
        self.top_level.append('SERIES')
        self.top_series = self.buildTopEvents(programs=self.series, cat='SERIES')

    else:
      try:
        vod_cat = getJsonURL(XAPI_MOVIE_CAT_GET % self.params, timestamp=timestamp,
                             cache=CACHE_NAME+self.params['HOST']+'movie_cat', fondle_new=None)
      except:
        debug(traceback.format_exc())
        vod_cat = []
      cat_dict = {}
      for vc in vod_cat:
        cat_dict[str(vc['category_id'])] = str(vc['category_name']).capitalize()
      try:
        vod = getJsonURL(XAPI_MOVIE_GET % self.params, timestamp=timestamp,
                         cache=CACHE_NAME+self.params['HOST'], fondle_new=None)
      except:
        debug(traceback.format_exc())
        vod = []
      for p in vod:
        cat = str(p['category_id'])
        self.buildXAPIMovieEvent(program=p, cat=cat_dict.get(cat, cat))

      if self.events:
        self.top_level.append('MOVIES')
        self.top_movies = self.buildTopEvents(programs=self.movies, cat='MOVIES')

      try:
        vod_cat = getJsonURL(XAPI_SERIES_CAT_GET % self.params, timestamp=timestamp,
                             cache=CACHE_NAME+self.params['HOST']+'series_cat', fondle_new=None)
      except:
        debug(traceback.format_exc())
        vod_cat = []
      cat_dict = {}
      for vc in vod_cat:
        cat_dict[str(vc['category_id'])] = str(vc['category_name']).capitalize()
      try:
        series = getJsonURL(XAPI_SERIES_GET % self.params, timestamp=timestamp,
                            cache=CACHE_NAME+self.params['HOST']+'series', fondle_new=None)
      except:
        debug(traceback.format_exc())
        series = []

      self.events = self.series
      for s in series:
        self.buildXAPISeriesEvent(program=s)

      if self.events:
        self.top_level.append('SERIES')
        self.top_series = self.buildTopEvents(programs=self.series, cat='SERIES')

    self.events = self.top
    for tl in self.top_level:
      self.buildTopEvent(program=tl)
    return True

  def buildVAPIMovieEvent(self, program=None, cat=None, desc=None):
    debug("VAPIMovie, Cat, Desc: %s %s %s\n" % (program, cat, desc))
    if program:
      if not cat:
        cat = 'N/A'
      title = str(program.get('title'))
      desc = cat + '\n\n' + str(program.get('desc'))
      if FORCE_ALPHA:
        added = 0
      else:
        added = int(program['added'])
      stream = str(program.get('vodItemId'))
      self.params['STREAM'] = stream
      self.params['EXT'] = str(program['ext'])
      self.params['PTYPE'] = PTYPE
      self.params['CTYPE'] = CTYPE
      self.params['TOKEN'] = S.token
      self.params['SDN'] = cat
      stream = VVOD_FMT % self.params
      self.events.append((stream, {'CAT': cat, 'DESC': desc, 'PT': title}, added, 0, title))

  def buildVAPISeriesEvent(self, program=None, cat=None, desc=None):
    debug("VAPISeries, Cat, Desc: %s %s %s\n" % (program, cat, desc))
    if program:
      id = str(program['id'])
      title = str(program.get('showName', 'N/A'))
      if not cat:
        cat = 'N/A'
      desc = program.get('desc')
      if not desc:
        desc = title
      desc = cat + '\n\n' + str(desc)
      ext = str(program['ext'])
      if FORCE_ALPHA:
        added = 0
      else:
        added = int(program['added'])
      extra = {'CAT': cat, 'DESC': desc, 'PT': title, 'L': 'VEPISODES', 'ID': id}
      extra.update(self.params)
      self.events.append((id, extra, 0, 0, title))

  def buildXAPIMovieEvent(self, program=None, cat=None, desc=None):
    debug("XAPIMovie, Cat, Desc: %s %s %s\n" % (program, cat, desc))
    if program:
      title = str(program.get('name', 'N/A'))
      if not desc:
        desc = title
      if not cat:
        cat = program['category_id']
      if not cat:
        cat = ''
      cat = str(cat)
      if FORCE_ALPHA:
        added = 0
      else:
        added = int(program['added'])
      stream = program.get('stream_id')
      if not stream:
        stream = ''
      stream = str(stream)
      self.params['STREAM'] = stream
      self.params['EXT'] = str(program['container_extension'])
      self.params['PTYPE'] = PTYPE
      self.params['SDN'] = cat
      self.params['XTYPE'] = 'movie'
      stream = XVOD_FMT % self.params
      self.events.append((stream, {'CAT': cat, 'DESC': desc, 'PT': title}, added, 0, title))

  def buildXAPISeriesEvent(self, program=None, cat=None, desc=None):
    debug("XAPISeries, Cat, Desc: %s %s %s\n" % (program, cat, desc))
    if program:
      id = str(program['series_id'])
      title = str(program.get('name', 'N/A'))
      if not desc:
        desc = title
      if not cat:
        cat = str(program['category_id'])
      extra = {'CAT': cat, 'DESC': desc, 'PT': title, 'L': 'XEPISODES', 'ID': id}
      extra.update(self.params)
      self.events.append((id, extra, 0, 0, title))

  def buildTopEvents(self, programs=None, cat=None):
    debug("TopEvents, Programs: %s\n" % programs)
    events = []
    alfa = set()
    for p in programs:
      alfa.add(str(ignoreThe(p[4]))[0].upper())
    alfa = list(alfa)
    alfa.sort()
    if alfa:
      events.append(('ALL', {'CAT': cat, 'DESC': 'ALL', 'PT': 'ALL', 'L': 'ALL'}, 0, 0, '...'))
    for a in alfa:
      if not cat:
        cat = a
      events.append((a, {'CAT': cat, 'DESC': a, 'PT': a, 'L': a}, 0, 0, a))
    return events

  def buildTopEvent(self, program=None):
    debug("Top, Program: %s\n" % program)
    if program:
      self.events.append((program, {'CAT': '', 'DESC': program, 'PT': program, 'L': program}, 0, 0, program))

  def data(self):
    error = ''
    try:
      if not self.checkSupport():
        return error, [], [], [], [], []
    except:
      error = 'Matching But Unsupported Stream!\n(Transient Error Or Unsupported Provider?)'
      debug(traceback.format_exc())
      debug('Absolut Exception! %(STREAM)s@%(HOST)s' % self.params)
      return error, [], [], [], [], []
    if not self.top:
      error = 'No VODka!\n(Transient Error?)'
      debug('No VODka! %(STREAM)s@%(HOST)s' % self.params)
      return error, [], [], [], [], []
    top = sorted(self.top, key=lambda e: ignoreThe(e[4]))
    top_movies = sorted(self.top_movies, key=lambda e: ignoreThe(e[4]))
    top_series = sorted(self.top_series, key=lambda e: ignoreThe(e[4]))
    if FORCE_ALPHA:
      movies = sorted(self.movies, key=lambda e: ignoreThe(e[4]))
      series = sorted(self.series, key=lambda e: ignoreThe(e[4]))
    else:
      movies = sorted(self.movies, key=lambda e: e[2])
      series = sorted(self.series, key=lambda e: e[2])
    return error, top, top_movies, top_series, movies, series


class myEvent(object):
  def __init__(self, index=None, epg=None):
    self.index = index
    self.epg = epg

  def __str__(self):
    return '(id: %s, name: %s, time: %s, duration: %s, extra: %s)' % (
             self.index, self.epg[self.index][4], self.epg[self.index][2],
             self.epg[self.index][3], self.epg[self.index][1])

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
    self.list = []
    if epg:
      self.list = epg

  def getCurrentIndex(self):
    # Same as OpenATV def, so no "if openatv_like:"
    return self.instance.getCurrentIndex()

  def setCurrentIndex(self, index):
    # Same as OpenATV def, so no "if openatv_like:"
    if self.instance is not None:
      self.instance.moveSelectionTo(index)

  def updateList(self, service, new_list=None):
    if new_list:
      self.list = new_list
      self.fillSingleEPG(service=service)

  def fillSingleEPG(self, service):
    self.l.setList(self.list)
    now = Now()
    if CACHE_INTERVAL_MINUTES:
      now /= (CACHE_INTERVAL_MINUTES*60)
      now *= (CACHE_INTERVAL_MINUTES*60)
    idx = 0
    for e in self.list:
      debug('e == %s\n' % str(e))
      if e[2] >= now:
        break
      idx += 1
    if idx > len(self.list):
      idx = 0
    self.setCurrentIndex(idx)
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
      return {'CAT': '', 'DESC': '', 'PT': ''}


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
      except:
        debug(traceback.format_exc())
      S.thread_lock.release()

  def unblock(self):
    debug('processRQueue unblock!\n')
    S.thread_lock.release()


class mySingleEPG(SingleEPG):
  def __init__(self, session, service, EPGtype='single', epg=(), filter=EPG_FILTER_DEF):
    overjump_value = None   
    if openatv_like:
      SingleEPG.__init__(self, session, service=service, EPGtype=EPGtype)
      overjump_value = config.epgselection.overjump.value                     
    else:
      SingleEPG.__init__(self, session, service=service)
    if openvix:
      self.type = EPG_TYPE_SINGLE
    self.skinName = "EPGSelection"
    self.setTitle(PLUGIN_NAME)                                                               
    global EPG_FILTER
    if S.sl is None:
      S.sl = InfoBar.instance.servicelist
    self.session = session
    self.service = service
    self.top = []
    self.top_movies = []
    self.top_series = []
    self.movies = []
    self.series = []
    if epg:
      self.top = epg[0]
      self.top_movies = epg[1]
      self.top_series = epg[2]
      self.movies = epg[3]
      self.series = epg[4]
    if not S.epg_levels:
      self.epg = self.top
      idx = -1
    else:
      self.epg, idx = S.epg_levels.pop()
    self.filters = list(set([e[1]['CAT'] for e in self.epg]))
    self.filters.sort()
    self.filters.append(EPG_FILTER_DEF)
    debug('Filters: %s\n' % self.filters)
    try:
      self.filter_index = self.filters.index(EPG_FILTER)
    except ValueError:
      self.filter_index = len(self.filters)-1
      EPG_FILTER = self.filters[self.filter_index] 
    self.filtered_epg = self.filterEPG(epg=self.epg)
    self['list'] = myEPGList(
        type=self.type, selChangedCB=self.onSelectionChanged,
        timer=self.session.nav.RecordTimer, time_epoch=None,
        overjump_empty=overjump_value, graphic=False,
        epg=self.filtered_epg)
    if idx != -1:
      self['list'].setCurrentIndex(idx)
    self.setFilterButtonText(text=EPG_FILTER)
    self['key_green'].setText('Display Queue')
    self['key_yellow'].setText('')
    self['key_blue'].setText('<<<')

  def filterEPG(self, epg=None):
    if epg:
      if EPG_FILTER == EPG_FILTER_DEF:
        regex = EPG_FILTER
      else:
        regex = re.escape(EPG_FILTER)
      return [e for e in epg if re.match(regex, e[1]['CAT'])]

  def buildVAPIEpisodeEvents(self, series=None, extra=None):
    debug('VEpisode: %s\n' % series)
    events = []
    if series and extra:
      try:
        timestamp = None
        if CACHE_INTERVAL_MINUTES:
          timestamp = Now()/(CACHE_INTERVAL_MINUTES*60)
        episodes = getJsonURL(VAPI_SERIES_INFO_GET % extra, timestamp=timestamp,
                              cache=CACHE_NAME+extra['HOST']+'series'+extra['ID'], fondle_new=None)
        debug("Episodes: %s\n" % episodes)
      except:
        debug(traceback.format_exc())
        seasons = []
      for e in episodes:
        debug("Episode: %s %s\n" % (e, type(e)))
        e = json.loads(e)
        debug("Episode: %s %s\n" % (e, type(e)))
        title = str(e['title'])
        extra['STREAM'] = str(e['vodItemId'])
        extra['EXT'] = str(e['ext'])
        extra['SDN'] = title
        season = e['season']
        episode = e['episode']
        desc = str(e['desc'])
        se = ''
        if season and episode:
          desc = desc + '\n\nS%s E%s' % (str(season).zfill(2), str(episode).zfill(2))
          se = '%s%s' % (str(season).zfill(2), str(episode).zfill(2))
        else:
          se = title
        if FORCE_ALPHA:
          added = 0
        else:
          added = int(e['added'])
        events.append((VVOD_FMT % extra, {'CAT': '', 'DESC': desc, 'PT': title, 'SE': se}, added, 0, title))
    if FORCE_ALPHA:
#      return sorted(events, key=lambda e: ignoreThe(e[4]))
      return sorted(events, key=lambda e: e[1]['SE'])
    else:
      return sorted(events, key=lambda e: e[2])

  def buildXAPIEpisodeEvents(self, series=None, extra=None):
    debug('XEpisode: %s\n' % series)
    events = []
    if series and extra:
      try:
        timestamp = None
        if CACHE_INTERVAL_MINUTES:
          timestamp = Now()/(CACHE_INTERVAL_MINUTES*60)
        info = getJsonURL(XAPI_SERIES_INFO_GET % extra, timestamp=timestamp,
                          cache=CACHE_NAME+extra['HOST']+'series'+extra['ID'], fondle_new=None)
        seasons = info.get('episodes', [])
        debug("Seasons: %s\n" % seasons)
      except:
        debug(traceback.format_exc())
        seasons = []
      for sea in seasons:
        debug("Season: %s\n" % sea)
        for p in seasons[sea]:
          title = str(p['title'])
          extra['XTYPE'] = 'series'
          extra['STREAM'] = str(p['id'])
          extra['EXT'] = str(p['container_extension'])
          extra['SDN'] = title
          season = p['season']
          episode = p['episode_num']
          desc = title
          se = ''
          if season and episode:
            desc = title + '\n\nS%s E%s' % (str(season).zfill(2), str(episode).zfill(2))
            se = '%s%s' % (str(season).zfill(2), str(episode).zfill(2))
          else:
            se = title
          if FORCE_ALPHA:
            added = 0
          else:
            added = int(p['added'])
          events.append((XVOD_FMT % extra, {'CAT': '', 'DESC': desc, 'PT': title, 'SE': se}, added, 0, title))
    if FORCE_ALPHA:
#      return sorted(events, key=lambda e: ignoreThe(e[4]))
      return sorted(events, key=lambda e: e[1]['SE'])
    else:
      return sorted(events, key=lambda e: e[2])

  def OK(self):
    global EPG_FILTER
    service_event, service_ref = self['list'].getCurrent()
    idx = self['list'].getCurrentIndex()
    debug('OK, ev, ref: %s %s\n' % (service_event, service_ref))
    extra_info = self['list'].getExtra()
    CAT = extra_info.get('CAT')
    L = extra_info.get('L')
    if not L:
      S.epg_levels.append((self.epg, idx))
      sr = service_ref.ref.toString()
      sr = sr.rsplit(':', 1)[0] + ':' + PLUGIN_MONIKER + ' ' + extra_info['PT']
      S.previous_vod_string = sr
      if openatv_like:
        self.closeEventViewDialog()
    # zap start
      srr = eServiceReference(sr)
      self.session.nav.playService(srr, **ADJUST)
      S.sl.addToHistory(srr)
    # zap end
      self.close(True)
      return
    if L in ['MOVIES']:
      S.epg_levels.append((self.epg, idx))
      self.epg = self.top_movies
    if L in ['SERIES']:
      S.epg_levels.append((self.epg, idx))
      self.epg = self.top_series
    if L in ['VEPISODES']:
      S.epg_levels.append((self.epg, idx))
      self.epg = self.buildVAPIEpisodeEvents(series=service_event, extra=extra_info)
    if L in ['XEPISODES']:
      S.epg_levels.append((self.epg, idx))
      self.epg = self.buildXAPIEpisodeEvents(series=service_event, extra=extra_info)
    if L in ['ALL']:
      if CAT in ['MOVIES']:
        S.epg_levels.append((self.epg, idx))
        self.epg = self.movies
      if CAT in ['SERIES']:
        S.epg_levels.append((self.epg, idx))
        self.epg = self.series
    else:
      if CAT in ['MOVIES']:
        S.epg_levels.append((self.epg, idx))
        self.epg = [e for e in self.movies if ignoreThe(e[4])[0] == L]
      if CAT in ['SERIES']:
        S.epg_levels.append((self.epg, idx))
        self.epg = [e for e in self.series if ignoreThe(e[4])[0] == L]
    self.filters = list(set([e[1]['CAT'] for e in self.epg]))
    self.filters.sort()
    self.filters.append(EPG_FILTER_DEF)
    debug('Filters: %s\n' % self.filters)
    try:
      self.filter_index = self.filters.index(EPG_FILTER)
    except ValueError:
      self.filter_index = len(self.filters)-1
    EPG_FILTER = self.filters[self.filter_index] 
    self.filtered_epg = self.filterEPG(epg=self.epg)
    self['list'].updateList(self.service, self.filtered_epg)
    self.setFilterButtonText(text=EPG_FILTER)

  # OpenPLi OK key assignment
  def eventSelected(self):
    self.OK()

  def closeScreen(self):
    global EPG_FILTER
    if not S.epg_levels:
      if openatv_like:
        self.closeEventViewDialog()
      self.close(True)
      return
    self.epg, idx = S.epg_levels.pop()
    self.filters = list(set([e[1]['CAT'] for e in self.epg]))
    self.filters.sort()
    self.filters.append(EPG_FILTER_DEF)
    debug('Filters: %s\n' % self.filters)
    try:
      self.filter_index = self.filters.index(EPG_FILTER)
    except ValueError:
      self.filter_index = len(self.filters)-1
    EPG_FILTER = self.filters[self.filter_index] 
    self.filtered_epg = self.filterEPG(epg=self.epg)
    self['list'].updateList(self.service, self.filtered_epg)
    self['list'].setCurrentIndex(idx)
    self.setFilterButtonText(text=EPG_FILTER)

  def createSetup(self):
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

  def setFilterButtonText(self, text=None):
    if text:
      if text == EPG_FILTER_DEF:
        self['key_red'].setText(EPG_FILTER_DEF_TEXT)
      else:
        self['key_red'].setText(text)

  def recButtonPressed(self):
    extra_info = self['list'].getExtra()
    L = extra_info.get('L')                                                                                                     
    if L:
      debug('Not at the right level for recording... %s\n' % L)
      return
    service_event, service_ref = self['list'].getCurrent()
    url = urllib2.unquote(re.sub('.*http', 'http', re.sub(':[^:]*$', '', service_ref.ref.toString())))
    debug('URL: %s\n' % url)
    pt = extra_info['PT']
    if S.epg_levels:
      previous_epg, previous_idx = S.epg_levels[-1]
      previous_extra = previous_epg[previous_idx][1]
      previous_L = previous_extra.get('L', '')
      previous_PT = previous_extra.get('PT', '')
      debug('Previous extra L and PT: %s %s\n' % (previous_L, previous_PT))
      if previous_L in ['VEPISODES', 'XEPISODES']:
        pt = '%s-%s' % (previous_PT, pt)
    k = pt
    fname = re.sub('__', '_', re.sub('[^a-zA-Z0-9-]', '_', re.sub('/', '-', '%s' % pt))) + '.mp4'
    cmd = re.sub('URL', url, re.sub('FILE', fname, REC_CMD))
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
    global EPG_FILTER
    self.filter_index += 1
    if self.filter_index >= len(self.filters):
      self.filter_index = 0
    EPG_FILTER = self.filters[self.filter_index] 
    self.filtered_epg = self.filterEPG(epg=self.epg)
    self['list'].updateList(self.service, self.filtered_epg)
    self.setFilterButtonText(text=EPG_FILTER)

  def redButtonPressedLong(self):
    self.redButtonPressed()

  # OpenPLi red key assignment
  def zapTo(self):
    self.recButtonPressed()

  def setTimerButtonText(self, text=None):
    return

  def greenButtonPressed(self):
    S.data_lock.acquire()
    k = '\n'.join(S.rqueue.keys())
    S.data_lock.release()
    if not k:
      k = 'Empty!'
    msg = 'Recording Queue\n\n%s' % k
    myInfo(self.session, msg)

  def greenButtonPressedLong(self):
    self.greenButtonPressed()

  def yellowButtonPressed(self):
    return

  def yellowButtonPressedLong(self):
    single.yellowButtonPressed()

  def blueButtonPressed(self):
    global EPG_FILTER
    self.filter_index -= 1
    if self.filter_index <0:
      self.filter_index = len(self.filters) - 1
    EPG_FILTER = self.filters[self.filter_index] 
    self.filtered_epg = self.filterEPG(epg=self.epg)
    self['list'].updateList(self.service, self.filtered_epg)
    self.setFilterButtonText(text=EPG_FILTER)

  def blueButtonPressedLong(self):
    self.blueButtonPressed()


def playTS(session, ts=None, service=None):
  S.previous_service = service
  try:
    ts = urllib2.unquote(ts)
  except:
    info(session, 'Malformed Service URL!\n(Can\'t Unquote.)')
    return True
  m = re.match(VTS_RE, ts, re.IGNORECASE)
  if m:
    S.vtype = True
    S.host = m.group('host')
    S.stream = int(m.group('stream'))
    S.token = m.group('token')
    try:
      auth = json.loads(base64.b64decode(S.token))
      S.user = str(auth['username'])
      S.pwd = str(auth['password'])
    except:
      info(session, text='No VODka For You!\n(Bad Auth Token Decode.)')
      return True
    error, top, top_movies, top_series, movies, series = OnlineEPG(
        host=S.host, user=S.user, pwd=S.pwd, stream=S.stream).data()
    if not error and not top:
      info(session, text='No VODka For You!\n(This Stream Doesn\'t Support It.)')
      debug('No VODka for %s@%s!' % (S.stream, urllib2.unquote(S.host)))
    elif error:
      info(session, text=error)
    else:
      debug("%s %s %s\n" % (top, top_movies, top_series))
      debug("%s\n" % movies)
      debug("%s\n" % series)
      if S.previous_service.toString() != S.previous_vod_string:
        while S.epg_levels:
          S.epg_levels.pop()
      session.open(mySingleEPG, service=service, epg=(top, top_movies, top_series, movies, series))
    return True
  m = re.match(XTS_RE, ts, re.IGNORECASE)
  if m:
    S.vtype = False
    S.host = m.group('host')
    S.user = m.group('user')
    S.pwd = m.group('pwd')
    S.stream = int(m.group('stream'))
    error, top, top_movies, top_series, movies, series = OnlineEPG(
        host=S.host, user=S.user, pwd=S.pwd, stream=S.stream).data()
    if not error and not top:
      info(session, text='No VODka For You!\n(This Stream Doesn\'t Support It.)')
      debug('No VODka for %s@%s!' % (S.stream, urllib2.unquote(S.host)))
    elif error:
      info(session, text=error)
    else:
      debug("%s %s %s\n" % (top, top_movies, top_series))
      debug("%s\n" % movies)
      debug("%s\n" % series)
      if S.previous_service.toString() != S.previous_vod_string:
        while S.epg_levels:
          S.epg_levels.pop()
      session.open(mySingleEPG, service=service, epg=(top, top_movies, top_series, movies, series))
    return True
  return False


def reConfig():
  global FORCE_ALPHA
  global IGNORE_THE
  global IGNORE_THE_REGEX
  global CACHE_INTERVAL_MINUTES
  global CACHE_CLEAR
  global PTYPE
  global CTYPE
  global REC_DELAY_SECONDS
  global REC_CMD
  global DEBUG
  FORCE_ALPHA = config.plugins.absolut.force_alpha.value
  IGNORE_THE = str(config.plugins.absolut.ignore_the.value)
  IGNORE_THE_REGEX = compileIgnoreRegex()
  CACHE_INTERVAL_MINUTES = int(config.plugins.absolut.cache_interval.value)
  CACHE_CLEAR = config.plugins.absolut.cache_clear.value
  if CACHE_CLEAR:
    config.plugins.absolut.cache_clear.value = False
    CACHE_CLEAR = False
    S.cache_key.pop(CACHE_NAME, None)
    S.cache_data.pop(CACHE_NAME, None)
    debug('Cleared cache!')
  PTYPE = config.plugins.absolut.ptype.value
  CTYPE = config.plugins.absolut.ctype.value
  REC_DELAY_SECONDS = int(config.plugins.absolut.rec_delay.value)
  if REC_DELAY_SECONDS < REC_DELAY_SECONDS_MIN:
    REC_DELAY_SECONDS = REC_DELAY_SECONDS_MIN
    config.plugins.absolut.rec_delay.value = REC_DELAY_SECONDS_MIN
  REC_CMD=config.plugins.absolut.rec_cmd.value
  if not REC_CMD:
    REC_CMD = REC_CMD_DEF
    config.plugins.absolut.rec_cmd.value = REC_CMD_DEF
  DEBUG = config.plugins.absolut.debug.value
  config.plugins.absolut.save()
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
  reConfig()
  service_ref = session.nav.getCurrentlyPlayingServiceReference()
  if service_ref:
    ts = service_ref.toString()
    debug('Current stream[ %s ]\n' % ts)
  else:
    info(session, text='No Current Stream!')
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
