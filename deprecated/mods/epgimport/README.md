* EPGImporter mods

NOTE: EPGImporter seems to have sync'ed against
https://github.com/oe-alliance/XMLTV-Import/commit/fa46934783aa4d4fb10be3ac744ae87935890977
and this mod isn't needed anymore (at least in OpenATV 6.2).

These are currently mods against EPGImporter 1.0+git190+4166ac7-r0(???)

I had reported the issue some time ago, at 
https://github.com/oe-alliance/XMLTV-Import/issues/34

Features:

* Enables adding events with empty description and/or subtitle

Events with an empty description and/or subtitle would generally be skipped
by the current XML parser.  This would cause some providers EPG to be very
sparsely populated, despite the most important event information being available.

How to use/install:

* Drop the xmltvconverter.py file into your plugins/EPGImport plugin
  directory (typically /usr/lib/enigma2/python/Plugins/Extensions/EPGImport)
* Restart the GUI/Enigma2/box.

On the next EPGImport, changes will take effect.

@oottppxx
