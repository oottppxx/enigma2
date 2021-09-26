from __future__ import print_function

openatv_like = True
try:
  # This works in OpenATV (and similar code bases) but fails on OpenPLi.
  # The particular import might not be relevant for the actual plugin.
  from Screens.EpgSelection import SingleEPG
except:
  openatv_like = False

# Quick fix for Vix
try:
  import boxbranding
  if "openvix" in boxbranding.getImageDistro().lower():
    openatv_like = True
except:
  pass

import contextlib
import re
import socket
try:
  from StringIO import StringIO
except ImportError:
  from io import StringIO
import sys
import time
import threading
import traceback

from types import ModuleType

from Components.config import config, ConfigBoolean, ConfigNumber, ConfigSelection, ConfigSubsection
from Plugins.Plugin import PluginDescriptor
if openatv_like:
  from Screens.Setup import Setup
else:
  import Screens.Setup
  import xml.etree.cElementTree
  from Components.config import configfile

PLUGIN_VERSION='6.2.1g'
PLUGIN_NAME='PyShell'
PLUGIN_DESC='E2 Python Shell'
PLUGIN_ICON='pyshell.png'
PLUGIN_PATH='Extensions/PyShell'
if not openatv_like:
  PLUGIN_PATH='/usr/lib/enigma2/python/Plugins/' + PLUGIN_PATH
SETUP_KEY='pyshell'


VERSION_DEF=PLUGIN_VERSION
VERSION_CHOICES=[(VERSION_DEF, VERSION_DEF)]
HOST_LOOPBACK='127.0.0.1'
HOST_ALL='0.0.0.0'
HOST=HOST_LOOPBACK
LOOPBACK_ONLY_DEF=True
LOOPBACK_ONLY=LOOPBACK_ONLY_DEF
PORT_DEF=8089
PORT=PORT_DEF
DEBUG_DEF=False
DEBUG=DEBUG_DEF

config.plugins.pyshell = ConfigSubsection()
config.plugins.pyshell.loopback = ConfigBoolean(default=LOOPBACK_ONLY_DEF)
config.plugins.pyshell.port = ConfigNumber(default=PORT_DEF)
config.plugins.pyshell.version = ConfigSelection(default=VERSION_DEF, choices=VERSION_CHOICES)
config.plugins.pyshell.debug = ConfigBoolean(default=DEBUG_DEF)
if not openatv_like:
  SAVED_SETUP=Screens.Setup.setupdom

FILE_RE=r'![aw]\s*(?P<NAME>[^\s]+)\s*$'
# Negative in slices is trouble, apparently...
# We can live without it.
#NUM_RE=r'([+-]{0,1}[0-9]+){0,1}'
NUM_RE=r'([0-9]+){0,1}'
ADDR_RE=r'![dmr](\s*(?P<F>'+NUM_RE+r'){0,1}(\s*,\s*(?P<S>'+NUM_RE+r')){0,1}(\s*,\s*(?P<T>'+NUM_RE+r')){0,1}){0,1}\s*$'
PROMPT='>>> '
CMD_APPEND='!a'
CMD_DISPLAY='!d'
CMD_EXEC='!e'
CMD_EXIT='!x'
CMD_HELP='!h'
CMD_MOVE='!m'
CMD_QUIT='!q'
CMD_REMOVE='!r'
CMD_WRITE='!w'
BANNER='%s for help\n' % CMD_HELP
HELP_MSG="""Commands:

!d ADDR2   displays the in-memory lines between [n1,n2[
!e         executes the in-memory lines
!r ADDR2   removes the in-memory lines between [n1,n2[
!m ADDR3   moves the in-memory lines between [n1,n2[ to line n3
!a FILE    appends the lines in FILE to the in-memory lines
!w FILE    writes the in-memory lines to FILE
!q         quits the session but keeps the in-memory lines
!x         exits the session and clears the in-memory lines
!h         displays this help message

Arguments:

FILE       expects a path to a file
ADDRn      are addresses, expected in the form: n1,n2,n3
ADDR2      uses n1 and n2; n3 is ignored if present.
ADDR3      uses all of n1, n2, and n3
If any of n1, n2, or n3 are ommitted, adequate defaults are assumed.


Any other input is appended to the in-memory lines, as is,
no validation is performed!

"""
#ADDR1      uses n1 only; n2 and n3 are ignored if present

