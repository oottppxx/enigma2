* Absolut is a VODka plugin, supporting XCAPI.

* AutoOff attempts to stop any service after the box goes to standby, and optionally
  tries to resume the service afterwards - apparently some images don't do it by
  default, so if you want to confirm, just activate debug and check the debug log.

* BigMac attempts to monitor IPTV streams and restart them if they get stuck.

* Frenchs adds some spice to Heinz (see below), marking catchup supporting channels
  as the M3U download is proxied through it; it supports XCAPI and VAPI.

* Heinz is a "ketchup" plugin, supporting XCAPI and VAPI.

* Innocent is a local M3U proxy for SmoothStreams.

* Line is a plugin that automatically hides the VBI line covering screen (black line
  at the top of the image) for all services. If the need arises to toggle it within
  a service, just invoke the plugin manually (or via hotkey, as you wish).

* McDonnells is an events lister/zapper for SmoothStreams and VAPI MatchCenter.

* MiracleWhip is a plugin to edit Suls/IPTVBouquetMaker/E2m3u2bouquet provider configs
  via the webbrowser.

* PyShell is a plugin for developers/coders - it provides a very simple Python
  shell with access to the Enigma2 runtime environment, so small (or not so small)
  snippets of code can be tested and experimented with while avoiding crashes.

* ReStart is a trivial plugin that stops/starts the current service. No more need
  to zap out/in.

* SnackBar is a trivial plugin that invokes the seek bar; apparently it's required
  as some distros have invoking the seek bar broken via hotkey.

* Subway is a plugin to display subscription info, if the service supports it; it
  should work for both XCAPI and VAPI.

Plugin release versions have 3 fields, major.minor.update, the major and minor
being numeric and the update being alfanumeric.

For most plugins, the major and minor release numbers track the corresponding fields of
the version of the OpenATV system where they were developed (currently OpenATV 6.2).

The update field is generally (but not always) some number followed by one or more
letters; numbers are bumped up when major changes are made to the code; letters are
bumped up when any fix is applied or reflect some other feature (e.g., alfa, beta).

For minor updates, the major/minor release tracking isn't expected to change, even
if the current system has evolved - let me know about innaccuracies.

Typically, the README files for each plugin/script will provide the necessary information
regarding where they were developed/tested, so one can make an educated guess if they'd
work on a particular system. In the end, there's nothing like trying it out. OpenATV and
OpenPLi are particularly targeted, but compatible distributions might also work
(e.g., WooshBuild, OpenViX, ..., just make sure they're up to date!)


Special thanks and greetings to:

* folks in PMC:Enigma (now extinct), namely @falleen, @BillHicks, @Bill, @corkman

* folks in DeathStar (now extinct), namely @agentsmith1, @SomeKewlName

* folks in Enigma2Talk, namely @danny187, @DutchDude6X, @duoduo80

Join us in the [Enigma2Talk Telegram chatroom](https://t.me/talkenigma2)
to help with testing, provide ideas and all kind of suggestions or comments!
