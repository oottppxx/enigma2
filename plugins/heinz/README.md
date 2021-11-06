# Heinz.

Catchup plugin supporting XC API and VAPI.

NOTE: The easiest way to use this plugin is by **binding a key to it**, to be
able to invoke it directly from a live stream and/or "ketchup" stream.

When **invoked during a supported live stream**, settings can be changed from
the EPG screen using the **Menu** key.

If **invoked during an unsupported live stream**, letting the timeout expire
will bring up the setup menu where settings can be adjusted.

If **invoked during a "ketchup" stream** (from v6.2.1c, reinvoking is only
needed if a "ketchup" stream is resumed from the zap history), the following
keys can be used to control it:

* **Left/Rewind/PreviousSong** - rewind the timeline;
* **Right/FastForward/NextSong** - forward the timeline;
* **Up/Info/EPG** - display stream information;
* **Down/Pause/Play+Pause** - pause the stream (OK, Exit,
    Pause/Play+Pause/Play to unpause);
* **OK/Play** - reload the stream at the current/selected timeline time;
* **Back/Stop** - stop the stream and return to the previous one;
* **Exit** - exit the timeline and continue as is;
* **1/2/3/4/5/6/7/8/9/0** - forward the timeline 1..10 minutes.

If **the stream is reloaded without any change to the timeline**, the stream will
go back by the configured number of minutes (see settings): this is useful if a
stream gets stuck and just a reload is needed.

Additional functionality for recording "ketchup" streams (or their URL) can be
accessed via the colored/record keys, when in the program selection screen:

* **Red/Record** - add (or remove if previously added) the selected program to
    the recording queue; recording will start after a brief delay (see settings)
    .
* **Yellow** - log the selected catchup program URL to the /tmp/heinz-url.log
    file.
* **Blue** - display the current queue of programs set to be recorded.

Dev/Testing on OpenATV 6.2, OpenPLi 6.2.

Caveat Emptor.

## Description

As mentioned above, this plugin allows access to a stream catchup archive, if
available. Navigation to the available past programs is done via the
short/single EPG screen.

## Settings

**"Extra duration (minutes)"**
* "Extra minutes to add to program duration, accounting for late endings."
* Default: 60 minutes.
* How many minutes to continue playing after the scheduled end of the event.
* Useful if the original broadcaster started the program later than scheduled.

**"Early start (minutes)"**
* "Extra minutes able to rewind past the start of the program, accounting for early starts."
* Default: 10 minutes.
* Useful if the original broadcaster started the program earlier than scheduled.

**"Reload offset (minutes)"**
* "Immediate reload offset, accounting for stuck streams, in minutes."
* Default: 2 minutes.
* How muchh to rewind if invoking the timeline and just reloading the stream,
  useful if the viewer lost the plot for a bit and wants quickly go back and
  rewatch a scene.

**"Support cache interval (minutes)"**
* "Time interval for caching stream ketchup support information, in minutes (0 to disable)."
* Default: 1440 minutes, 24 hours, 1 day.
* Translates to how often to query for the information regarding which streams
  support catchup, to avoid overloading the providers with requests. The default
  means 1 query each day interval, with each interval resetting at midnight.

**"EPG cache interval (minutes)"**
* "Time interval for caching the latest stream ketchup EPG, in minutes (0 to disable)."
* Default: 15 minutes.
* Translates to how often to query for the information regarding catchup events,
  to avoid overloading  the providers with requests. The default means 1 query
  in each 15 minutes interval, with each interval starting at the hour, quarter
  of an hour, half an hour, or 45 minutes past the hour.

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
  request. Only relevant for VAPI and new XCAPI, not used with the old XCAPI.

**"Lookback (days)"**
* "Number of days to lookback for programs."
* Default: 3 days.
* This is used as a forced setting for VAPI, for reasons... Also used for XC API
  if the "force lookup" setting is true and providers don't correctly set the
  number of days in the archive.

**"Use new XCAPI"**
* "Use the new(?) XCAPI."
* Default: False.
* Apparently there are really 2 different XC APIs, with slightly different
  stream URLs used, and that use durations in minutes vs seconds. If the
  provider streams show up as unsupported, the setting can be changed to True
  for testing if the provider supports this new XC API format. Unfortunately
  there are no accomodations for simultaneous different providers, each using
  a different XC API format.

