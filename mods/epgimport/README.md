* EPGImporter mods

These are currently mods against EPGImporter 1.0+git190+4166ac7-r0(???)

They allow events to be added that would be generally skipped, due to
badly formatted(?) XML. This would cause some providers EPG to be very
sparsely populated, despite event information being available.

* Drop the xmltvconverter.py file into your plugins/EPGImport plugin
  directory (typically /usr/lib/enigma2/python/Plugins/Extensions/EPGImport)
* Restart the GUI/Enigma2/box.

On the next EPGImport, changes will take effect.

@oottppxx
