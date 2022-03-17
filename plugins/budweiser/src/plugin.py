import json
import os
import signal
import sys
import time
import traceback

from fcntl import ioctl

from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen


PLUGIN_VERSION='6.2.2c'
PLUGIN_NAME='Budweiser'
PLUGIN_DESC='Dub weiser'
PLUGIN_ICON='budweiser.png'
PLUGIN_PATH='Extensions/Budweiser'
PLUGINS_PATH='/usr/lib/enigma2/python/Plugins'
DEBUG_FILE='/tmp/budweiser-debug.log'
SOURCES_FILE=PLUGINS_PATH+'/'+PLUGIN_PATH+'/sources.json'

AUDIO_FD=0
AUDIO_PROCESS=None
TITLE_DEF="Sources"
DEVICE_DEF="alsasink device=hw:0"
EXTRA_OPS=["CTRL^Z"]

def debug(s):
  try:
    os.stat(DEBUG_FILE)
  except:
    pass
  else:
    t = time.ctime()
    with open(DEBUG_FILE, 'a+') as f:
      f.write('%s %s' % (t, s))


def info(session, text=None, callback=None):
  if text:
    if callback:
      session.openWithCallback(callback, MessageBox, text, MessageBox.TYPE_INFO, simple=True)
    else:
      session.open(MessageBox, text, MessageBox.TYPE_INFO, simple=True)
      

def audioFind():
  global AUDIO_FD
  try:
    if AUDIO_FD:
      try:
        debug('audioFind() checking if fd %s is still valid...\n' % AUDIO_FD)
        if ioctl(AUDIO_FD, 0x6f0c) == 0:
          debug('audioFind() fd %s is still valid...\n' % AUDIO_FD)
          return AUDIO_FD
      except:
        debug('audioFind() fd %s is invalid, searching...\n' % AUDIO_FD)
    pid = os.getpid()
    ldir = os.listdir('/proc/%s/fd' % pid)
    ldir.append('0')
    debug('LDIR: %s\n' % ldir)
    for fd in ldir:
      try:
        ls = os.readlink('/proc/%s/fd/%s' % (pid, fd))
      except:
        pass
      debug('LS: %s\n' % ls)
      if '/dev/dvb/adapter' in ls and 'audio' in ls:
        debug('audioFind() found fd %s...\n' % fd)
        AUDIO_FD=int(fd)
        break
  except:
    debug('audioFind() exception!\n')
    debug(traceback.format_exc())
  return int(fd)


def audioStop():
  try:
    fd = audioFind()
    debug('audioStop(): %s\n' % str(fd))
    ioctl(fd, 0x6f01)
  except:
    debug('audioStop() exception!\n')
    debug(traceback.format_exc())


def audioStart():
  try:
    fd = audioFind()
    debug('audioStart(): %s\n' % str(fd))
    ioctl(fd, 0x6f02)
  except:
    debug('audioStart() exception!\n')
    debug(traceback.format_exc())


def audioKill():
  debug('Kill audioProcess: %s\n' % str(AUDIO_PROCESS))
  if AUDIO_PROCESS:
    try:
      os.kill(AUDIO_PROCESS, signal.SIGKILL)
      os.killpg(AUDIO_PROCESS, signal.SIGKILL)
      os.waitpid(AUDIO_PROCESS, 0)
      os.system("sync && echo 3 > /proc/sys/vm/drop_caches")
    except:
      debug('audioKill() os.kill|killpg|waitpid() exception!\n')
      debug(traceback.format_exc())
  

def audioProcess(argv):
  global AUDIO_PROCESS
  debug('Run audioProcess: %s\n' % str(argv))
  audioKill()
  try:
    os.system("sync && echo 3 > /proc/sys/vm/drop_caches")
    AUDIO_PROCESS = os.fork()
    if not AUDIO_PROCESS:
      debug('Child audioProcess() execv(): %s\n' % str(argv))
      os.setsid()
      os.execv(argv[0], argv)
  except:
    debug('Parent audioProcess() forking exception: %s\n' % str(argv))
    debug(traceback.format_exc())


