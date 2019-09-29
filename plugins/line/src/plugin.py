from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import InfoBar


PLUGIN_VERSION='6.2.0b'
PLUGIN_NAME='Line'
PLUGIN_DESC='Toggles VBI Line'
PLUGIN_ICON='line.png'

HIDE_DEF=True
HIDE=HIDE_DEF
SERVICE=''

def main(session, **kwargs):
  global HIDE
  global SERVICE
  if session:
    service = session.nav.getCurrentlyPlayingServiceReference().toString()
    if service != SERVICE:
      SERVICE = service
      HIDE = HIDE_DEF
    if HIDE:
      InfoBar.instance.hideVBILineScreen.hide()
    else:
      InfoBar.instance.hideVBILineScreen.show()
    HIDE=not HIDE


def Plugins(**kwargs):
  return [
      PluginDescriptor(
          name=PLUGIN_NAME,
          description=PLUGIN_DESC,
          where=PluginDescriptor.WHERE_PLUGINMENU,
          icon=PLUGIN_ICON,
          fnc=main)]
