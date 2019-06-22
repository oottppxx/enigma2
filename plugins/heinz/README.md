NOTE: The easiest way to use this plugin is
by **binding a key to it**, to be able to
invoke it directly from a live stream and/or
"ketchup" stream.

When **invoked during a supported live stream**,

![EPG Screen Image](https://github.com/oottppxx/enigma2/blob/master/plugins/heinz/screenshots/hz-epg.jpg)

settings can be changed from the EPG screen
using the

 Menu

key.

If **invoked during an unsupported live stream**,
letting the timeout expire will take you to
the setup menu where you can adjust the
settings.

![Settings Screen Image](https://github.com/oottppxx/enigma2/blob/master/plugins/heinz/screenshots/hz-setup.jpg)

If **invoked during a "ketchup" stream** (from v6.2.1c, reinvoking is only needed if you exit the "ketchup" and then
resume it via zap history),

![Timeline Screen Image](https://github.com/oottppxx/enigma2/blob/master/plugins/heinz/screenshots/hz-slider.jpg)

the following keys can be used to control it:

 Left, Right, Up, Down, OK, Back, and Exit

 OR

 Rewind/PreviousSong, FastForward/NextSong,
 Info/EPG, Pause/Play+Pause, Play, and Stop.

as well as

1 2 3 4 5 6 7 8 9 0

These keys will, respectively:
- rewind the timeline;
- forward the timeline;
- display stream information;

![Info Screen Image](https://github.com/oottppxx/enigma2/blob/master/plugins/heinz/screenshots/hz-info.jpg)

- pause the stream (OK, Exit, Pause/Play+Pause/Play
to unpause);

![Pause Screen Image](https://github.com/oottppxx/enigma2/blob/master/plugins/heinz/screenshots/hz-pause.jpg)

- reload the stream at the current/selected
timeline time;
- stop the stream and return to the previous one;
- exit the timeline and continue as is;
- forward the timeline 1..10 minutes.

If **the stream is reloaded without any change to
the timeline**, the stream will go back by
the configured number of minutes (see settings):
this is useful if a stream gets stuck and just a
reload is needed.

Additional functionality for recording "ketchup"
streams (or their URL) can be accessed via the
colored/record keys.


Dev/Testing on OpenATV 6.2, OpenPLi 6.2.

Caveat Emptor.