DEBUG_FILE='/tmp/pyshell-debug.log'
def debug(s):
  if DEBUG:
    f = open(DEBUG_FILE, 'a+')
    f.write(s+'\n')
    f.close()
    print(s)

RECV_BUFFER=4096
RECV_TIMEOUT=3600 # 1 hour
THREAD=None
SESSION=None
MODULE=None
SCRIPT=[]


class PYSHELLd(threading.Thread):
  def __init__(self, host=HOST, port=PORT):
    debug('Init PYSHELLd!')
    self.host = host
    self.port = port
    debug('Host: %s, port: %s\n' % (HOST, PORT))
    try:
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
      self.sock.bind((self.host,self.port))
    except:
      debug('Can\'t bind to %d port!' % PORT)
    else:
      threading.Thread.__init__(self)

  def run(self):
    global MODULE
    global SCRIPT
    debug('Run!')
    try:
      self.sock.listen(1)
    except:
      debug('Can\'t listen on %d port!' % PORT)
    else:
      debug('Listen OK!')
      self.sock.settimeout(None)
      while True:
        conn, addr = self.sock.accept()
        debug('ACCEPT!')
        conn.settimeout(RECV_TIMEOUT)
        try:
          conn.send(BANNER)
        except:
          try:
            conn.send(bytes(BANNER, 'utf8'))
          except:
            debug('BANNER MSG ERROR!')
            break
        while True:
          try:
            conn.send(PROMPT)
          except:
            try:
              conn.send(bytes(PROMPT, 'utf8'))
            except:
              debug('PROMPT MSG ERROR!')
              break
          data = ''
          try:
            cmd = conn.recv(RECV_BUFFER)
            if type(cmd) != str:
              cmd = cmd.decode()
          except:
            debug('RECV ERROR!')
            sys.last_traceback = None
            break
          debug('RECV!')
          try:
            fun, err, brk = self.dispatchCmd(cmd)
            if fun:
              try:
                out = fun(cmd)
                debug('FUN OUTPUT: %s\n' % out)
                if out is not None:
                  try:
                    conn.send(out)
                  except:
                    conn.send(bytes(out, 'utf8'))
              except:
                debug(err)
              try:
                sys.exc_clear()
              except:
                pass
              #sys.last_traceback = None
              if brk:
                break
              continue
            debug('APPENDING TO SCRIPT!')
            SCRIPT.append(str(cmd))
          except:
            debug('Dispatch/Append Error!')
            print(traceback.format_exc())
            conn.close()
            sys.last_traceback = None
            break
          else:
            debug('OK!')
        debug('CLOSING!')
        try:
          conn.send('Closing...\n')
        except:
          try:
            conn.send(bytes('Closing...\n', 'utf8'))
          except:
            debug('CLOSING MSG ERROR!')
        conn.close()
        sys.last_traceback = None

  def dispatchCmd(self, cmd=None):
    all_cmds={
        CMD_APPEND: (self.cmdAppend, 'CMD_APPEND MSG ERROR', False),
        CMD_DISPLAY: (self.cmdDisplay, 'CMD_DISPLAY MSG ERROR', False),
        CMD_EXEC: (self.cmdExec, 'CMD_EXEC MSG ERROR', False),
        CMD_EXIT: (self.cmdExit, 'CMD_EXIT MSG ERROR', True),
        CMD_HELP: (self.cmdHelp, 'CMD_HELP MSG ERROR', False),
        CMD_MOVE: (self.cmdMove, 'CMD_MOVE MSG ERROR', False),
        CMD_QUIT: (self.cmdQuit, 'CMD_QUIT MSG ERROR', True),
        CMD_REMOVE: (self.cmdRemove, 'CMD_REMOVE MSG ERROR', False),
        CMD_WRITE: (self.cmdWrite, 'CMD_WRITE MSG ERROR', False),
    }
    if cmd:
