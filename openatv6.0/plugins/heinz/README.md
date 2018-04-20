NOTE: The easiest way to use this plugin is
by binding a key to it, to be able to invoke
it directly from a live stream and/or
"ketchup" stream.

When invoked during a live stream, settings
can be changed from the mini-EPG screen
using the

    Menu

key.

When invoked during a "ketchup" stream, the
following keys can be used to control it:

    Left, Right, Up, Down, OK, and Exit

These keys will, respectively:
- rewind the timeline;
- forward the timeline;
- display stream information;
- pause the stream;
- reload the stream at the current/selected
timeline time;
- do nothing and continue as is.

If the stream is reloaded without any change
to the timeline, the stream will go back by
the configured number of minutes (see
settings):  this is useful if a stream gets
stuck and just a reload is needed.

NOTE: the timeline current time is an
approximation, and frequent rewinding,
forwarding, pausing, or reloading the stream,
namely after it's stuck for long, will desync
the timeline current time with the real stream
time.

NOTE: from version 6.0.3j, a keymap.xml file
is used that also maps other keys to the
relevant actions during timeline display.
Check/edit this file in your plugins/Heinz
directory, namely if you require a custom
keymap (a reload of enigma2 will be required
after any change to the keymap).

Dev/Testing on OpenATV 6.0, Caveat Emptor.