def runCommand(op=None, data=None, opTypes=None, device=None):
  debug('runCommand(): %s\n' % op)
  debug('data: %s\n' % str(data))
  debug('opTypes: %s\n' % str(opTypes))
  debug('device: %s\n' % str(device))
  if op in 'CTRL^Z':
    try:
      audioKill()
      audioStart()
    except:
      debug('ok() audioKill|Start() exception!\n')
      debug(traceback.format_exc())
    return True
  try:
    data = data.get(op, None)
    opType, url, comment, audioOp, selectExits = data
    debug('runCommand() opType: %s\n' % str(opType))
    debug('runCommand() url: %s\n' % str(url))
    debug('runCommand() comment: %s\n' % str(comment))
    debug('runCommand() audioOp: %s\n' % str(audioOp))
    debug('runCommand() selectExits: %s\n' % str(selectExits))
    if audioOp == 1:
      audioStop()
    elif audioOp == 2:
      audioStart()
    argv = opTypes.get(opType, None)
    if argv:
      # Keep the order, so we can include %(DEVICE)s in %(URL)s.
      argv = [str(x) % {"URL": url, "DEVICE": device} for x in argv]
      argv = [str(x) % {"DEVICE": device} for x in argv]
      audioProcess(argv)
    if selectExits:
      return True
    else:
      return False
  except:
    debug('runCommand() exception!\n')
    debug(traceback.format_exc())
  debug('runCommand() exit!\n')
  return True


class SourceSelectionScreen(Screen):
  skin = """<screen position="center,center" size="200,400">
            <widget name="myList" position="25,25" size="150,350"/>
            </screen>"""
  def __init__(self, session, title=None, sources=None):
    self.session = session
    Screen.__init__(self, session)
    if sources.get("title", False):
      Screen.setTitle(self, title=sources.get("title", ""))
    elif title:
      Screen.setTitle(self, title=title)
    self.device = sources.get("device", DEVICE_DEF)
    self.opTypes = sources.get("optypes", None)
    self.sources = sources.get("data", None)
    self.sources_names = []
    self.sources_hash = {}
    if not self.sources:
      info('Error retrieving possible sources!')
      self.sources = None
      return
    debug('sources: %s\n' % self.sources)
    for entry in self.sources:
      self.sources_names.append(entry[0])
      self.sources_hash[entry[0]] = entry[1:]
    self.sources_names = EXTRA_OPS + self.sources_names
    debug('sources_names: %s\n' % self.sources_names)
    debug('sources_hash: %s\n' % self.sources_hash)
    self.myList =  MenuList(self.sources_names)
    self['myList'] = self.myList
    self['myActionMap'] = ActionMap(['WizardActions'],
        {
          'back': self.exit,
          'ok': self.ok,
       }, -1)

  def exit(self):
    self.close()

  def ok(self):
    try:
      cur = self.myList.getCurrent()
      debug('ok pressed, cur: %s\n' % cur)
      if runCommand(op=cur, data=self.sources_hash, opTypes=self.opTypes, device=self.device):
        self.exit()
    except:
      debug('ok() runCommand() exception!\n')
      debug(traceback.format_exc())
      self.exit()


def _byteify(data, ignore_dicts=False):
  if isinstance(data, str):
    return data
  if isinstance(data, list):
    return [ _byteify(item, ignore_dicts=True) for item in data ]
  if isinstance(data, dict) and not ignore_dicts:
    return {
      _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
      for key, value in data.items()
    }
  if str(type(data)) == "<type 'unicode'>":
    return data.encode('utf-8')
  return data


def getJsonData(filename):
  with open(filename, 'r') as f:
    data = _byteify(json.loads(f.read(), object_hook=_byteify), ignore_dicts=True)
  debug('data: %s\n' % data)
  return data
    

def main(session, **kwargs):
  try:
    sources = getJsonData(SOURCES_FILE)
  except:
    info(session, text='Error reading sources file %s!' % SOURCES_FILE)
    debug('main() getJsonData() exception!\n')
    debug(traceback.format_exc())
    return
  session.open(SourceSelectionScreen, title=TITLE_DEF, sources=sources)


def Plugins(**kwargs):
  return PluginDescriptor(
      name=PLUGIN_NAME,
      description=PLUGIN_DESC,
      where=PluginDescriptor.WHERE_PLUGINMENU,
      icon=PLUGIN_ICON,
      fnc=main)

