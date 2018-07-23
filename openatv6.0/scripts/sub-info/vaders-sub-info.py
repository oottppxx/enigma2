#!/usr/bin/python

import json
import sys
import time
import urllib2
import zlib

VAPI_INFO='http://vapi.vaders.tv/vod/user?username=%(USER)s&password=%(PWD)s'
TIME_FMT='%Y-%m-%d %H:%M:%S'

def getJsonURL(url):
  request = urllib2.Request(url)                                                                                     
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

if len(sys.argv) < 3:
  print "Usage: %s <user> <pass>" % sys.argv[0]
  sys.exit(-1)

ui = getJsonURL(VAPI_INFO % {'USER': sys.argv[1], 'PWD': sys.argv[2]})

user = ''
enabled = ''
create_date = ''
create_date_2 = ''
update_date = ''
exp_date = ''
is_trial = ''
max_cons = ''
if ui:
  user = ui.get('username', '~')
  enabled = ui.get('enabled', '~')
  create_date = ui.get('created_at', None)
  create_date_2 = ui.get('createdAt', None)
  update_date = ui.get('updatedAt', None)
  exp_date = ui.get('exp_date', None)
  is_trial = ui.get('is_trial', '~')
  max_cons = ui.get('max_connections', '~')
else:
  print "No info!"
  sys.exit(0)

if create_date:
  create_date = time.strftime(TIME_FMT, time.gmtime(int(create_date)))
else:
  create_date = '~'

if exp_date:
  exp_date = time.strftime(TIME_FMT, time.gmtime(int(exp_date)))
else:
  exp_date = '~'

print 'User: %s' % user
print 'Enabled: %s' % enabled
print 'Created: %s' % create_date
print 'Created (2): %s' % create_date_2
print 'Updated: %s' % update_date
print 'Expires: %s' % exp_date
print 'Trial: %s' % is_trial
print 'Max Cons: %s' % max_cons
