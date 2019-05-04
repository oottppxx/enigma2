#!/usr/bin/python

import json
import re
import sys
import time
import urllib2
import zlib

VAPI_MC_SCHED='http://vapi.vaders.tv/mc/schedule?username=%(USER)s&password=%(PWD)s'
TIME_FMT='%Y-%m-%d %H:%M:%S'

def getJsonURL(url):
  request = urllib2.Request(url)
  request.add_header('User-Agent', 'MC2XML script @oottppxx')
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
  return json.loads(data)


if len(sys.argv) < 4:
  print "Usage: %s <user> <pass> <offset>" % sys.argv[0]
  sys.exit(-1)

mc = getJsonURL(VAPI_MC_SCHED % {'USER': sys.argv[1], 'PWD': sys.argv[2]})
offset = sys.argv[3]

channels = {}
programmes = []
if mc:
  for program in mc:
    cat = str(program['category']['name'])
    logo = str(program['category']['logo'])
    title = program['title'].encode('ascii', 'replace')
    start = re.sub('[^0-9]', '', str(program['startTime']).split('+')[0])
    stop = re.sub('[^0-9]', '', str(program['endTime']).split('+')[0])
    for stream in program['streams']:
      sid = str(stream['id']) + '.vaders.tv'
      sname = str(stream['name'])
      ptitle = title
      if "1080" in sname:
        ptitle += ' [1080]'
      channels[sid] = sname
      programmes.append({'START': start, 'STOP': stop, 'CHANNEL': sid,
                         'TITLE': ptitle, 'CAT': cat, 'LOGO': logo})
else:
  print "No info!"
  sys.exit(0)

HEADER="""<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE tv SYSTEM "xmltv.dtd">
    <tv source-info-url="http://vaders.tv" source-info-name="VS" generator-info-name="VS" generator-info-url="http://www.xmltv.org/">"""
TRAILER="""    </tv>
"""
CHANNEL_TMPL="""        <channel id="%(ID)s">
            <display-name>%(SDN)s</display-name>
            <icon src="none" />
        </channel>"""
PROGRAMME_TMPL="""        <programme start="%(START)s%(OFFSET)s" stop="%(STOP)s%(OFFSET)s" channel="%(ID)s">
            <title lang="en">%(TITLE)s</title>
            <category lang="en">%(CAT)s</category>
            <category lang="en">Sports</category>
            <icon src="%(LOGO)s"/>
         </programme>"""

print HEADER
for channel_id, channel_name in channels.iteritems():
  print CHANNEL_TMPL % {'ID': channel_id, 'SDN': channel_name}
for p in programmes:
  print PROGRAMME_TMPL % {'START': p['START'], 'STOP': p['STOP'], 'ID': p['CHANNEL'],
                          'TITLE': p['TITLE'], 'CAT': p['CAT'], 'LOGO': p['LOGO'],
                          'OFFSET': offset}
print TRAILER
