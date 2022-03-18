# Budweiser.

Replace the current service audio with an alternative audio source.

Join us in the [Enigma2Talk Telegram chatroom](https://t.me/talkenigma2)
to help with testing, provide ideas and all kind of suggestions or comments!

This plugin is EXPERIMENTAL; it has been successfully tested on:
* Mut@nt HD51 - PurE2 6.5, OpenATV 7.0
* Octagon SF8008 - OpenSpa 7.5
* uClan Ustym 4K - Openatv 6.4
* VU Solo 4k - OpenATV 7.0/7.1, Egami10, OpenBlackHole 5.0, OpenViX 6.0.
* VU Uno|Duo 4k SE - OpenATV 6.4, OpenSpa x.y
* VU Zero - OpenBlackHole 4.4, OpenATV 6.4, OpenPLi 8.1
* Zgemma H7C - OpenATV 6.2, OpenATV 6.4

In some of the above, the example Once radio AAC stream does not, or might not,
play.

## Description

Invoking the plugin should display a list of alternative audio sources, and the
current buffering value. Selecting one of the sources (via the OK key) should:
* perform an audio operation, per the source definition: either do nothing, mute
  the service audio, or unmute the service audio. Note that if the current
  service is using Exteplayer3 or another external player, audio ops will most
  likely fail to take any effect.
* perform an operation of a certain type. The type should also be defined in the
  file as a list of commands (technically, execv() arguments) to be executed, so
  the audio source plays via the system audio device. The commands are then run
  as enigma2 sub processes, and any instances of '%(URL)s', '%(BUFFERS)s', or
  '%(DEVICE)s' are replaced appropriately if required.
* depending on the source definition, once an alternative source is selected,
  the sources list can auto-close or remain open; if the latter, the list can be
  closed via the EXIT key.

The current buffering value can be increased/decreased by using the CHANNEL
UP/DOWN keys and the PREV/NEXT keys, respectively (the range is currently 0 to
2000 - beware that a very small value might cause the alternative audio stream
not to play).

The list of alternative audio sources is a simple JSON text file, placed in the
/usr/lib/enigma2/Plugins/Extensions/Budweiser/sources.json path. Of course the
file can be edited and new sources added, and existing sources can be removed or
reordered. The opreation types/commands can also be tweaked, if necessary.
There's no need to reload the plugin after each edit, the file is read on each
invocation. To troubleshoot any errors/parsing errors on the file, please turn
on debug and examine the output (see Settings).

The plugin always inserts a pre-defined audio source at the top of the list:
CTRL^Z. Selecting this source will (try to) stop any previously selected
alternative audio source, resume/unmute the current service audio, and close the
list.

## Settings

None; to enable debugging, create the /tmp/budweiser-debug.log file for further
inspection of the plugin inner workings; don't forget to remove it when no
longer needed.

## Notes

* The example sources were retrieved from the http://fmstream.org/ site.

* The more astute readers might have noticed that the way it all works is
generic enough so the plugin can be used as a very simple way to create a
predefined list of commands to be run, not necessarily related to any audio
operations.

* Depending on the (frequency) of usage, it might be handier to assign a hotkey
to the plugin, so the list of sources can be brought up with a single key press
on the remote.

* This plugin idea came while reading a @Miguel_Patito discussion in the
"Sat en espanol enigma2 vu+" Telegram chatroom; it was an interesting technical
problem to try and figure out how to solve. Of course, once I finished with
version 6.2.1a, I found out about
[ziko](https://www.linuxsat-support.com/cms/user/344808-ziko/)'s
[IPAudio plugin](https://www.linuxsat-support.com/thread/148485-ipaudio-by-ziko/?postID=618093#post618093),
which apparently also uses a specific gstreamer utility in the background. I
guess my idea is ~1 year too late, but my implementation and approach is
slightly different and has its own merits and novelties, so I'll keep it around.

