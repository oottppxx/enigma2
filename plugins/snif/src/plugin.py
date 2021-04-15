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

import base64
import os
import re
import socket
import struct
import threading
import time
import traceback


from Components.config import config, ConfigBoolean, ConfigNumber, ConfigSelection, ConfigSubsection, ConfigText
from Plugins.Plugin import PluginDescriptor
if openatv_like:
  from Screens.Setup import Setup
else:
  import Screens.Setup
  import xml.etree.cElementTree
  from Components.config import configfile


PLUGIN_VERSION='6.2.0a'
PLUGIN_NAME='Snif'
PLUGIN_DESC='Per User Con Tracker'
PLUGIN_ICON='snif.png'
PLUGIN_PATH='Extensions/Snif'
if not openatv_like:
  PLUGIN_PATH='/usr/lib/enigma2/python/Plugins/' + PLUGIN_PATH
SETUP_KEY='snif'

VISIBLE_WIDTH=40
VERSION_DEF=PLUGIN_VERSION
VERSION_CHOICES=[(VERSION_DEF, VERSION_DEF)]
ENABLE_DEF=False
ENABLE=ENABLE_DEF
LIMIT_DEF=2
LIMIT=LIMIT_DEF
LUSERS_DEF='tvu1,tvu2'
LUSERS=[x for x in LUSERS_DEF.split(',') if x]
PORTS_DEF='8001,8002'
PORTS=PORTS_DEF
NPORTS_DEF=[8001,8002]
NPORTS=NPORTS_DEF
DEBUG_ACTIVE_DEF=False
DEBUG_ACTIVE=DEBUG_ACTIVE_DEF


config.plugins.snif = ConfigSubsection()
config.plugins.snif.enable = ConfigBoolean(default=ENABLE_DEF)
config.plugins.snif.limit = ConfigNumber(default=LIMIT_DEF)
config.plugins.snif.users = ConfigText(default=LUSERS_DEF, fixed_size=False, visible_width=VISIBLE_WIDTH)
config.plugins.snif.ports = ConfigText(default=PORTS_DEF, fixed_size=False, visible_width=VISIBLE_WIDTH)
config.plugins.snif.debug = ConfigBoolean(default=DEBUG_ACTIVE_DEF)
config.plugins.snif.version = ConfigSelection(default=VERSION_DEF, choices=VERSION_CHOICES)
if not openatv_like:
  SAVED_SETUP=Screens.Setup.setupdom

DEBUG_FILE='/tmp/snif-debug.log'
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


MIN_CAPTURE_LEN=80
MAX_CAPTURE_LEN=1500
AUTH_RE=re.compile(r'Authorization: Basic (?P<digest>[A-Za-z0-9+/=]+)', re.IGNORECASE)

# con = address+sport+dport
# con -> user
CONS={}
# user -> [con1, con2, ...]
USERS={}

IP32_1 = 0x45000000
IP32_2 = 0x12340000
IP32_3 = 0x40060000
IP_HEADER_1 = struct.pack('!LLL', IP32_1, IP32_2, IP32_3)
TCP_CHECK_URG = 0
TCP_HEADER_2 = struct.pack('!L', TCP_CHECK_URG)

THREAD=None

SOCK = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
SOCK.bind(('',0))
SOCK.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
#SOCK.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

class Sniffer(threading.Thread):
  def __init__(self):
    DEBUG('Init Sniffer!\n')
    threading.Thread.__init__(self)

  def checksum(self, msg):
    s = 0 
    for i in range(0, len(msg), 2):
      w = ord(msg[i]) + (ord(msg[i+1]) << 8 )
      s = s + w
    s = (s>>16) + (s & 0xffff);
    s = s + (s >> 16);  
    s = ~s & 0xffff
    return s

  def reset(self, src, dst, sport, dport, seq, ack):
    ip_header = IP_HEADER_1 + struct.pack('!4s4s', src, dst)

    tcp_source = sport
    tcp_dest = dport
    tcp32_1 = (sport << 16) | dport
    tcp_seq = seq
    tcp_ack_seq = ack
    tcp_hlen_res_flags_wnd = 0x50040000
    tcp_header_1 = struct.pack('!HHLLL' , tcp_source, tcp_dest, tcp_seq, 
        tcp_ack_seq, tcp_hlen_res_flags_wnd)

    psh_tail_value = 0x00060014
    psh_tail = struct.pack('!L', psh_tail_value)
    psh = struct.pack('!4s4s' , src, dst) + psh_tail
    tcp_check = self.checksum(psh + tcp_header_1 + TCP_HEADER_2)

    tcp_urg_ptr = 0
    SOCK.sendto(str(ip_header + tcp_header_1 + struct.pack('H', tcp_check) + struct.pack('!H', tcp_urg_ptr)),
             ('', 0))


  def run(self):
    DEBUG('Sniffing...\n')
    global CONS
    global USERS
    try:
      while(True):
        user = None
        data = SOCK.recvfrom(1600)
        packet = data[0]
        address = data[1]
        header = struct.unpack('!BBHHHBBHBBBBBBBB', packet[:20])
        ihl = (header[0]&0x0f)*4
        total_len = header[2]
        if total_len < MAX_CAPTURE_LEN:
          tcp = struct.unpack('!HHLLBB', packet[ihl:ihl+14])
          dport = tcp[1]
          thl = (tcp[4]>>4)*4
          if dport in NPORTS:
            sport = tcp[0]
            con = str(address[0])+','+str(sport)+','+str(dport)
            if total_len > MIN_CAPTURE_LEN:
