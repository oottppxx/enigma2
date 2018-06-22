#!/usr/bin/python


USER=''
PWD=''


import re
import urllib2
import zlib


BOUQUET_FILE='/etc/enigma2/userbouquet.vod__tv_.tv'
SUB_BOUQUET_FILE='/etc/enigma2/bouquets/userbouquet.vod%s.tv'
RELOAD_URL='http://127.0.0.1/web/servicelistreload?mode=0'
M3U_URL='http://vaders.tv/vget?username=%s&password=%s&vod=true'
M3U_FILE='/home/root/m3u.txt'
EXT_RE='#EXTINF.*group-title="(?P<cat>[^"]+)".*,(?P<desc>.+)'
URL_RE='(?P<url>http://.*play/vod.*)'
NAME='#NAME %s'
SERVICE_BOUQUET='#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.vod%d.tv" ORDER BY bouquet'
SERVICE_VOD='#SERVICE 4097:0:1:feed:dead:beef:0:0:0:0:%s:VOD'
DESCRIPTION='#DESCRIPTION %s'

def getData(user=None, pwd=None):
  if not (user or pwd):
    with open(M3U_FILE, 'rU') as f:
      data = f.readlines()
      data = [x.strip() for x in data]
      data = [x for x in data if x]
  else:
    request = urllib2.Request(M3U_URL % (user, pwd))
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
    data = data.split('\n')
  return data


def filterData(data):
  re_ext = re.compile(EXT_RE)
  re_url = re.compile(URL_RE)
  new_data = {}
  ext = 0
  cat = ''
  desc = ''
  for d in data:
    m = re_ext.match(d)
    if m and not ext:
      cat = m.group('cat')
      desc = m.group('desc')
      ext = 1
      continue
    m = re_url.match(d)
    if m and ext == 1:
      url = m.group('url')
      new_data.setdefault(cat, [])
      new_data[cat].append((desc, url))
      ext = 0
      continue
    ext = 0
  return new_data


def writeFile(fname, data):
  with open(fname, 'w') as f:
    f.write('\n'.join(data))


def writeData(cat, streams, index):
  vod = []
  vod.append(NAME % cat)
  for s in streams:
    url = urllib2.quote(s[1])
    vod.append(SERVICE_VOD % url)
    vod.append(DESCRIPTION % s[0])
  writeFile(SUB_BOUQUET_FILE % index, vod)


def outputData(data):
  index = 0
  movies = data.get('Movies', [])
  if movies:
    writeData('MOVIES', movies, index)
    index += 1
  for k in sorted(data.keys()):
    if k != 'Movies':
      writeData(k, data[k], index)
      index += 1
  if index:
    vod = []
    vod.append(NAME % 'VOD')
    limit = 0
    while limit < index:
      vod.append(SERVICE_BOUQUET % limit)
      limit += 1
    writeFile(BOUQUET_FILE, vod)

try:
  outputData(filterData(getData(user=USER, pwd=PWD)))
  urllib2.urlopen(urllib2.Request(RELOAD_URL))
except:
  print 'An error occurred, but we\'re too lazy to understand which one...'