#      for c, t in all_cmds.iteritems():
      for c, t in iter(all_cmds.items()):
        if re.match(c, cmd):
          return t
    return (None, None, None)

  def parseAddress(self, cmd=None):
    if cmd:
      m = re.match(ADDR_RE, cmd)
      if m:
        m = m.groupdict()
        f = m.get('F')
        s = m.get('S')
        t = m.get('T')
        if f:
          f = int(f)
        else:
          f = None
        if s:
          s = int(s)
        else:
          s = None
        if t:
          t = int(t)
        else:
          t = None
        return (None, f, s, t)
      return ('invalid address', None, None, None)
    return (None, None, None, None)

  @contextlib.contextmanager
  def stdIO(self, output=None):
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    if not output:
      output = StringIO()
    sys.stdout = output
    sys.stderr = output
    try:
      yield output
    finally:
      sys.stdout = old_stdout
      sys.stderr = old_stderr
      output.close()

  def parseReadFile(self, cmd=None):
    if cmd:
      m = re.match(FILE_RE, cmd)
      if m:
        m = m.groupdict()
        name = m.get('NAME')
        contents = ''
        if name:
          f = open(name, 'r')
          contents = f.read()
          f.close()
          return (None, name, contents)
      return ('invalid name', None, None)
    return (None, None, None)

  def parseWriteFile(self, cmd=None):
    if cmd:
      m = re.match(FILE_RE, cmd)
      if m:
        m = m.groupdict()
        name = m.get('NAME')
        if name:
          f = open(name, 'w')
          f.write(''.join(SCRIPT))
          f.close()
          return None
      return 'invalid name'
    return None

  def cmdAppend(self, cmd=None):
    global SCRIPT
    try:
      error, name, contents = self.parseReadFile(cmd)
      if error:
        return 'Error: %s!\n' % error
      if contents:
        SCRIPT.extend([x+'\n' for x in contents.split('\n')])
        return ''
      return 'Nothing to append from %s.\n' % name
    except:
      return traceback.format_exc()

  def cmdWrite(self, cmd=None):
    try:
      if not SCRIPT:
        return 'Nothing to write!\n'
      error = self.parseWriteFile(cmd)
      if error:
        return 'Error: %s!\n' % error
    except:
      return traceback.format_exc()

  def cmdDisplay(self, cmd=None):
    try:
      error, f, s, t = self.parseAddress(cmd)
      if error:
        return 'Error: %s!\n' % error
      if f is None:
        f = 0
      if s is None:
        s = len(SCRIPT)
###   Simply using a slice, the indexes stop reflecting the originals
###   We need to add f to get the real indexes, and adjust f to 0 if negative
      f = max(f, 0)
      return ''.join([str(idx+f)+':\t'+str(val) for idx,val in enumerate(SCRIPT[f:s])])
    except:
      return traceback.format_exc()

  def cmdExec(self, cmd=None):
    global MODULE
    msg = ''
    try:
      if not MODULE:
        MODULE = ModuleType('Sandbox', 'Sandbox module')
      MODULE.__dict__['session'] = SESSION
      with self.stdIO() as output:
        try:
          exec(''.join(SCRIPT), MODULE.__dict__)
        except:
          pass
        msg = output.getvalue()
      return 'StdOut/StdErr:\n' + msg + 'Last Unhandled Exception:\n' + traceback.format_exc()
    except:
      return traceback.format_exc()

  def cmdHelp(self, cmd=None):
    try:
      return HELP_MSG
    except:
      return traceback.format_exc()

  def cmdMove(self, cmd=None):
    global SCRIPT
    try:
      if not SCRIPT:
        return 'Error: nothing to remove!\n'
      error, f, s, t = self.parseAddress(cmd)
      if error:
        return 'Error: %s!\n' % error
      # move the last line
      if f is None and s is None:
        f = len(SCRIPT)-1
        s = len(SCRIPT)
      # move line n2
      elif f is None and s is not None:
        f = s
        s = f+1
      # move line n1
      elif f is not None and s is None:
        s = f+1
      # we swap n1 and n2 if necessary
      if f > s:
        x = f
        f = s
        s = x
      if t is None:
        if f == len(SCRIPT)-1:
