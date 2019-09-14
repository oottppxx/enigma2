from Plugins.Plugin import PluginDescriptor


PLUGIN_VERSION='6.2.0b'
PLUGIN_NAME='ReStart'
PLUGIN_DESC='Stops/Starts the current service'
PLUGIN_ICON='restart.png'


def main(session, **kwargs):
  if session:
    sr = session.nav.getCurrentlyPlayingServiceReference()
    if sr:
      session.nav.stopService()
      session.nav.playService(sr)


def Plugins(**kwargs):
  return [
      PluginDescriptor(
          name=PLUGIN_NAME,
          description=PLUGIN_DESC,
          where=PluginDescriptor.WHERE_PLUGINMENU,
          icon=PLUGIN_ICON,
          fnc=main)]
