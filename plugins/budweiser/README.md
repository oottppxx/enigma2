# Budweiser.

Replace the current service audio with an alternative audio source.

Join us in the [Enigma2Talk Telegram chatroom](https://t.me/talkenigma2)
to help with testing, provide ideas and all kind of suggestions or comments!

This plugin is EXPERIMENTAL; it has been successfully tested on:
* Abcom Pulse 4k - OpenBH 5.1
* Amiko Viper 4k v40 - OpenBH 5.1
* Edision MIO 4k+ - OpenBH 5.1
* Gigablue UE 4k - TeamBlue 6.4
* Mut@nt HD51 - OpenATV 7.0, PurE2 6.5
* Octagon SF4008 - OpenLD 3.4
* Octagon SF8008 - OpenBH 5.1, OpenSPA 7.5
* uClan Ustym 4K - OpenATV 6.4
* VU+ Solo 4k - Egami 10.0, OpenATV 7.0|7.1, OpenBlackHole 5.0, OpenViX 6.0.
* VU+ Solo2 - OpenATV 6.x.
* VU+ Ultimo 4k - OpenBlackHole 5.1
* VU+ Uno - OpenPLi 8.1
* VU+ Uno|Duo 4k [SE] - OpenATV 6.4, OpenPLi 8.1, OpenSPA 7.5
* VU+ Zero - OpenATV 6.4, OpenBlackHole 4.4, OpenPLi 8.1
* Zgemma H7C - OpenATV 6.2|6.4
* Zgemma Star H2 - OpenPLi 8.1

On some decoders sometimes the alternative audio doesn't play for some
box/distro combos which were tested as successful by others. Investigation is
ongoing to check for interactions with other software/plugins that might be
installed on the problematic devices, but no smoking gun yet, so no known fix.

On some decoders, sometimes audio does not resume if the unmute option is
selected: to get service sound back, just zap to another service (or eventually
restart the current service, if you have the right plugin to do so installed).

On the MIPS receivers tested, the service audio can't be muted separately via
IOCTL, so an (ugly but smart) hack was "borrowed" from Ziko IPAUDIO plugin.
This requires stop/starting the entire service, so a video glitch is seen, it
can be disabled by setting "mute_tweak" to false in the sources.json file (see
below).

In some of the above, the example AAC stream does not, or might not, play.

Per [Ev0](https://www.linuxsat-support.com/thread/152127-budweiser-plugin/?postID=661724#post661724)'s
comment, you might want to tweak your current audio settings:
* make sure you have downmix selected.
* make sure 3D Surround is set to off.
* make sure Auto Volume Level (AVL) is also set to off.

VU+ BlackHole was also tested, but it doesn't seem to have any alternative and
usable audio devices/sinks other than the dvbaudiosink, which is of course busy
once services are in use? As such, unless a proper system audio device/sink is
found, this plugin won't work there.

## Description

Invoking the plugin should display a list of alternative audio sources (see
below), and the current buffering value. Selecting one of the sources (via the
OK key) should:
* perform an audio operation, per the source definition: either do nothing, mute
  the service audio, or unmute the service audio. Note that if the current
  service is using Exteplayer3 or another external player, audio ops will most
  likely fail to take any effect.
* perform an operation of a certain type. The type should also be defined in the
  file as a list of commands (technically, execv() arguments) to be executed, so
  the audio source plays via the system audio device. The commands are then run
  as enigma2 sub processes, and any instances of '%(URL)s', '%(BUFFERS)s', or
  '%(DEVICE)s' are replaced appropriately if required.
* if a different source than the last is selected, the buffer value will update
  to the value defined for the stream in the source definition, per the file.
* depending on the source definition, once an alternative source is selected,
  the sources list can auto-close or remain open; if the latter, the list can be
  closed via the EXIT key.

The current buffering value can be increased/decreased by using the CHANNEL
UP/DOWN keys (by 100), the PREV/NEXT keys (by 10), and the VOLUME UP/DOWN keys
(progressive) - the range is currently 0 to 2000, beware that a very small value
might cause the alternative audio stream not to play). Once the buffer value is
adjusted, you need to (re)select the source for it to take effect - beware that
the audio won't start playing until the buffer is full, which means that for a
high value it might take a while (experimentally, a value of a 1000 is about 30
seconds of delay, but as the setting is in buffers, it will heavily depend on
the stream type).

The list of alternative audio sources is a simple JSON text file, placed in the
/usr/lib/enigma2/Plugins/Extensions/Budweiser/sources.json path. Of course the
file can be edited and new sources added, and existing sources can be removed or
reordered. The operation types/commands can also be tweaked, if necessary.
There's no need to reload the plugin after each edit, the file is read on each
invocation. To troubleshoot any errors/parsing errors on the file, please turn
on debug and examine the output (see Settings).

The plugin always inserts a pre-defined audio source at or very near the top of
the list: CTRL^Z. Selecting this source will (try to) stop any previously
selected alternative audio source, resume/unmute the current service audio, and
close the list.

## Settings

All settings are controlled from the same file as the alternative audio sources.

To enable debugging, create the /tmp/budweiser-debug.log file for further
inspection of the plugin inner workings; don't forget to remove it when no
longer needed. There are a couple of example entries in the list, to enable
debugging, save the file with a timestamp, and disable.

## Notes

* The internet radio example sources were initially retrieved from the
http://fmstream.org/ site.

* The more astute readers might have noticed that the way it all works is
generic enough so the plugin can be used as a very simple way to create a
predefined list of commands to be run, not necessarily related to any audio
operations.

* Depending on the (frequency) of usage, it might be handier to assign a hotkey
to the plugin, so the list of sources can be brought up with a single key press
on the remote.

* This plugin idea came while reading a @Miguel_Patito discussion in a Telegram
chatroom; it was an interesting technical problem to try and figure out how to
solve. Of course, once I finished with version 6.2.1a, I found out about
[ziko](https://www.linuxsat-support.com/cms/user/344808-ziko/)'s
[IPAudio plugin](https://www.linuxsat-support.com/thread/148485-ipaudio-by-ziko/?postID=618093#post618093),
which apparently also uses a specific gstreamer utility in the background. I
guess my idea is ~1 year too late, but my implementation and approach is
slightly different and has its own merits and novelties, so I'll keep it around.