**"Generate current"**
* "Generate entry for currently playing event."
* Default: True.
* Some providers make the current program available quasi-immediately on their
  catchup archive, so it can be played from the start while the program is still
  live. Useful if timeshift isn't available.

**"Stop at current"**
* "Stop adding events when the current playing one is found."
* Default: True.
* Some providers don't sort their catchup programming, so if entries seem to be
  missing from the catchup, testing with the setting set to False is advised.

**"Numeric skips OK"**
* "Skip OK when forwarding timeline 1-10 minutes using numeric keys (0 key equals 10 minutes)."
* Default: True.
* If pressing the numeric keys while in the timeline, the stream will
  immediately be fast forwarded the corresponding number of minutes, without the
  need of pressing the "OK" key; if the setting is set to False, pressing the
  numeric keys will only advance the timeline, and requires "OK" to apply, also
  allowing "Exit" to cancel.

**"Timeline smoothness"**
* "Adjusts timeline rewind/forward speed vs smoothness (10 to 20 is the recommended range)."
* Default: 17.
* This number influences how smooth the timeline can be navigated on each
  direction, each time a forwarding/rewinding action is taken; a higher number
  will slow down the progress, but make it more precise. A lower number will
  make fast progress but probably make it difficult to land on a precise time.

**"Inactivity timer (seconds)"**
* "Timeline inactivity timer, in seconds (0 to disable)."
* Default: 5 seconds.
* How long it takes for the timeline to dismiss itself if no action is taken on
  it.

** "Force lookup"**
* "Try and work around a broken catchup API."
* Default: False.
* Some providers don't populate their catchup archive correctly; if no programs
  are showing for a certain service, this setting can be tweaked to True for
  testing if that's the case.

**"List offset (minutes)"**
* "Try and work around bad XC listing times."
* Default: 0 minutes.
* Used to adjust the program times as displayed in the list; generally used to
  fix timezone issues, but can also be used to fix providers which incorrectly
  populate their catchup archives. If the times are off in the list but the
  streams always land on the start of the corresponding program, this is most
  likely the setting to tweak to make things right.

**"Play offset (minutes)"**
* "Try and work around bad XC play times."
* Default: 0 minutes.
* Used to workaround bad program times as (incorrectly) recorded by a provider.
  If when selecting an event from the EPG list a different one plays, or the
  stream starts in the middle of the selected program, this is most likely the
  setting to tweak to make things right.

**"Rec. extra duration (minutes)"**
* "Extra minutes to record past the stated program end, accounting for late endings."
* Default: 5 minutes.
* How long to request past the program when recording, to account for programs
  that end/run later than scheduled.

**"Rec. early start (minutes)"**
* "Extra minutes to record before the stated program start, accounting for early starts."
* Default: 5 minutes.
* How long to request before the start of the program when recording, to account
  for programs that start earlier than scheduled.

**"Rec. delay (seconds)"**
* "Minimum delay, in seconds, before recording starts (no smaller than 1), allowing for single connection providers and zap time."
* Default: 60 seconds, 1 minute.
* Allows some time before starting a recording, so the user can zap out of the
  current stream/provider - useful for providers that only allow 1 connection,
  and account the catchup usage as 1 connection as well.

**"Rec. command"**
* "Recording command to use (URL, DURATION, and FILE will be replaced, leave empty for default)."
* Default:
`"/usr/bin/ffmpeg -y -i \'URL\' -t DURATION -vcodec copy -acodec copy -f mp4 /media/hdd/movie/downloading.mp4 </dev/null >/dev/null 2>&1 && mv /media/hdd/movie/downloading.mp4 /media/hdd/movie/\'FILE\' >/dev/null 2>&1' && wget -O- -q \'http://localhost/web/message?text=FILE%0aDownload+Completed!&type=2&timeout=5\'"`
 * This command is spawned in the background for each recording. The default
  command invokes ffmpeg to download the program to the /media/hdd/movie/downloading.mp4
  file; if the download is successful, the file is then renamed according to the
  program title, and if the latter is also successful, a notification is
  triggered via OpenWebif web API. Feel free to replace the command as you wish,
  do let me know of any improvements that can be done to the default.

**"Debug"**
* "Activate debug log."
* Default: False.
* If set to True, debug information is recorded under the
  /tmp/heinz-debug.log file.
