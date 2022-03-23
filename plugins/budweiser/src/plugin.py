import json
import os
import signal
import sys
import time
import traceback

from fcntl import ioctl

from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen


PLUGIN_VERSION='6.2.3m'
PLUGIN_NAME='Budweiser'
PLUGIN_DESC='Dub weiser'
PLUGIN_ICON='budweiser.png'
PLUGIN_PATH='Extensions/Budweiser'
PLUGINS_PATH='/usr/lib/enigma2/python/Plugins'
DEBUG_FILE='/tmp/budweiser-debug.log'
SOURCES_FILE=PLUGINS_PATH+'/'+PLUGIN_PATH+'/sources.json'

WIDTH_DEF=200
THEIGHT_DEF=50
LHEIGHT_DEF=300
MARGIN_DEF=25
TFSIZE_DEF=25
LFSIZE_DEF=20
FONT_DEF='Regular'

AUDIO_FD=0
AUDIO_PROCESS=None
TITLE_DEF="Sources"
DEVICE_DEF="alsasink device=hw:0"
MIN_BUFFERS=0
MAX_BUFFERS=2000
BUFFERS_BIG_STEP=100
BUFFERS_SMALL_STEP=10
BUFFERS_DEF=100
BUFFERS=BUFFERS_DEF
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
  global AUDIO_PROCESS
  debug('Kill audioProcess: %s\n' % str(AUDIO_PROCESS))
  if AUDIO_PROCESS:
    try:
      os.kill(AUDIO_PROCESS, signal.SIGKILL)
      os.killpg(AUDIO_PROCESS, signal.SIGKILL)
      os.waitpid(AUDIO_PROCESS, 0)
      os.system("sync && echo 3 > /proc/sys/vm/drop_caches")
      AUDIO_PROCESS = None
    except:
      debug('audioKill() os.kill|killpg|waitpid() exception!\n')
      debug(traceback.format_exc())
  

def audioProcess(argv):
  global AUDIO_PROCESS
  debug('Run audioProcess: %s\n' % str(argv))
  try:
    audioKill()
    os.system("sync && echo 3 > /proc/sys/vm/drop_caches && echo 1 > /proc/sys/vm/overcommit_memory")
    AUDIO_PROCESS = os.fork()
    if not AUDIO_PROCESS:
      debug('Child audioProcess() argv: %s\n' % str(argv))
      os.closerange(3,1024)
      os.setsid()
      debug('Child audioProcess() execv(): %s\n' % str(argv))
      os.execv(argv[0], argv)
    debug('Parent audioProcess() fork(): %s\n' % str(AUDIO_PROCESS))
  except:
    debug('Parent audioProcess() forking exception: %s\n' % str(argv))
    debug(traceback.format_exc())
  os.system("sync && echo 3 > /proc/sys/vm/drop_caches && echo 0 > /proc/sys/vm/overcommit_memory")