#              DEBUG('%s %s %s %s %s %s\n' % (address, ihl, total_len, sport, dport, thl))
              tdata = str(packet[ihl+thl:])
#              DEBUG('TCP data: %s\n' % tdata)
              m = AUTH_RE.search(tdata)
              if m:
                plain = base64.b64decode(m.group('digest'))
                user = plain.split(':')[0]
#                DEBUG('Found user %s\n' % user)
                if user and user in LUSERS:
                  if CONS.get(con, None):
                    DEBUG('Error: connection %s already present!\n' % con)
                  else:
                    DEBUG('Adding %s for %s!\n' % (con, user))
                    if len(USERS.get(user, [])) >= LIMIT:
                      DEBUG('Too many connections for %s, resetting...\n' % user)
                      addresses = struct.unpack('!4s4s', packet[12:20])
                      self.reset(addresses[0], addresses[1], sport, dport, tcp[2]+len(tdata), tcp[3])
                    else:
                      CONS.setdefault(con, user)
                      USERS.setdefault(user, [])
                      USERS[user].append(con)
                else:
                  if user:
                    DEBUG('User %s not limited!\n' % user)
                DEBUG('Cons: %s\n' % CONS)
                DEBUG('Users: %s\n' % USERS)
            else:
              flags = tcp[5]
              rst_or_fin = flags & 0x5
              if rst_or_fin:
                user = CONS.get(con, None)
                if user:
                  DEBUG('Removing %s for %s!\n' % (con, user))
                  try:
                    CONS.pop(con)
                    USERS[user].remove(con)
                    if not USERS.get(user):
                      DEBUG('Last connection for %s, removing user!\n' % user)
                      USERS.pop(user)
                  except:
                    DEBUG('Error: connection %s didn\'t exist for user %s!\n' % (con, user))
                    DEBUG('%s\n' % traceback.format_exc())
                  DEBUG('Cons: %s\n' % CONS)
                  DEBUG('Users: %s\n' % USERS)
                else:
                  DEBUG('Info: connection %s not present!\n' % con)
    except:
      DEBUG('%s\n' % traceback.format_exc())

  def stop(self):
    DEBUG('Stopping...\n')
    DEBUG('STOP!\n')


def reConfig():
  global ENABLE
  global LIMIT
  global LUSERS
  global PORTS
  global NPORTS
  global DEBUG_ACTIVE
  ENABLE = config.plugins.snif.enable.value
  LIMIT = config.plugins.snif.limit.value
  try:
    LUSERS = [x for x in config.plugins.snif.users.value.split(',') if x]
  except:
    config.plugins.snif.users._value = LUSERS_DEF
    LUSERS = [x for x in LUSERS_DEF.split(',') if x]
  PORTS = config.plugins.snif.ports.value
  try:
    NPORTS = [int(x) for x in PORTS.split(',') if x]
  except:
    config.plugins.snif.ports._value = PORTS_DEF
    PORTS = PORTS_DEF
    NPORTS = NPORTS_DEF
  DEBUG_ACTIVE = config.plugins.snif.debug.value
  config.plugins.snif.save()
  if not openatv_like:
    configfile.save()


def onSetupClose(test=None):
  global THREAD
  reConfig()
  if THREAD:
    THREAD.stop()
  if ENABLE:
    THREAD=Sniffer()
    THREAD.daemon=True
    THREAD.start()
  if not openatv_like:
    Screens.Setup.setupdom = SAVED_SETUP


def autoStart(reason, **kwargs):
  print 'Snif autostart!'
  onSetupClose()


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
          name=PLUGIN_NAME,
          description=PLUGIN_DESC,
          where=PluginDescriptor.WHERE_PLUGINMENU,
          icon=PLUGIN_ICON,
          fnc=main)]

