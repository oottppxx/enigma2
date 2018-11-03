* e2m3u2bouquet/Suls mods

Mods against Suls v0.7.7 (https://github.com/su1s/e2m3u2bouquet/releases/tag/v0.7.7)

Features/fixes:

* Enables catchup markings (!!!) on supported channels/providers
* Enables channel moves and/or copies across categories/bouquets,
including to newly created categories/bouquets, via the override file
* Fixes VOD matching issues for particular provider(s)
* Fixes picon files' name generation

NOTE: if you want to mark channels with something other than 3
exclamation marks, just modify the line of the script after the
copyright string at the top, that says BANG=' !!!' (edit the
content within the single quotes, don't touch the rest).

How to use/install:

* Pick the version appropriate mod Python file (NOTE: you need
to download from github as RAW!)
* Rename it to e2m3u2bouquet.py
* Drop it on your plugins/E2m3u2bouquet Suls plugin directory
(typically /usr/lib/enigma2/python/Plugins/Extensions/E2m3u2bouquet)
* Restart the GUI/Enigma2/box.

On the next bouquet update, changes will take effect.

@oottppxx