def runCommand(op=None, data=None, opTypes=None, device=None, buffers=BUFFERS_DEF):
  debug('runCommand(): %s\n' % op)
  debug('data: %s\n' % str(data))
  debug('opTypes: %s\n' % str(opTypes))
  debug('device: %s\n' % str(device))
  debug('buffers: %s\n' % str(buffers))
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
      # Keep the order, so we can include %(DEVICE)s and %(BUFFERS)s in %(URL)s.
      argv = [str(x) % {"URL": url, "DEVICE": device, "BUFFERS": buffers} for x in argv]
      argv = [str(x) % {"DEVICE": device, "BUFFERS": buffers} for x in argv]
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
  def __init__(self, session, title=None, sources=None):
    WIDTH=sources.get("skin_width", WIDTH_DEF)
    THEIGHT=sources.get("skin_text_height", THEIGHT_DEF)
    LHEIGHT=sources.get("skin_list_height", LHEIGHT_DEF)
    MARGIN=sources.get("skin_margins", MARGIN_DEF)
    TFSIZE=sources.get("skin_text_font_size", TFSIZE_DEF)
    LFSIZE=sources.get("skin_list_font_size", LFSIZE_DEF)
    FONT=sources.get("skin_font_name", FONT_DEF)
    skin_geometry={
      'SWIDTH': WIDTH, 'SHEIGHT': THEIGHT+LHEIGHT+2*MARGIN,
      'TLEFT': MARGIN, 'TTOP': MARGIN, 'TWIDTH': WIDTH-2*MARGIN, 'THEIGHT': THEIGHT,
      'FONT': FONT, 'TFSIZE': TFSIZE, 'LFSIZE': LFSIZE,
      'LLEFT': MARGIN, 'LTOP': MARGIN+THEIGHT, 'LWIDTH': WIDTH-2*MARGIN, 'LHEIGHT': LHEIGHT,
    }
    self.skin = """<screen position="center,center" size="%(SWIDTH)d,%(SHEIGHT)d">
        <widget source="myText" render="Label" position="%(TLEFT)d,%(TTOP)d" size="%(TWIDTH)d,%(THEIGHT)d" font="%(FONT)s;%(TFSIZE)d"/>
        <widget name="myList" position="%(LLEFT)d, %(LTOP)d" size="%(LWIDTH)d,%(LHEIGHT)d" font="%(FONT)s;%(LFSIZE)d"/>
        </screen>""" % skin_geometry
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
    self['myText'] = StaticText('Buf.: %s' % str(BUFFERS))
    self['myActionMap'] = ActionMap(['WizardActions', 'ShortcutActions', 'TextEntryActions'],
        {
          'back': self.exit,
          'ok': self.ok,
          'nextBouquet': self.bigIncreaseBuffers,
          'prevBouquet': self.bigDecreaseBuffers,
          'deleteForward': self.smallIncreaseBuffers,
          'deleteBackward': self.smallDecreaseBuffers,
       }, -1)

  def exit(self):
    self.close()

  def ok(self):
    try:
      cur = self.myList.getCurrent()
      debug('ok pressed, cur: %s\n' % cur)
      if runCommand(op=cur, data=self.sources_hash, opTypes=self.opTypes, device=self.device, buffers=BUFFERS):
        self.exit()
    except:
      debug('ok() runCommand() exception!\n')
      debug(traceback.format_exc())
      self.exit()
      
  def increaseBuffers(self, step=BUFFERS_BIG_STEP):
    global BUFFERS
    debug('increaseBuffers() step: %s!\n' % str(step))
    try:
      if BUFFERS < MAX_BUFFERS:
        BUFFERS+=step
        if BUFFERS > MAX_BUFFERS:
          BUFFERS=MAX_BUFFERS
        self['myText'].setText('Buf.: %s' % str(BUFFERS))
    except:
      debug('increaseBuffers() exception!\n')
      debug(traceback.format_exc())
      
  def decreaseBuffers(self, step=BUFFERS_BIG_STEP):
    global BUFFERS
    debug('decreaseBuffers() step: %s!\n' % str(step))
    try:
      if BUFFERS > MIN_BUFFERS:
        BUFFERS-=step
        if BUFFERS<MIN_BUFFERS:
          BUFFERS=MIN_BUFFERS
        self['myText'].setText('Buf.: %s' % str(BUFFERS))
    except:
      debug('decreaseBuffers() exception!\n')
      debug(traceback.format_exc())


  def bigIncreaseBuffers(self):
    self.increaseBuffers(step=BUFFERS_BIG_STEP)


  def bigDecreaseBuffers(self):
    self.decreaseBuffers(step=BUFFERS_BIG_STEP)


  def smallIncreaseBuffers(self):
    self.increaseBuffers(step=BUFFERS_SMALL_STEP)


  def smallDecreaseBuffers(self):
    self.decreaseBuffers(step=BUFFERS_SMALL_STEP)


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

