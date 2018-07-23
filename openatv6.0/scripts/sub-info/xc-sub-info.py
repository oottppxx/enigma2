#!/usr/bin/python

import json
import sys
import time
import urllib2
import zlib

XC_INFO='http://%(HOST)s/player_api.php?username=%(USER)s&password=%(PWD)s&action=user&sub=info'
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

if len(sys.argv) < 4:
  print "Usage: %s <host> <user> <pass>" % sys.argv[0]
  sys.exit(-1)

data = getJsonURL(XC_INFO % {'HOST': sys.argv[1], 'USER': sys.argv[2], 'PWD': sys.argv[3]})

message = ''
user = ''
status = ''
create_date = ''
exp_date = ''
auth = ''
is_trial = ''
active_cons = ''
max_cons = ''
formats = ''
ui = data.get('user_info')
if ui:
  message = ui.get('message', '~')
  user = ui.get('username', '~')
  status = ui.get('status', '~')
  auth = ui.get('auth', '~')
  create_date = ui.get('created_at', None)
  exp_date = ui.get('exp_date', None)
  is_trial = ui.get('is_trial', '~')
  active_cons = ui.get('active_cons', '~')
  max_cons = ui.get('max_connections', '~')
  formats = ui.get('allowed_output_formats', '~')
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

print 'Message: %s' % message
print 'User: %s' % user
print 'Status: %s' % status
print 'Auth: %s' % auth
print 'Created: %s' % create_date
print 'Expires: %s' % exp_date
print 'Trial: %s' % is_trial
print 'Cons: %s/%s' % (active_cons, max_cons)
print 'Formats: %s' % formats
