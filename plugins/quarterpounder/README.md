# Quarter Pounder.

Attempts to detect a stuck stream and to
restart it.

Join us in the [Enigma2Talk Telegram chatroom](https://t.me/talkenigma2)
to help with testing, provide ideas and all kind of suggestions or comments!

## Description

This plugin subscribes to service events, and when it detects an evEOF (end of
file) it assumes the current playing service got interrupted and restarts it (if
enabled).

## Settings

**"Enable"**
* "Enable or disable."
* Default: True.
* If disabled, the plugin won't try to restart any service. Useful if you're
  seeing too many interruptions for a particular service/provider and want to
  temporarilty disable the plugin without uninstalling it.

**"GUI Check"**
* "Ignores or postpones restarts if using the GUI."
* Default: "Channels (ignore)".
* This setting, if not disabled, conditions the plugin to not try and restart
  the current service when it detects a failure if the GUI is in use - this
  is to improve GUI navigation, namely of bouquets if the current service is a
  very stuck stream.
  It can either "ignore" the evEOF event completely (and rely on further events
  being triggered for broken services) or it can "postpone" the restart until it
  detects the GUI interaction is over.
  For GUI interactions, it can be restricted to have this behavior only during
  bouquet navigation ("Channels"), any usual menu/submenu ("InfoBar"), or "Any"
  GUI activity (some plugins can trigger this even in the background, so some
  care is needed when using this option, as it can disable the plugin entirely).

**"Ignore Strings (comma separated list)"**
* "Ignore services which contain any of the strings in their URL and/or description (empty resets to default)."
* Default: "mp4,mkv".
* If the current playing service matches any of the strings in the list, the
  plugin won't restart it. Typically we don't want to restart VOD streams, which
  are, in my experience, URLs for mp4 or mkv files, hence the default setting.
  If you have other types of VOD URLs (or even regular live streams from a
  specific provider), as long as you can match them uniquely here, feel free to
  add to the list so the plugin ignores those as well.
  The match is case insensitive.

**"Restart Delay (seconds)"**
* "Minimum interval between restarts (either our own or due to zapping)."
* Default: 0 seconds.
* This controls how long to refrain from restarting a service if we have already
  done a restart (of that same service) before. With 0, we always try to restart
  the service, but this can be taxing on the CPU. If you feel like experimenting
  with this setting, try 1 second increments until you find a value that works
  for you and your providers.

**"Restart Indicator"**
* "How to indicate a restart has occurred."
* Default: "Default".
* With the "default" setting, the plugin won't do anything specific, so whatever
  is configured on the Enigma2 system will activate; typically this means that
  you'll see the service infobar popping up, if this behaviour wasn't disabled
  in the main box settings.
  With the "none" setting, the plugin will try and disable the service infobar
  to display during restarts, independently of what's configured in the main box
  settings.


**"Stuck Channels Hack"**
* "Hack around stuck DVB channels."
* Default: "".
* This is also a comma separated list of strings. If any of the string matches
  (in a case insensitive way) with the current service that just started, the
  plugin will try and force restart the service _once_ after some time (see the
  next setting). After this the plugin behaves normally and it will restart the
  service again only if it detects a failure.
  Does it sound crazy that a restart is forced on a service that was just
  started? Yes, but apparently that's necessary in some cases, even DVB
  services - hey, it's a hack!

**"Stuck Channels Hack Delay"**
* "Hack around stuck DVB channels."
* Default: 2500 ms / 2.5 seconds.
* How long after a service that matches one of the strings in the previous
  setting) starts before we force re-start it once.

**"Debug"**
* "Activate debug log."
* Default: False.
* If set to True, debug information is recorded under the
  /tmp/quarterpounder-debug.log file.

