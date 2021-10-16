# Absolut VODka.

VOD plugin supporting XC API and VAPI.

Dev/Testing on OpenATV 6.2, OpenPLi 6.2.

Caveat Emptor.

Join us in the [Enigma2Talk Telegram chatroom](https://t.me/talkenigma2)
to help with testing, provide ideas and all kind of suggestions or comments!

## Description

This plugin allows access to your provider's VOD content, if they implement
either the XC (Xtream Codes) or the Vaders API.

It should be invoked when watching a live stream (binding to a hot key is
recommended), the VOD content will then be navigated to via the short EPG
screens.

## Settings

**"Ignore added time"**
* "Ignore added date/time and use alphabetical or season/episode order."
* Default: True.
* Useful if your provider added times don't relate to any episode order.

**"Ignore beginnings"**
* "Ignore beginning 'The', 'An, 'A', etc..."
* Default: "the,an,a".
* Unless you like to have all titles starting with "The" under the T section,
  leave it alone. Modify accordingly for the usual language used in the titles
  of your shows/movies if you like the feature.

**"Cache interval (minutes)"**
* "Time interval for caching movies/series, in minutes (0 to disable)."
* Default: 1440 minutes / 24 hours.
* Your provider probably doesn't update VOD every day, so we're polite here and
  don't query more often than this interval (unless you explicitly clear the
  cache or reload the box, of course).

**"Service type"**
* "Enigma2 service player to use."
* Default: 4097/IPTV.
* This is used creating the service references for the Enigma2 player
  assignments. If you installed service app, you might have other preferences,
  e.g., 5001/GSTREAMER, 5002/EXTEPLAYER3, etc...

**"Stream type"**
* "Stream type/proto to request."
* Default: m3u8.
* When requesting VOD stream URLs from your provider, what type of stream to
  request. Only relevant for VAPI, not used on XCAPI providers.

**"Clear cache"**
* "Explicitly clear movies/series cache."
* Default: False
* If you set it to True, the VOD cache will be cleared when exiting the settings
  and the setting itself will become False again. This means the next time the
  plugin is invoked, it will refresh the VOD program information by fetching it
  from the provider. Only really useful if you happen to know your provider
  updated the VOD programming before the cache interval elapsed (see "Cache 
  Interval" setting).

**"Rec. delay (seconds)"**
* "Minimum delay, in seconds, before recording starts (no smaller than 1),i
  allowing for single connection providers and zap time."
* Default: 60 seconds / 1 minute.
* Once you add a program to the recording queue, you have this much time to zap
  to another provider live stream, or non-IPTV providers. Useful if your IPTV
  provider only allows 1 simultaneous connection of either live TV or VOD.

**"Rec. command"**
* "Recording command to use (URL and FILE will be replaced, leave empty for default)."
"Debug" "Activate debug log."
* Default:
`"/usr/bin/ffmpeg -y -i \'URL\' -vcodec copy -acodec copy -f mp4 /media/hdd/movie/downloading.mp4 </dev/null >/dev/null 2>&1 && mv /media/hdd/movie/downloading.mp4 /media/hdd/movie/\'FILE\' >/dev/null 2>&1' && wget -O- -q \'http://localhost/web/message?text=FILE%0aDownload+Completed!&type=2&timeout=5\'"`
 * This command is spawned in the background for each recording. The default
  command invokes ffmpeg to download the program to the /media/hdd/movie/downloading.mp4
  file; if the download is successful, the file is then renamed according to the
  program title, and if the latter is also successful, a notification is
  triggered via OpenWebif web API. Feel free to replace the command as you wish,
  do let me know of any improvements that can be done to the default.

**"Debug"**
* "Activate debug log."
* Default: False
* If set to True, debug information is recorded under /tmp/absolut-debug.log file.

