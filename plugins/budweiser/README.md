# Budweiser.

This plugin is currently EXPERIMENTAL, and has been successfully tested on:
* Mut@nt HD51 - PurE2 6.5
* Octagon SF8008 - OpenSpa 7.5
* VU Zero - OpenBlackHole 4.4
* zGgemma H7C - OpenATV 6.2, OpenATV 6.4

Replace the current service audio with a pre-defined alternative audio source.

Join us in the [Enigma2Talk Telegram chatroom](https://t.me/talkenigma2)
to help with testing, provide ideas and all kind of suggestions or comments!

## Description

Invoking the plugin should display the list of the pre-defined alternative
audio sources, selecting one of those should:
* mute the current service audio (not possible if the current service is using
  Exteplayer3).
* play the selected audio source (via the system audio device).

Alternative audio sources are currently (this might change at any time in the
future) pre-defined in the sources.json file (no need to reload the plugin on
edits to this file).

Currently (this might change at any time in the future) the sources.json file
contains a hash in which:
* the keys are the source name that will show up in the selection list.
* the values are commands to be run when selecting the corresponding key from
  the list.

The commands specified are run as enigma2 sub processes. Currently (this might
change at any time in the future) all underscores in the command are replaced by
spaces before invocation - as such, if an underscore shows up in a URL, it
should itself be replaced by %5f or other adequate encoding.

There are 2 special pre-defined audio sources that are always added by the
plugin to the top of the list:
* CTRL^Z - selecting this source will (try to) stop any previously selected
  alternative audio source and resume the current service audio.
* E2MUTE - selecting this source will only (try to) mute the current service
  audio.

## Settings

None - the debug setting is currently hardcoded to True in some of the IPK
versions.

**"Debug"**
* "Activate debug log."
* Default: False
* If set to True, debug information is recorded under the
  /tmp/budweiser-debug.log file.
