from Plugins.Plugin import PluginDescriptor
from Screens.InfoBarGenerics import Seekbar


PLUGIN_VERSION='6.2.0a'
PLUGIN_NAME='SnackBar'
PLUGIN_DESC='Invokes Seekbar'
PLUGIN_ICON='snackbar.png'


def main(session, **kwargs):
  session.open(Seekbar, True)


def Plugins(**kwargs):
  return [
      PluginDescriptor(
          name=PLUGIN_NAME,
          description=PLUGIN_DESC,
          where=PluginDescriptor.WHERE_PLUGINMENU,
          icon=PLUGIN_ICON,
          fnc=main)]