#          s1 = [f:]
#          s2 = [:f]
#          SCRIPT = s1 + s2
#          return ''
          t = 0
        else:
          t = s
      if t >= f and t < s:
        return 'Error: destination overlaps move region!\n'
      block = SCRIPT[f:s]
      if t < f:
        s1 = SCRIPT[0:t]
        s2 = SCRIPT[t:f]
        s3 = SCRIPT[s:]
        SCRIPT = s1 + block + s2 + s3
      else:
        s1 = SCRIPT[:f]
        s2 = SCRIPT[s:t+1]
        s3 = SCRIPT[t+1:]
        SCRIPT = s1 + s2 + block + s3
      return ''
    except:
      return traceback.format_exc()

  def cmdRemove(self, cmd=None):
    global MODULE
    global SCRIPT
    try:
      if not SCRIPT:
        return 'Error: nothing to remove!\n'
      error, f, s, t = self.parseAddress(cmd)
      if error:
        return 'Error: %s!\n' % error
      # delete the last line
      if f is None and s is None:
        f = len(SCRIPT)-1
        s = len(SCRIPT)
      # delete line n2
      elif f is None and s is not None:
        f = s
        s = f+1
      # delete line n1
      elif f is not None and s is None:
        s = f+1
      # default case is delete from line n1 up to line n2
      # and it forces deletion of more than 1 line (or the
      # entire script) to be explicit
      # we swap n1 and n2 if necessary
      if f > s:
        t = f
        f = s
        s = t
#      SCRIPT.__delslice__(f,s)
      n = s-f
      while n:
        SCRIPT.__delitem__(f)
        n -= 1
      if not SCRIPT:
        MODULE = None
      return ''
    except:
      return traceback.format_exc()

  def cmdQuit(self, cmd=None):
    try:
      return 'Quitting...\n'
    except:
      return traceback.format_exc()

  def cmdExit(self, cmd=None):
    global MODULE
    global SCRIPT
    try:
      MODULE = None
      SCRIPT = []
      return 'Exiting & clearing...\n'
    except:
      return traceback.format_exc()

  def stop(self):
    debug('STOP!')
    self.sock.shutdown(socket.SHUT_RDWR)
    self.sock.close()


def reConfig():
  global PORT
  global HOST
  global LOOPBACK_ONLY
  global DEBUG
  LOOPBACK_ONLY = config.plugins.pyshell.loopback.value
  if LOOPBACK_ONLY:
    HOST = HOST_LOOPBACK
  else:
    HOST = HOST_ALL
  PORT = config.plugins.pyshell.port.value
  if PORT < 1024 or PORT > 65535:
    config.plugins.pyshell.port._value = PORT_DEF
    PORT = config.plugins.pyshell.port.value
  DEBUG = config.plugins.pyshell.debug.value
  config.plugins.pyshell.save()
  if not openatv_like:
    configfile.save()


def onSetupClose(test=None):
  global THREAD
  reConfig()
  if THREAD:
    THREAD.stop()
  THREAD=PYSHELLd(host=HOST, port=PORT)
  THREAD.daemon=True
  THREAD.start()
  if not openatv_like:
    Screens.Setup.setupdom = SAVED_SETUP


def autoStart(reason, **kwargs):
  print('PyShell autostart!')
  onSetupClose()


def sessionStart(reason, **kwargs):
  global SESSION
  SESSION=kwargs.get('session')


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
